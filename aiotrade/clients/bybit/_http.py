import hashlib
import hmac
import logging
import time
from typing import Any

import orjson

from aiotrade._errors import ExchangeResponseError
from aiotrade._http import HttpClient
from aiotrade._types import HttpMethod

DOMAIN_MAIN = "bybit"
TLD_MAIN = "com"


logger = logging.getLogger("aiotrade.bybit")


def _mask_headers(headers: dict[str, Any]) -> dict[str, Any]:
    masked: dict[str, Any] = {}
    for k, v in headers.items():
        if k in ("X-BAPI-API-KEY", "X-BAPI-SIGN"):
            masked[k] = v[:6] + "..." if isinstance(v, str) else "****"
        else:
            masked[k] = v
    return masked


class BybitHttpClient(HttpClient):
    """Bybit HTTP client."""

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        testnet: bool = False,
        demo: bool = False,
        recv_window: int = 5000,
        referral_id: str | None = None,
    ) -> None:
        """Initialize HTTP client.

        Args:
            api_key: Trading API key
            api_secret: Trading API secret
            testnet: Use testnet instead of mainnet
            demo: Use demo trading
            recv_window: Receive window in milliseconds
            referral_id: Referral ID
        """
        # Subdomain selection based on testnet and demo flags
        if demo and testnet:
            sub = "api-demo-testnet"
        elif demo:
            sub = "api-demo"
        elif testnet:
            sub = "api-testnet"
        else:
            sub = "api"
        base_url = f"https://{sub}.{DOMAIN_MAIN}.{TLD_MAIN}"
        self.referral_id = referral_id

        super().__init__(base_url, api_key, api_secret, recv_window)

    def _generate_signature(
        self, api_key: str, api_secret: str, payload: str, timestamp: int
    ) -> str:
        """Bybit V5 signature (API v5).

        Signature is generated as:
        HMAC_SHA256(apiSecret, timestamp + apiKey + recvWindow + payload)
        - For GET: payload is the sorted query string.
        - For POST: payload is the plain JSON string.
        """
        param_str = str(timestamp) + api_key + str(self.recv_window) + payload
        return hmac.new(
            bytes(api_secret, "utf-8"),
            param_str.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _prepare_payload(self, method: HttpMethod, params: dict[str, Any]) -> str:
        def cast_values() -> None:
            string_params = [
                "qty",
                "price",
                "triggerPrice",
                "takeProfit",
                "stopLoss",
            ]
            integer_params = ["positionIdx"]
            for key, value in params.items():
                if key in string_params:
                    if not isinstance(value, str):
                        params[key] = str(value)
                elif key in integer_params and not isinstance(value, int):
                    params[key] = int(value)

        if method == "GET":
            return "&".join(
                f"{k}={v}" for k, v in sorted(params.items()) if v is not None
            )
        cast_values()
        sanitized = {k: params[k] for k in sorted(params) if params[k] is not None}
        if not sanitized:
            return "{}"

        # Note: need Bybit logic for signature
        # serialization must match server expectations
        return orjson.dumps(sanitized).decode().replace(":", ": ").replace(",", ", ")

    async def _build_request_args(
        self,
        method: HttpMethod,
        endpoint: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        auth: bool = False,
    ) -> tuple[
        dict[str, Any],
        str,
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, Any] | None,
    ]:
        # Fast path: avoid unnecessary checks and recomputation
        if self._session.closed:
            session_type = "shared" if self._shared_session else "individual"
            raise RuntimeError(
                f"Session is closed ({session_type}). Create a new HttpClient instance."
            )

        # Prefer local assignment for micro-speed-up
        params = params if params is not None else {}
        req_headers = headers if headers is not None else {}

        # Optimize timestamp retrieval
        timestamp = int(time.time() * 10**3)

        # Cheap check for referral
        if self.referral_id is not None:
            req_headers["Referer"] = self.referral_id

        # Fast payload prep
        req_payload = self._prepare_payload(method, params)

        # Quickly handle signature/auth
        if auth:
            if not (self.api_key and self.api_secret):
                raise ValueError(
                    "API key and API secret must be set for authenticated requests."
                )
            signature = self._generate_signature(
                self.api_key, self.api_secret, req_payload, timestamp
            )
            req_headers["X-BAPI-API-KEY"] = self.api_key
            req_headers["X-BAPI-SIGN"] = signature
            req_headers["X-BAPI-SIGN-TYPE"] = "2"
            req_headers["X-BAPI-TIMESTAMP"] = str(timestamp)
            req_headers["X-BAPI-RECV-WINDOW"] = str(self.recv_window)

        else:
            signature = None

        req_url = f"{self.base_url}{endpoint}"

        if method == "GET":
            req_url = f"{req_url}?{req_payload}" if req_payload else req_url
            req_json = None
        else:
            req_json = {k: params[k] for k in sorted(params) if params[k] is not None}

        # Logging fast, avoid joining or formatting unnecessarily unless debug
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "Making async %s request to %s with params: %s", method, req_url, params
            )

        return (req_headers, req_url, None, req_json, None)

    async def _async_request(
        self,
        method: HttpMethod,
        endpoint: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        auth: bool = False,
    ) -> dict[str, Any]:
        (
            req_headers,
            req_url,
            req_params,
            req_json,
            req_data,
        ) = await self._build_request_args(method, endpoint, params, headers, auth)

        async with self._session.request(
            method,
            req_url,
            params=req_params,
            json=req_json,
            data=req_data,
            headers=req_headers,
        ) as resp:
            try:
                resp.raise_for_status()
                res_json: dict[str, Any] = await resp.json(content_type=None)
                if res_json.get("retCode") != 0:
                    raise ExchangeResponseError("bybit", res_json)
            except ExchangeResponseError as err:
                if logger.isEnabledFor(logging.ERROR):
                    logger.error(
                        "ExchangeResponseError during async request: "
                        "method=%s url=%s headers=%s status=%s error=%s",
                        method,
                        req_url,
                        _mask_headers(req_headers),
                        resp.status,
                        err,
                    )
                raise
            except Exception as err:
                if logger.isEnabledFor(logging.ERROR):
                    logger.error(
                        "HTTP error during async request: "
                        "method=%s url=%s headers=%s status=%s err=%r",
                        method,
                        req_url,
                        _mask_headers(req_headers),
                        resp.status,
                        err,
                    )
                raise
        return res_json
