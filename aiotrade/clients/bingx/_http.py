import hashlib
import hmac
import logging
import time
from collections.abc import Mapping
from typing import Any
from urllib import parse

from aiotrade._errors import ExchangeResponseError
from aiotrade._http import HttpClient
from aiotrade._protocols import ParamsType
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
        self.api_key = api_key
        self.api_secret = api_secret

        super().__init__(base_url, recv_window=recv_window)

    def _generate_signature(self, api_secret: str, payload: str) -> str:
        """Bingx V5 signature (API v5)."""
        return hmac.new(
            api_secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _prepare_payload(
        self, in_url: bool, params: dict[str, Any], timestamp: int
    ) -> tuple[str, str | None]:
        """
        Prepare BingX payload and URL-encoded payload, as per exchange rules.

        Returns a tuple: (payload_for_signature, url_encoded_payload_for_query)
        """
        # Always work with a sorted list of (k, v) tuples
        if in_url:
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
        params: ParamsType | None = None,
        headers: dict[str, str] | None = None,
        auth: bool = False,
        use_params_as_query: bool = False,
        base_url: str | None = None,
    ) -> tuple[
        dict[str, Any],
        str,
        dict[str, Any] | None,
        list[dict[str, Any]] | dict[str, Any] | None,
        dict[str, Any] | str | None,
    ]:
        # Fast path: avoid unnecessary checks and recomputation
        if self._session.closed:
            session_type = "shared" if self._shared_session else "individual"
            raise RuntimeError(
                f"Session is closed ({session_type}). Create a new HttpClient instance."
            )
        if params is not None and not isinstance(params, Mapping):
            raise TypeError(
                "BingX client does not support list params for 'params'. "
                "Only dict is supported."
            )

        # Prefer local assignment for micro-speed-up
        params = dict(params) if params is not None else {}
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
        in_url = method == "GET" or "/openApi/spot/" in endpoint
        req_payload, req_url_params = self._prepare_payload(in_url, params, timestamp)

        if auth:
            if not (self.api_key and self.api_secret):
                raise ValueError(
                    "API key and API secret must be set for authenticated requests."
                )
            signature = self._generate_signature(self.api_secret, req_payload)
        else:
            signature = None

        base_req_url = f"{base_url if base_url else self.base_url}{endpoint}"

        if in_url:
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
        if self.verbose:
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
        params: ParamsType | None = None,
        headers: dict[str, str] | None = None,
        auth: bool = False,
        use_params_as_query: bool = False,
        base_url: str | None = None,
    ) -> dict[str, Any]:
        (
            req_headers,
            req_url,
            req_params,
            req_json,
            req_data,
        ) = await self._build_request_args(
            method, endpoint, params, headers, auth, use_params_as_query, base_url
        )

        if self.verbose:
            logger.info(
                "Request args: method=%s, headers=%r, url=%r, params=%r, "
                "json=%r, data=%r, base_url=%r",
                method,
                req_headers,
                req_url,
                req_params,
                req_json,
                req_data,
                base_url,
            )

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
                if res_json.get("code") not in (None, 0):
                    raise ExchangeResponseError("bingx", res_json)
            except ExchangeResponseError as err:
                if logger.isEnabledFor(logging.ERROR):
                    logger.error(
                        f"[ExchangeResponseError] method={method} | "
                        f"url={_mask_signature(req_url)} | "
                        f"headers={_mask_headers(req_headers)} | "
                        f"status={resp.status} | "
                        f"error={err}"
                    )
                raise
            except Exception as err:
                if logger.isEnabledFor(logging.ERROR):
                    logger.error(
                        f"[HTTP Error] method={method} | "
                        f"url={_mask_signature(req_url)} | "
                        f"headers={_mask_headers(req_headers)} | "
                        f"status={resp.status} | "
                        f"err={err!r}"
                    )
                raise
            return res_json
