"""Protocols for Bybit API client interfaces."""

from typing import Any, Dict, Protocol


class HttpClientProtocol(Protocol):
    """Protocol defining HTTP client interface for Bybit API."""

    async def get(
        self,
        endpoint: str,
        params: Dict[str, Any] | None = None,
        headers: Dict[str, str] | None = None,
        auth: bool = False,
    ) -> Dict[str, Any]:
        """Send a GET HTTP request."""
        ...

    async def post(
        self,
        endpoint: str,
        params: Dict[str, Any] | None = None,
        headers: Dict[str, str] | None = None,
        auth: bool = False,
    ) -> Dict[str, Any]:
        """Send a POST HTTP request."""
        ...

    async def put(
        self,
        endpoint: str,
        params: Dict[str, Any] | None = None,
        headers: Dict[str, str] | None = None,
        auth: bool = False,
    ) -> Dict[str, Any]:
        """Send a PUT HTTP request."""
        ...

    async def delete(
        self,
        endpoint: str,
        params: Dict[str, Any] | None = None,
        headers: Dict[str, str] | None = None,
        auth: bool = False,
    ) -> Dict[str, Any]:
        """Send a DELETE HTTP request."""
        ...
