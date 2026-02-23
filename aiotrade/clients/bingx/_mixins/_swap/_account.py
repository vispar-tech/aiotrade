from typing import Any

from aiotrade._protocols import HttpClientProtocol


class AccountMixin:
    """Account management methods for BingX swap API client.

    This mixin provides methods for managing swap trading accounts
    and account-related operations.
    """

    async def get_swap_positions(
        self: "HttpClientProtocol",
        symbol: str | None = None,
    ) -> dict[str, Any]:
        """Retrieve information on user's Perpetual Swap positions.

        GET /openApi/swap/v2/user/positions

        https://bingx-api.github.io/docs-v3/#/en/Swap/Account%20Endpoints/Query%20position%20data

        Args:
            symbol: Pair symbol (e.g., "BTC-USDT"). If None, query all.
                                    If None, query all positions.

        Returns:
            dict[str, Any]: API response containing position data.
        """
        params: dict[str, Any] = {}
        if symbol is not None:
            params["symbol"] = symbol

        return await self.get(
            "/openApi/swap/v2/user/positions",
            params=params,
            auth=True,
        )

    async def get_swap_account_balance(
        self: "HttpClientProtocol",
    ) -> dict[str, Any]:
        """
        Retrieve user's Perpetual Swap account balance.

        GET /openApi/swap/v3/user/balance

        https://bingx-api.github.io/docs-v3/#/en/Swap/Account%20Endpoints/Query%20account%20data

        Returns:
            dict[str, Any]: API response containing account balance data.
        """
        return await self.get(
            "/openApi/swap/v3/user/balance",
            auth=True,
        )
