import hashlib
import hmac
import json
import logging
import time
from collections.abc import Mapping
from operator import itemgetter
from typing import Any
from urllib import parse

from aiotrade._errors import ExchangeResponseError
from aiotrade._http import HttpClient
from aiotrade._protocols import ParamsType
from aiotrade._types import HttpMethod

logger = logging.getLogger("aiotrade.binance")


def _mask_headers(headers: dict[str, Any]) -> dict[str, Any]:
    masked: dict[str, Any] = {}
    for k, v in headers.items():
        if k in ("X-MBX-APIKEY",):
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


class BinanceHttpClient(HttpClient):
    """Binance HTTP client."""

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        demo: bool = False,
        recv_window: int = 5000,
        broker_id: str | None = None,
    ) -> None:
        """Initialize HTTP client.

        Args:
            api_key: Trading API key
            api_secret: Trading API secret
            demo: Use demo trading
            recv_window: Receive window in milliseconds
            broker_id: Referral ID
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.demo = demo
        self.broker_id = broker_id

        super().__init__(
            "https://api.binance.com",
            recv_window=recv_window,
        )

    def _generate_signature(self, api_secret: str, payload: str) -> str:
        """Binance signature."""
        return hmac.new(
            api_secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _prepare_payload(
        self,
        method: HttpMethod,
        params: dict[str, Any],
    ) -> str:
        """
        Prepare BingX payload and URL-encoded payload, as per exchange rules.

        Returns a string url params
        """
        sorted_params = sorted(params.items())
        # Always work with a sorted list of (k, v) tuples
        if method == "GET":
            # Any structured value triggers full encoding
            contains_struct = any(
                isinstance(v, (dict, list))
                or (isinstance(v, str) and ("{" in v or "[" in v))
                for _, v in sorted_params
            )
            if contains_struct:
                url_params_str = "&".join(
                    f"{k}={parse.quote(str(v), safe='')}" for k, v in sorted_params
                )
            else:
                url_params_str = "&".join(f"{k}={v}" for k, v in sorted_params)
            return url_params_str

        items: list[tuple[str, str]] = []
        for k, v in sorted_params:
            if isinstance(v, dict):
                items.append((k, json.dumps(sorted(v.items()))))
            else:
                items.append((k, str(v)))
        return "&".join(f"{k}={v!s}" for k, v in items)

    @staticmethod
    def _order_params(data: dict[str, Any]) -> list[tuple[str, str]]:
        """Convert params to list with signature as last element."""
        data = dict(filter(lambda el: el[1] is not None, data.items()))
        has_signature = False
        params: list[tuple[str, str]] = []
        for key, value in data.items():
            if key == "signature":
                has_signature = True
            else:
                params.append((key, str(value)))
        # sort parameters by key
        params.sort(key=itemgetter(0))
        if has_signature:
            params.append(("signature", data["signature"]))
        return params

    def _fix_batch_orders_request(self, params: dict[str, Any]) -> dict[str, Any]:
        for order in params["batchOrders"]:
            order = self._order_params(order)
        query_string = parse.urlencode(params).replace("%40", "@").replace("%27", "%22")
        params["batchOrders"] = query_string[12:]
        return params

    async def _build_request_args(
        self,
        method: HttpMethod,
        endpoint: str,
        params: ParamsType | None = None,
        headers: dict[str, str] | None = None,
        auth: bool = False,
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

        if auth and not (self.api_key and self.api_secret):
            raise ValueError(
                "API key and API secret must be set for authenticated requests."
            )

        if "batchOrders" in params:
            params = self._fix_batch_orders_request(params)

        # Set recv window from cls
        params["recvWindow"] = self.recv_window
        params["timestamp"] = timestamp
        req_payload = self._prepare_payload(method, params)
        req_body = None

        if auth:
            if not (self.api_key and self.api_secret):
                raise ValueError(
                    "API key and API secret must be set for authenticated requests."
                )
            req_headers["X-MBX-APIKEY"] = self.api_key
            signature = self._generate_signature(self.api_secret, req_payload)
        else:
            signature = None

        req_url = f"{base_url if base_url else self.base_url}{endpoint}"

        if method == "GET":
            req_url = f"{req_url}?{req_payload}" if req_payload else req_url
            if signature:
                req_url += (
                    f"?signature={signature}"
                    if not req_payload
                    else f"&signature={signature}"
                )
        elif method in ["POST", "PUT", "DELETE"]:
            req_headers.update({"Content-Type": "application/x-www-form-urlencoded"})
            req_body = req_payload
            if signature:
                req_body += (
                    f"?signature={signature}"
                    if not req_payload
                    else f"&signature={signature}"
                )

        # Logging fast, avoid joining or formatting unnecessarily unless debug
        if self.verbose:
            logger.debug(
                "Making async %s request to %s with params: %s",
                method,
                req_url,
                params,
            )

        return (
            req_headers,
            req_url,
            None,
            None,
            req_body,
        )

    async def _async_request(
        self,
        method: HttpMethod,
        endpoint: str,
        params: ParamsType | None = None,
        headers: dict[str, str] | None = None,
        auth: bool = False,
        base_url: str | None = None,
    ) -> dict[str, Any]:
        (
            req_headers,
            req_url,
            req_params,
            req_json,
            req_data,
        ) = await self._build_request_args(
            method, endpoint, params, headers, auth, base_url
        )
        if self.verbose:
            logger.info(
                "Request args: headers=%r, url=%r, params=%r, json=%r, data=%r",
                req_headers,
                req_url,
                req_params,
                req_json,
                req_data,
            )

        wrapped: dict[str, Any]

        async with self._session.request(
            method,
            req_url,
            params=req_params,
            json=req_json,
            data=req_data,
            headers=req_headers,
        ) as resp:
            try:
                # Try to parse JSON response; fallback to None if not JSON
                try:
                    response_content = await resp.json(content_type=None)
                except Exception:
                    response_content = None

                response_message = resp.reason if not resp.ok else "ok"
                response_code = resp.status

                if isinstance(response_content, dict):
                    # Pop 'msg' if present for a friendly message
                    if "msg" in response_content:
                        response_message = response_content.pop("msg")
                    # Pop 'code' if present for code override
                    if "code" in response_content:
                        response_code = response_content.pop("code")
                elif isinstance(response_content, list):
                    # Always wrap lists in a result container
                    response_content = {"list": response_content}

                wrapped = {
                    "retCode": response_code,
                    "retMsg": response_message or "unknown",
                    "result": response_content,
                }

                if not resp.ok or (400 < response_code < 200):
                    raise ExchangeResponseError("binance", wrapped)
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
            return wrapped
