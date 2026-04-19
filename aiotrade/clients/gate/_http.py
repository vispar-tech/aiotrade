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

logger = logging.getLogger("aiotrade.gate")


def _mask_headers(headers: dict[str, Any]) -> dict[str, Any]:
    masked: dict[str, Any] = {}
    for k, v in headers.items():
        if k in ("KEY", "SIGN"):
            masked[k] = v[:6] + "..." if isinstance(v, str) else "****"
        else:
            masked[k] = v
    return masked


class GateHttpClient(HttpClient):
    """Gate HTTP client."""

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        demo: bool = False,
        broker_tag: str | None = None,
    ) -> None:
        """Initialize HTTP client.

        Args:
            api_key: Trading API key
            api_secret: Trading API secret
            demo: Use demo trading
            broker_tag: Broker tag
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.demo = demo
        self.broker_tag = broker_tag

        self._api_prefix = "/api/v4"
        super().__init__(
            "https://api-testnet.gateapi.io" if demo else "https://api.gateio.ws"
        )

    def _generate_signature(
        self,
        api_secret: str,
        method: HttpMethod,
        path: str,
        payload: str,
        query_payload: str,
        timestamp: int,
    ) -> str:
        """
        Generate only the sign for Gate.io API v4.

        Returns:
            The signature string.
        """
        # Use fast local variable and avoid unnecessary string conversions
        encoded_payload = (payload or "").encode("utf-8")
        hashed_payload = hashlib.sha512(encoded_payload).hexdigest()

        # Preallocate and join parts to avoid redundant string formatting
        parts = [
            method,
            path,
            query_payload,
            hashed_payload,
            str(timestamp),
        ]
        sign_str = "\n".join(parts)

        # Pre-encode, use memoryview to avoid copy if possible
        encoded_sign_str = sign_str.encode("utf-8")
        encoded_secret = api_secret.encode("utf-8")

        # Use hmac directly, avoid extra allocations
        return hmac.new(encoded_secret, encoded_sign_str, hashlib.sha512).hexdigest()

    def _prepare_payload(
        self,
        method: HttpMethod,
        params: ParamsType,
        use_params_as_query: bool = False,
    ) -> tuple[str, str]:
        """Prepare the canonical payload body for POST/PUT, or query string for GET."""
        if method == "GET" or use_params_as_query:
            if isinstance(params, Mapping):
                return "", "&".join(
                    f"{k}={v}" for k, v in sorted(params.items()) if v is not None
                )
            raise TypeError(
                "GATE client does not support list params for GET requests. "
                "Only dict is supported."
            )
        sanitized: list[dict[str, Any]] | dict[str, Any]
        # Handle both dict and list[dict[str, Any]] for params
        if isinstance(params, Mapping):
            sanitized = {k: params[k] for k in sorted(params) if params[k] is not None}
            if not sanitized:
                return "{}", ""
        elif isinstance(params, list):
            sanitized = list(params)
        else:
            sanitized = [
                {k: v for k, v in sorted(d.items()) if v is not None} for d in params
            ]
            if not sanitized or all(not d for d in sanitized):
                return "[]", ""

        # Note: need Gate logic for signature
        # serialization must match server expectations
        return orjson.dumps(sanitized).decode().replace(":", ": ").replace(
            ",", ", "
        ), ""

    async def _build_request_args(  # noqa: PLR0912
        self,
        method: HttpMethod,
        endpoint: str,
        params: ParamsType | None = None,
        headers: dict[str, Any] | None = None,
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
        if params is None:
            params = {}
        elif "batch_cancel_orders" in endpoint:
            params = list(params)  # type: ignore
        elif isinstance(params, Mapping):
            params = dict(params)
        else:
            params = [dict(p) for p in params]

        # Prefer local assignment for micro-speed-up
        req_headers: dict[str, str] = headers if headers is not None else {}
        endpoint = self._api_prefix + endpoint

        timestamp = int(time.time())

        req_headers["Timestamp"] = str(timestamp)
        if self.demo:
            req_headers["DEMO"] = "1"

        # Fast payload prep
        req_payload, req_query = self._prepare_payload(
            method,
            params,
            use_params_as_query=use_params_as_query,
        )

        # Quickly handle signature/auth
        if auth:
            if not (self.api_key and self.api_secret):
                raise ValueError(
                    "API key and API secret must be set for authenticated requests."
                )

            signature = self._generate_signature(
                self.api_secret, method, endpoint, req_payload, req_query, timestamp
            )
            req_headers["KEY"] = self.api_key
            req_headers["SIGN"] = signature

        else:
            signature = None

        req_url = f"{base_url if base_url else self.base_url}{endpoint}"
        req_json: list[dict[str, Any]] | dict[str, Any] | None

        if method == "GET" or use_params_as_query:
            req_url = f"{req_url}?{req_query}" if req_query else req_url
            req_json = None
        elif isinstance(params, list):
            if "batch_cancel_orders" in endpoint:
                req_json = list(params)
            else:
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

        wrapped: dict[str, Any]
        response_content: dict[str, Any] | list[dict[str, Any]] | None

        async with self._session.request(
            method,
            req_url,
            params=req_params,
            json=req_json,
            data=req_data,
            headers=req_headers,
        ) as resp:
            try:
                try:
                    response_content = await resp.json(content_type=None)
                except Exception:
                    response_content = None

                response_message = resp.reason if not resp.ok else "ok"
                response_code = resp.status

                error_message = None
                label_message = None
                if isinstance(response_content, dict) and (
                    "label" in response_content or "message" in response_content
                ):
                    error_message = response_content.pop("message", None)
                    label_message = response_content.pop("label", None)

                if isinstance(response_content, list):
                    # Always wrap lists in a result container
                    response_content = {"list": response_content}

                wrapped = {
                    "retCode": response_code,
                    "retMsg": (
                        error_message or label_message or response_message or "unknown"
                    ),
                    "result": response_content,
                }

                if not resp.ok:
                    raise ExchangeResponseError("gate", wrapped)
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
            return wrapped
