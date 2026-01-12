"""HTTP client module for Bybit API communication."""

import hashlib
import hmac
import json
import logging
import time
from types import TracebackType
from typing import Any, Literal, Self

import aiohttp

from .session import BybitSessionManager

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

    def _generate_signature(self, payload: str, timestamp: str) -> str:
        """Bybit V5 signature (API v5).

        Signature is generated as:
        HMAC_SHA256(apiSecret, timestamp + apiKey + recvWindow + payload)
        - For GET: payload is the sorted query string.
        - For POST: payload is the plain JSON string.
        """
        param_str = timestamp + self.api_key + str(self.recv_window) + payload
        return hmac.new(
            self.api_secret.encode("utf-8"),
            param_str.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _prepare_payload(self, method: HttpMethod, params: dict[str, Any]) -> str:
        # Ensure certain params are always strings
        string_params = {"qty", "price", "triggerPrice", "takeProfit", "stopLoss"}
        for k in string_params:
            if k in params and not isinstance(params[k], str):
                params[k] = str(params[k])
        if method == "GET":
            # For GET, sort and join non-None params into a query string
            filtered = [(k, v) for k, v in params.items() if v is not None]
            filtered.sort()
            return "&".join(f"{k}={v}" for k, v in filtered)
        # For POST/PUT/DELETE, return compact JSON (sorted keys, omit None)
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
        if self._session.closed:
            session_type = "shared" if self._shared_session else "individual"
            raise RuntimeError(
                f"Session is closed ({session_type}). "
                "Create a new BybitHttpClient instance.",
            )
        params = params or {}
        headers = headers or {}

        # Add referral_id as Referer header if present
        if self.referral_id:
            headers["Referer"] = self.referral_id

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

        async with self._session.request(
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

    @property
    def uses_shared_session(self) -> bool:
        """Check if this client uses a shared session."""
        return self._shared_session

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
