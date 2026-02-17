from typing import Any, Dict

from aiotrade._protocols import HttpClientProtocol


class SpotMixin:
    """Spot copytrading-related methods for BingX API client.

    This mixin provides methods for managing spot copytrading operations.
    """

    async def sell_spot_asset_by_order(
        self: HttpClientProtocol,
        order_id: int,
    ) -> Dict[str, Any]:
        """
        Trader sells spot assets based on buy order number.

        POST /openApi/copyTrading/v1/spot/trader/sellOrder

        See:
            https://bingx-api.github.io/docs-v3/#/en/Copy%20Trade/Spot%20Trading/Trader%20sells%20spot%20assets%20based%20on%20buy%20order%20number

        Args:
            order_id: Trader's spot buy order number

        Returns:
            Dict with API response for the sell operation.
        """
        params = {
            "orderId": order_id,
        }
        return await self.post(
            "/openApi/copyTrading/v1/spot/trader/sellOrder",
            params=params,
            auth=True,
        )

    async def get_personal_trading_overview(
        self: HttpClientProtocol,
    ) -> Dict[str, Any]:
        """
        Get spot trader's copy trading overview (cumulative profits, copier profit).

        GET /openApi/copyTrading/v1/spot/traderDetail

        See:
            https://bingx-api.github.io/docs-v3/#/en/Copy%20Trade/Spot%20Trading/Personal%20Trading%20Overview

        Returns:
            Dict with trading overview response.
        """
        return await self.get(
            "/openApi/copyTrading/v1/spot/traderDetail",
            auth=True,
        )

    async def get_profit_overview(
        self: HttpClientProtocol,
    ) -> Dict[str, Any]:
        """
        Get spot trader's profit overview (cumulative profit, copier profit, etc).

        GET /openApi/copyTrading/v1/spot/profitHistorySummarys

        See:
            https://bingx-api.github.io/docs-v3/#/en/Copy%20Trade/Spot%20Trading/Profit%20Summary

        Returns:
            Dict with profit overview response.
        """
        return await self.get(
            "/openApi/copyTrading/v1/spot/profitHistorySummarys",
            auth=True,
        )

    async def get_profit_details(
        self: HttpClientProtocol,
        page_index: int,
        page_size: int,
        start_time: int | None = None,
        end_time: int | None = None,
    ) -> Dict[str, Any]:
        """
        Get spot trader's profit details (paginated).

        GET /openApi/copyTrading/v1/spot/profitDetail

        See:
            https://bingx-api.github.io/docs-v3/#/en/Copy%20Trade/Spot%20Trading/Profit%20Details

        Args:
            page_index: Page number; must be > 0.
            page_size: Number of items per page; must be > 0, max 100.
            start_time: Start timestamp (ms) for profit distribution filter (optional).
            end_time: End timestamp (ms) for profit distribution filter (optional).

        Returns:
            Dict with page of profit detail results.
        """
        params = {
            "pageIndex": page_index,
            "pageSize": page_size,
        }
        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time

        return await self.get(
            "/openApi/copyTrading/v1/spot/profitDetail",
            params=params,
            auth=True,
        )

    async def get_history_orders(
        self: HttpClientProtocol,
        page_index: int,
        page_size: int,
        symbol: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
    ) -> Dict[str, Any]:
        """
        Query historical spot copytrading orders.

        GET /openApi/copyTrading/v1/spot/historyOrder

        See:
            https://bingx-api.github.io/docs-v3/#/en/Copy%20Trade/Spot%20Trading/Query%20Historical%20Orders

        Args:
            page_index (int): Page index, must be greater than 0.
            page_size (int): Number of items per page, must be greater than 0,
                maximum 100.
            symbol (str, optional): Trading pair (e.g. "BTC-USDT").
            start_time (int, optional): Start timestamp in milliseconds,
                query orders within the time range.
            end_time (int, optional): End timestamp in milliseconds,
                query orders within the time range.

        Returns:
            Dict[str, Any]: Page of historical spot copytrading order results.
        """
        params: dict[str, Any] = {
            "pageIndex": page_index,
            "pageSize": page_size,
        }
        if symbol is not None:
            params["symbol"] = symbol
        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time

        return await self.get(
            "/openApi/copyTrading/v1/spot/historyOrder",
            params=params,
            auth=True,
        )
