"""Protocols for Bybit API client interfaces."""

from collections.abc import Mapping, Sequence
from typing import Any, Protocol

ParamsType = Mapping[str, Any] | Sequence[Mapping[str, Any]]


class HttpClientProtocol(Protocol):
    """Protocol defining HTTP client interface for Bybit API."""

    async def get(
        self,
        endpoint: str,
        params: ParamsType | None = None,
        headers: dict[str, str] | None = None,
        auth: bool = False,
    ) -> dict[str, Any]:
        """Send a GET HTTP request."""
        ...

    async def post(
        self,
        endpoint: str,
        params: ParamsType | None = None,
        headers: dict[str, str] | None = None,
        auth: bool = False,
    ) -> dict[str, Any]:
        """Send a POST HTTP request."""
        ...

    async def put(
        self,
        endpoint: str,
        params: ParamsType | None = None,
        headers: dict[str, str] | None = None,
        auth: bool = False,
    ) -> dict[str, Any]:
        """Send a PUT HTTP request."""
        ...

    async def delete(
        self,
        endpoint: str,
        params: ParamsType | None = None,
        headers: dict[str, str] | None = None,
        auth: bool = False,
    ) -> dict[str, Any]:
        """Send a DELETE HTTP request."""
        ...
