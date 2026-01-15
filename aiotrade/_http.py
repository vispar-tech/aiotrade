"""Shared HTTP client module for trading API communication."""

import logging
from abc import ABC, abstractmethod
from types import TracebackType
from typing import Any, Self

import aiohttp

from aiotrade._session import SharedSessionManager
from aiotrade._types import HttpMethod

logger = logging.getLogger("aiotrade.client")


class HttpClient(ABC):
    """Shared asynchronous HTTP client for trading APIs."""

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        api_secret: str | None = None,
        recv_window: int = 5000,
    ) -> None:
        """
        Initialize the HTTP client.

        Args:
            base_url: Base URL for the trading API.
            api_key: Optional trading API key.
            api_secret: Optional trading API secret.
            recv_window: Time in milliseconds representing the
                receive window for signed requests.
        """
        self.base_url = base_url
        self.api_key = api_key
        self.api_secret = api_secret
        self.recv_window = recv_window

        # Use shared session if available; otherwise, create a new aiohttp session.
        if SharedSessionManager.is_initialized():
            self._session = SharedSessionManager.get_session()
            self._shared_session = True
        else:
            connector = aiohttp.TCPConnector(limit=50)
            self._session = aiohttp.ClientSession(
                connector=connector,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )
            self._shared_session = False

    def set_recv_window(self, recv_window: int) -> None:
        """
        Set the receive window value for signed requests.

        Args:
            recv_window: New time in milliseconds for the receive window.
        """
        self.recv_window = recv_window

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

    @abstractmethod
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
        """
        Prepare the arguments required for making an HTTP request.

        Returns a tuple containing:
            - aiohttp request kwargs (dict)
            - resolved URL (str)
            - parameters (dict or None)
            - headers (dict or None)
            - extra kwargs (dict or None)
        """
        ...

    @abstractmethod
    async def _async_request(
        self,
        method: HttpMethod,
        endpoint: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        auth: bool = False,
    ) -> dict[str, Any]:
        """
        Execute an asynchronous HTTP request using the given parameters.

        Returns the decoded JSON response as a dictionary.
        """
        ...

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
