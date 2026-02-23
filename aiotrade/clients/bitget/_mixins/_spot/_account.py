from typing import Any, Literal

from aiotrade._protocols import HttpClientProtocol


class AccountMixin:
    async def get_account_info(self: HttpClientProtocol) -> dict[str, Any]:
        """
        Get account information.

        Frequency limit: 1 request/sec per User ID.

        API Reference:
            GET /api/v2/spot/account/info

        Returns:
            dict[str, Any]: API response with detailed account information.
        """
        return await self.get(
            "/api/v2/spot/account/info",
            auth=True,
        )

    async def get_account_assets(
        self: HttpClientProtocol,
        coin: str | None = None,
        asset_type: Literal["hold_only", "all"] | None = None,
    ) -> dict[str, Any]:
        """
        Get Account Assets.

        Frequency limit: 10 requests/sec per User ID.

        API Reference:
            GET /api/v2/spot/account/assets

        Args:
            coin: Token name, e.g. "USDT".
                This field is used for querying the positions of a single coin.
            asset_type: Asset type, e.g., "hold_only" (default), or "all".
                - hold_only: Position coin
                - all: All coins
                Used for querying multiple coins.
                When only assetType is entered without coin,
                    results of all eligible coins are returned.
                When both coin and assetType are entered, coin has higher priority.

        Returns:
            dict[str, Any]: API response with account asset information.
        """
        params: dict[str, str] = {}
        if coin is not None:
            params["coin"] = coin
        if asset_type is not None:
            params["assetType"] = asset_type

        return await self.get(
            "/api/v2/spot/account/assets",
            params=params,
            auth=True,
        )
