from typing import Any, Dict

from aiotrade._protocols import HttpClientProtocol


class UserMixin:
    """Mixin for user endpoints."""

    async def get_api_key_info(
        self: HttpClientProtocol,
    ) -> Dict[str, Any]:
        """
        Get API Key information.

        See:
            https://bybit-exchange.github.io/docs/v5/user/apikey-info

        Returns:
            Dict with API key information response.
        """
        return await self.get(
            "/v5/user/query-api",
            params=None,
            auth=True,
        )
