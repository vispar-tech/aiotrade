import hashlib
import hmac
import logging
import time
from typing import Any
from urllib import parse

from aiotrade._errors import ExchangeResponseError
from aiotrade._http import HttpClient
from aiotrade._types import HttpMethod

logger = logging.getLogger("aiotrade.bingx")


def _mask_headers(headers: dict[str, Any]) -> dict[str, Any]:
    masked: dict[str, Any] = {}
    for k, v in headers.items():
        if k == "X-BX-APIKEY":
            masked[k] = v[:6] + "..." if isinstance(v, str) else "****"
        else:
            masked[k] = v
    return masked


def _mask_signature(url: str) -> str:
    """Mask the signature value in a BingX API URL's query string, fast."""
    sig = "signature="
    i = url.find(sig)
    if i == -1:
        return url
    amp = url.find("&", i)
    if amp == -1:
        # signature is last or only param
        return url[: i + len(sig)] + "***"
    return url[: i + len(sig)] + "***" + url[amp:]


class BingxHttpClient(HttpClient):
    """Bingx HTTP client."""

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        demo: bool = False,
        recv_window: int = 5000,
    ) -> None:
        """Initialize HTTP client.

        Args:
            api_key: Trading API key
            api_secret: Trading API secret
            demo: Use vst instead of mainnet
            recv_window: Receive window in milliseconds
        """
        if demo:
            base_url = "https://open-api-vst.bingx.com"
        else:
            base_url = "https://open-api.bingx.com"
        super().__init__(base_url, api_key, api_secret, recv_window)

    def _generate_signature(self, api_secret: str, payload: str) -> str:
        """Bingx V5 signature (API v5)."""
        return hmac.new(
            bytes(api_secret, "utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _prepare_payload(
        self, method: HttpMethod, params: dict[str, Any], timestamp: int
    ) -> tuple[str, str | None]:
        """
        Prepare BingX payload and URL-encoded payload, as per exchange rules.

        Returns a tuple: (payload_for_signature, url_encoded_payload_for_query)
        """
        # Always work with a sorted list of (k, v) tuples
        if method == "GET":
            sorted_items = sorted(params.items())
            params_str = "&".join(f"{k}={v}" for k, v in sorted_items)
            params_str = (
                f"{params_str}&timestamp={timestamp}"
                if params_str
                else f"timestamp={timestamp}"
            )

            # Any structured value triggers full encoding
            contains_struct = any(
                isinstance(v, (dict, list))
                or (isinstance(v, str) and ("{" in v or "[" in v))
                for _, v in sorted_items
            )
            if contains_struct:
                url_params_str = "&".join(
                    f"{k}={parse.quote(str(v), safe='')}" for k, v in sorted_items
                )
            else:
                url_params_str = "&".join(f"{k}={v}" for k, v in sorted_items)
            url_params_str = (
                f"{url_params_str}&timestamp={timestamp}"
                if url_params_str
                else f"timestamp={timestamp}"
            )
            return params_str, url_params_str

        # For non-GET: mutate params and build simple k=v string for signature
        params["timestamp"] = timestamp
        sorted_items = sorted(params.items())
        params_str = "&".join(f"{k}={v!s}" for k, v in sorted_items)
        return params_str, None

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

        if auth:
            if not self.api_key:
                raise ValueError("API key must be set for authenticated requests.")
            if not self.api_secret:
                raise ValueError("API secret must be set for authenticated requests.")
            req_headers["X-BX-APIKEY"] = self.api_key

        # Set recv window from cls
        params["recvWindow"] = self.recv_window
        req_payload, req_url_params = self._prepare_payload(method, params, timestamp)

        if auth:
            if not (self.api_key and self.api_secret):
                raise ValueError(
                    "API key and API secret must be set for authenticated requests."
                )
            signature = self._generate_signature(self.api_secret, req_payload)
        else:
            signature = None

        base_req_url = f"{self.base_url}{endpoint}"

        if method == "GET":
            req_url = f"{base_req_url}?{req_url_params}"
            if signature:
                req_url += f"&signature={signature}"
            req_json = None
        else:
            req_json = params
            req_json["timestamp"] = timestamp
            req_json["signature"] = signature
            req_url = base_req_url

        # Logging fast, avoid joining or formatting unnecessarily unless debug
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "Making async %s request to %s with params: %s",
                method,
                base_req_url,
                params,
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
                if res_json.get("code") != 0:
                    raise ExchangeResponseError("bingx", res_json)
            except Exception as err:
                if logger.isEnabledFor(logging.ERROR):
                    logger.error(
                        "HTTP error during async request: "
                        "method=%s url=%s headers=%s status=%s err=%r",
                        method,
                        _mask_signature(req_url),
                        _mask_headers(req_headers),
                        resp.status,
                        err,
                    )
                raise
        return res_json
