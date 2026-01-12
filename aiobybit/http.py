"""HTTP client module for Bybit API communication."""

import hashlib
import hmac
import json
import logging
import time
from types import TracebackType
from typing import Any, Literal, Self

import aiohttp

HttpMethod = Literal["GET", "POST", "PUT", "DELETE"]

logger = logging.getLogger(__name__)


DOMAIN_MAIN = "bybit"
TLD_MAIN = "com"


class BybitHttpClient:
    """Asynchronous HTTP client for Bybit API (main, testnet, demo; NO bytick)."""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
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
        # subdomain logic for main, testnet, demo, testnet-demo
        if demo and testnet:
            sub = "api-demo-testnet"
        elif demo:
            sub = "api-demo"
        elif testnet:
            sub = "api-testnet"
        else:
            sub = "api"
        # Compose URL for only BYBIT main/testnet/demo endpoints
        self.base_url = f"https://{sub}.{DOMAIN_MAIN}.{TLD_MAIN}"
        self.api_key = api_key
        self.api_secret = api_secret
        self.recv_window = recv_window
        self.referral_id = referral_id
        self._async_session: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> Self:
        """Enter async context manager and initialize HTTP session."""
        logger.debug("Initializing asynchronous session.")
        connector = aiohttp.TCPConnector(limit=50)
        self._async_session = aiohttp.ClientSession(connector=connector)
        self._configure_session()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Exit async context manager and close HTTP session."""
        logger.debug("Exiting asynchronous context manager.")
        if self._async_session:
            await self._async_session.close()
            self._async_session = None

    def _configure_session(self) -> None:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.referral_id:
            headers["Referer"] = self.referral_id
        if self._async_session:
            self._async_session.headers.update(headers)

    def _generate_signature(self, payload: str, timestamp: str) -> str:
        """Bybit V5 signature (API v5).

        sign = (apiSecret, timestamp + apiKey + recvWindow + payload).
        payload:
            * for GET: query string (sorted, url-encoded if needed)
            * for POST: plain json string.
        """
        param_str = timestamp + self.api_key + str(self.recv_window) + payload
        return hmac.new(
            self.api_secret.encode("utf-8"),
            param_str.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _prepare_payload(self, method: HttpMethod, params: dict[str, Any]) -> str:
        # params should be ordered by param name, asc
        string_params = {"qty", "price", "triggerPrice", "takeProfit", "stopLoss"}
        for k in string_params:
            if k in params and not isinstance(params[k], str):
                params[k] = str(params[k])
        if method == "GET":
            filtered = [(k, v) for k, v in params.items() if v is not None]
            filtered.sort()
            return "&".join(f"{k}={v}" for k, v in filtered)
        sorted_params = {k: params[k] for k in sorted(params) if params[k] is not None}
        return (
            json.dumps(sorted_params, separators=(",", ":")) if sorted_params else "{}"
        )

    async def _async_request(
        self,
        method: HttpMethod,
        endpoint: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        auth: bool = True,
    ) -> dict[str, Any]:
        if not self._async_session:
            raise RuntimeError(
                "Asynchronous session is not initialized. "
                "Use context manager (async with).",
            )
        params = params or {}
        headers = headers or {}
        timestamp = str(int(time.time() * 1000))
        if auth:
            payload = self._prepare_payload(method, params)
            signature = self._generate_signature(payload, timestamp)
            headers.update(
                {
                    "X-BAPI-API-KEY": self.api_key,
                    "X-BAPI-SIGN": signature,
                    "X-BAPI-SIGN-TYPE": "1",
                    "X-BAPI-TIMESTAMP": timestamp,
                    "X-BAPI-RECV-WINDOW": str(self.recv_window),
                },
            )
        url = f"{self.base_url}{endpoint}"
        logger.debug(f"Making async {method} request to {url} with params: {params}")

        req_params = params if method == "GET" and params else None
        req_json = (
            None
            if method == "GET"
            else {k: v for k, v in params.items() if v is not None}
            if params
            else None
        )

        async with self._async_session.request(
            method,
            url,
            params=req_params,
            json=req_json,
            headers=headers,
        ) as resp:
            try:
                resp.raise_for_status()
                res_json: dict[str, Any] = await resp.json(content_type=None)
            except Exception:
                logger.error(
                    f"Request error: method={method}, url={url}, "
                    f"params={params}, headers={headers}",
                )
                raise
            if res_json.get("retCode") == 10004:
                payload = self._prepare_payload(method, params)
                logger.error(
                    f"Bybit signature error (retCode 10004): {res_json.get('retMsg')}\n"
                    f"Origin string is: "
                    f"'{timestamp + self.api_key + str(self.recv_window) + payload}'. "
                    f"Params: {params}",
                )
                raise Exception(res_json.get("retMsg", "Unknown error"))
            return res_json

    async def get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        auth: bool = True,
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
        auth: bool = True,
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
        auth: bool = True,
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
        auth: bool = True,
    ) -> dict[str, Any]:
        """Async DELETE request."""
        return await self._async_request(
            method="DELETE",
            endpoint=endpoint,
            params=params,
            headers=headers,
            auth=auth,
        )
