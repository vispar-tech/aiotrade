from typing import Any

from aiotrade._protocols import HttpClientProtocol


class AccountMixin:
    """Wallet account endpoints."""

    async def get_api_key_permissions(
        self: "HttpClientProtocol",
    ) -> dict[str, Any]:
        """
        Get API Key Permission.

        API Docs:
            GET /sapi/v1/account/apiRestrictions

        Returns:
            dict: API JSON response containing API key permissions.
        """
        return await self.get(
            "/sapi/v1/account/apiRestrictions",
            auth=True,
        )
