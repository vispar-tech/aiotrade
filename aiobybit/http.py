"""HTTP client module for Bybit API communication."""

import hashlib
import hmac
import logging
import time
from types import TracebackType
from typing import Any, Literal, Self

import aiohttp
import orjson

from .session import BybitSessionManager

HttpMethod = Literal["GET", "POST", "PUT", "DELETE"]

logger = logging.getLogger(__name__)


DOMAIN_MAIN = "bybit"
TLD_MAIN = "com"


def _mask_headers(headers: dict[str, Any]) -> dict[str, Any]:
    masked: dict[str, Any] = {}
    for k, v in headers.items():
        if k in ("X-BAPI-API-KEY", "X-BAPI-SIGN"):
            masked[k] = v[:6] + "..." if isinstance(v, str) else "****"
        else:
            masked[k] = v
    return masked


class BybitHttpClient:
    """Asynchronous HTTP client for Bybit API (main, testnet, demo; NO bytick)."""

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        testnet: bool = False,
        demo: bool = False,
        recv_window: int = 5000,
        referral_id: str | None = None,
    ) -> None:
        """Initialize Bybit HTTP client.

        Args:
            api_key: Bybit API key
            api_secret: Bybit API secret
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
        self.base_url = f"https://{sub}.{DOMAIN_MAIN}.{TLD_MAIN}"
        self.api_key = api_key
        self.api_secret = api_secret
        self.recv_window = recv_window
        self.referral_id = referral_id

        # Check if shared session is initialized
        if BybitSessionManager.is_initialized():
            # Use shared session
            self._session = BybitSessionManager.get_session()
            self._shared_session = True
        else:
            # Create individual session for this client
            connector = aiohttp.TCPConnector(limit=50)
            self._session = aiohttp.ClientSession(
                connector=connector,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )
            self._shared_session = False

    async def close(self) -> None:
        """
        Close the underlying HTTP session if it is not shared and not already closed.

        For shared sessions, this method does nothing.
        """
        await self._close_session()

    async def __aenter__(self) -> Self:
        """Enter the async context manager."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Exit the async context manager. Close session if not shared."""
        if not self._shared_session:
            await self._close_session()

    async def _close_session(self) -> None:
        """Close the aiohttp session if necessary."""
        if self._session and not self._session.closed:
            await self._session.close()

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
        return orjson.dumps(sanitized, option=orjson.OPT_SORT_KEYS).decode("utf-8")

    async def _build_request_args(
        self,
        method: HttpMethod,
        endpoint: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        auth: bool = False,
    ) -> tuple[
        HttpMethod,
        str,
        dict[str, Any] | None,
        dict[str, Any] | None,
        dict[str, str],
        int,
        str | None,
        dict[str, Any],
    ]:
        # Fast path: avoid unnecessary checks and recomputation
        if self._session.closed:
            session_type = "shared" if self._shared_session else "individual"
            raise RuntimeError(
                f"Session is closed ({session_type}). "
                "Create a new BybitHttpClient instance."
            )

        # Prefer local assignment for micro-speed-up
        params = params if params is not None else {}
        headers = headers if headers is not None else {}

        # Optimize timestamp retrieval
        timestamp = int(time.time() * 10**3)

        # Cheap check for referral
        if self.referral_id is not None:
            headers["Referer"] = self.referral_id

        # Fast payload prep
        req_payload = self._prepare_payload(method, params)

        # Quickly handle signature/auth
        if auth:
            if not (self.api_key and self.api_secret):
                raise ValueError(
                    "API key and secret must be set for authenticated requests."
                )
            signature = self._generate_signature(
                self.api_key, self.api_secret, req_payload, timestamp
            )
            headers.update(
                {
                    "X-BAPI-API-KEY": self.api_key,
                    "X-BAPI-SIGN": signature,
                    "X-BAPI-SIGN-TYPE": "2",
                    "X-BAPI-TIMESTAMP": str(timestamp),
                    "X-BAPI-RECV-WINDOW": str(self.recv_window),
                }
            )
        else:
            signature = None

        url = f"{self.base_url}{endpoint}"

        if method == "GET":
            url = f"{url}?{req_payload}" if req_payload else url
            req_params = None
            req_json = None
            payload = req_payload
        else:
            req_params = None
            req_json = (
                {k: v for k, v in params.items() if v is not None} if params else None
            )
            payload = req_payload

        # Logging fast, avoid joining or formatting unnecessarily unless debug
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "Making async %s request to %s with params: %s", method, url, params
            )

        return (
            method,
            url,
            req_params,
            req_json,
            headers,
            timestamp,
            payload,
            params,
        )

    async def _async_request(
        self,
        method: HttpMethod,
        endpoint: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        auth: bool = False,
    ) -> dict[str, Any]:
        (
            method_val,
            url,
            req_params,
            req_json,
            headers_val,
            timestamp,
            payload,
            params_orig,
        ) = await self._build_request_args(method, endpoint, params, headers, auth)

        async with self._session.request(
            method_val,
            url,
            params=req_params,
            json=req_json,
            headers=headers_val,
        ) as resp:
            try:
                resp.raise_for_status()
                res_json: dict[str, Any] = await resp.json(content_type=None)
            except Exception:
                logger.error(
                    f"Request error: method={method_val}, url={url}, "
                    f"params={params_orig}, headers={_mask_headers(headers_val)}",
                )
                raise
            if res_json.get("retCode") == 10004:
                if self.api_key is None:
                    pass
                logger.error(
                    f"Bybit signature error (retCode 10004): {res_json.get('retMsg')}\n"
                    f"Origin string is: "
                    f"'"
                    f"{timestamp or ''}"
                    f"{self.api_key or ''}"
                    f"{self.recv_window!s}"
                    f"{payload or ''}"
                    f"'. "
                    f"Params: {params_orig}",
                )
                raise Exception(res_json.get("retMsg", "Unknown error"))
            return res_json

    @property
    def uses_shared_session(self) -> bool:
        """Check if this client uses a shared session."""
        return self._shared_session

    async def get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        auth: bool = False,
    ) -> dict[str, Any]:
        """Async GET request."""
        return await self._async_request(
            method="GET",
            endpoint=endpoint,
            params=params,
            headers=headers,
            auth=auth,
        )

    async def post(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        auth: bool = False,
    ) -> dict[str, Any]:
        """Async POST request."""
        return await self._async_request(
            method="POST",
            endpoint=endpoint,
            params=params,
            headers=headers,
            auth=auth,
        )

    async def put(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        auth: bool = False,
    ) -> dict[str, Any]:
        """Async PUT request."""
        return await self._async_request(
            method="PUT",
            endpoint=endpoint,
            params=params,
            headers=headers,
            auth=auth,
        )

    async def delete(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        auth: bool = False,
    ) -> dict[str, Any]:
        """Async DELETE request."""
        return await self._async_request(
            method="DELETE",
            endpoint=endpoint,
            params=params,
            headers=headers,
            auth=auth,
        )
