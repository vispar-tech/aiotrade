import base64
import hashlib
import hmac
import logging
import time
from collections.abc import Mapping
from typing import Any

import orjson

from aiotrade._errors import ExchangeResponseError
from aiotrade._http import HttpClient
from aiotrade._protocols import ParamsType
from aiotrade._types import HttpMethod

logger = logging.getLogger("aiotrade.kucoin")


def _mask_headers(headers: dict[str, Any]) -> dict[str, Any]:
    masked: dict[str, Any] = {}
    for k, v in headers.items():
        if k in ("KC-API-KEY", "KC-API-SIGN", "KC-API-PASSPHRASE"):
            masked[k] = v[:6] + "..." if isinstance(v, str) else "****"
        else:
            masked[k] = v
    return masked


class KuCoinHttpClient(HttpClient):
    """KuCoin HTTP client."""

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        passphrase: str | None = None,
        recv_window: int = 5000,
    ) -> None:
        """Initialize HTTP client.

        Args:
            api_key: Trading API key
            api_secret: Trading API secret
            passphrase: Trading API passphrase
            recv_window: Receive window in milliseconds
            broker_tag: Broker tag
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase
        if api_secret is not None and passphrase is not None:
            # Encode KuCoin passphrase using HMAC SHA256, result should be Base64 str
            hm = hmac.new(
                api_secret.encode("utf-8"), passphrase.encode("utf-8"), hashlib.sha256
            )
            self.passphrase = base64.b64encode(hm.digest()).decode()
        else:
            self.passphrase = None

        super().__init__("https://api.kucoin.com", recv_window=recv_window)

    def _generate_signature(
        self,
        api_secret: str,
        method: HttpMethod,
        path: str,
        payload: str,
        timestamp: int,
    ) -> str:
        """KuCoin signature.

        Signature is generated as:
        Base64(HMAC_SHA256(apiSecret, prehash))
        Where prehash = timestamp + method + requestPath + body
        - For GET: body is the sorted query string.
        - For POST: body is the plain JSON string.
        All parts are concatenated as strings.
        """
        body_str = "?" + payload if payload and method == "GET" else payload
        prehash = f"{timestamp}{method.upper()}{path}{body_str}"

        signature = hmac.new(
            api_secret.encode("utf-8"),
            prehash.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        return base64.b64encode(signature).decode()

    def _prepare_payload(self, method: HttpMethod, params: ParamsType) -> str:
        if method == "GET":
            if isinstance(params, Mapping):
                return "&".join(
                    f"{k}={v}" for k, v in sorted(params.items()) if v is not None
                )
            raise TypeError(
                "KuCoin client does not support list params for GET requests. "
                "Only dict is supported."
            )
        sanitized: list[dict[str, Any]] | dict[str, Any]
        # Handle both dict and list[dict[str, Any]] for params
        if isinstance(params, Mapping):
            sanitized = {k: params[k] for k in sorted(params) if params[k] is not None}
            if not sanitized:
                return "{}"
        else:
            sanitized = [
                {k: v for k, v in sorted(d.items()) if v is not None} for d in params
            ]
            if not sanitized or all(not d for d in sanitized):
                return "[]"

        return orjson.dumps(sanitized).decode().replace(":", ": ").replace(",", ", ")

    async def _build_request_args(
        self,
        method: HttpMethod,
        endpoint: str,
        params: ParamsType | None = None,
        headers: dict[str, Any] | None = None,
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
        if params is None:
            params = {}
        elif isinstance(params, Mapping):
            params = dict(params)
        else:
            params = [dict(p) for p in params]

        # Prefer local assignment for micro-speed-up
        req_headers: dict[str, str] = headers if headers is not None else {}

        timestamp = int(time.time() * 1000)

        # Fast payload prep
        req_payload = self._prepare_payload(method, params)

        # Quickly handle signature/auth
        if auth:
            if not (self.api_key and self.api_secret and self.passphrase):
                raise ValueError(
                    "API key, API secret and passphrase "
                    "must be set for authenticated requests."
                )
            signature = self._generate_signature(
                self.api_secret, method, endpoint, req_payload, timestamp
            )
            req_headers["KC-API-KEY"] = self.api_key
            req_headers["KC-API-PASSPHRASE"] = self.passphrase
            req_headers["KC-API-SIGN"] = signature
            req_headers["KC-API-KEY-VERSION"] = "3"
            req_headers["KC-API-TIMESTAMP"] = str(timestamp)
        else:
            signature = None

        req_url = f"{base_url if base_url else self.base_url}{endpoint}"
        req_json: list[dict[str, Any]] | dict[str, Any] | None

        if method == "GET":
            req_url = f"{req_url}?{req_payload}" if req_payload else req_url
            req_json = None
        elif isinstance(params, list):
            # If params is a list[dict[str, Any]], filter Nones inside dicts
            req_json = [
                {k: d[k] for k in sorted(d) if d[k] is not None} for d in params
            ]
        else:
            # Assume dict[str, Any]
            req_json = {k: params[k] for k in sorted(params) if params[k] is not None}

        # Logging fast, avoid joining or formatting unnecessarily unless debug
        if self.verbose:
            logger.debug(
                "Making async %s request to %s with params: %s", method, req_url, params
            )

        return (req_headers, req_url, None, req_json, None)

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
                "Request args: headers=%r, url=%r, params=%r, "
                "json=%r, data=%r, base_url=%r",
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
                content_type = resp.headers.get("Content-Type", "")
                res_json: dict[str, Any]
                if "application/json" in content_type:
                    res_json = await resp.json()
                elif "text/plain" in content_type:
                    text = await resp.text()
                    try:
                        res_json = orjson.loads(text)
                    except Exception:
                        res_json = {"code": resp.status * 10000, "data": {"raw": text}}
                else:
                    # Default: try JSON, fallback error
                    res_json = await resp.json()
                if res_json.get("code") != "200000":
                    raise ExchangeResponseError("kucoin", res_json)
                return res_json
            except ExchangeResponseError as err:
                if logger.isEnabledFor(logging.ERROR):
                    logger.error(
                        f"[ExchangeResponseError] method={method} | "
                        f"url={req_url} | "
                        f"headers={_mask_headers(req_headers)} | "
                        f"status={resp.status} | "
                        f"error={err}"
                    )
                raise
            except Exception as err:
                if logger.isEnabledFor(logging.ERROR):
                    logger.error(
                        f"[HTTP Error] method={method} | "
                        f"url={req_url} | "
                        f"headers={_mask_headers(req_headers)} | "
                        f"status={resp.status} | "
                        f"err={err!r}"
                    )
                raise
