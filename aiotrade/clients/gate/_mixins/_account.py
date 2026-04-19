from typing import Any

from aiotrade._protocols import HttpClientProtocol


class AccountMixin:
    async def get_account_detail(
        self: HttpClientProtocol,
    ) -> dict[str, Any]:
        """
        Retrieve user account information.

        Returns:
            Dictionary with account detail.

        Endpoint: GET /account/detail
        """
        return await self.get(
            "/account/detail",
            auth=True,
        )

    async def get_account_main_keys(
        self: HttpClientProtocol,
    ) -> dict[str, Any]:
        """
        Query all account main key information.

        Returns:
            List of main account key information.

        Endpoint: GET /account/main_keys
        """
        return await self.get(
            "/account/main_keys",
            auth=True,
        )
