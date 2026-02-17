from typing import Any, Dict, Literal

from aiotrade._protocols import HttpClientProtocol


class PerpetualMixin:
    """
    Perpetual copytrading-related methods for BingX API client.

    This mixin provides methods for managing perpetual copytrading operations.
    """

    async def get_perpetual_current_trader_order(
        self: HttpClientProtocol,
        symbol: str,
        offset: int = 0,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        Get current trader's order (copy position) for perpetual contracts.

        See:
            https://bingx-api.github.io/docs-v3/#/en/Copy%20Trade/USDT-M%20Perpetual%20Contracts/Trader%E2%80%99s%20current%20order

        Args:
            symbol: Trading pair, e.g. "BTC-USDT" (uppercase, required).
            offset: Offset for record pagination (default: 0).
            limit: Number of records to return (default: 20, max: 50).

        Returns:
            Dict with API response for current open (copy-traded) orders.
        """
        params = {
            "symbol": symbol,
            "offset": offset,
            "limit": limit,
        }
        return await self.get(
            "/openApi/copyTrading/v1/swap/trace/currentTrack",
            params=params,
            auth=True,
        )

    async def close_perpetual_trader_position_by_order(
        self: HttpClientProtocol,
        position_id: int,
    ) -> Dict[str, Any]:
        """
        Close trader perpetual position by order number.

        See:
            https://bingx-api.github.io/docs-v3/#/en/Copy%20Trade/USDT-M%20Perpetual%20Contracts/Traders%20close%20positions%20according%20to%20the%20order%20number

        Args:
            position_id: Order number for the position to be closed.

        Returns:
            Dict with close position response.
        """
        params = {
            "positionId": position_id,
        }
        return await self.post(
            "/openApi/copyTrading/v1/swap/trace/closeTrackOrder",
            params=params,
            auth=True,
        )

    async def set_perpetual_trader_tpsl_by_order(
        self: HttpClientProtocol,
        position_id: int,
        take_profit_mark_price: float,
        stop_loss_mark_price: float,
    ) -> Dict[str, Any]:
        """
        Set take-profit and stop-loss for perpetual position by order number.

        See:
            https://bingx-api.github.io/docs-v3/#/en/Copy%20Trade/USDT-M%20Perpetual%20Contracts/Traders%20set%20take%20profit%20and%20stop%20loss%20based%20on%20order%20numbers

        Args:
            position_id: Order number for which to set TP/SL.
            take_profit_mark_price: Mark price for take profit.
            stop_loss_mark_price: Mark price for stop loss.

        Returns:
            Dict with set TP/SL response.
        """
        params = {
            "positionId": position_id,
            "takeProfitMarkPrice": take_profit_mark_price,
            "stopLossMarkPrice": stop_loss_mark_price,
        }
        return await self.post(
            "/openApi/copyTrading/v1/swap/trace/setTPSL",
            params=params,
            auth=True,
        )

    async def get_perpetual_personal_trading_overview(
        self: HttpClientProtocol,
        day_size: Literal[7, 30, 90, 180] | None = None,
    ) -> Dict[str, Any]:
        """
        Get perpetual trader's copy trading overview (cumulative profits, gains, etc).

        See:
            https://bingx-api.github.io/docs-v3/#/en/Copy%20Trade/USDT-M%20Perpetual%20Contracts/Trader%20Detail

        Args:
            day_size: Profit rate over the last N days; must be 7, 30, 90, or 180.

        Returns:
            Dict with trading overview response.
        """
        params: dict[str, Any] = {}
        if day_size is not None:
            params["daySize"] = day_size

        return await self.get(
            "/openApi/copyTrading/v1/PFutures/traderDetail",
            params=params,
            auth=True,
        )

    async def get_perpetual_profit_overview(
        self: HttpClientProtocol,
    ) -> Dict[str, Any]:
        """
        Get perpetual trader's profit overview (cumulative profit, gains, etc).

        See:
            https://bingx-api.github.io/docs-v3/#/en/Copy%20Trade/USDT-M%20Perpetual%20Contracts/Profit%20Overview

        Returns:
            Dict with profit overview response.
        """
        return await self.get(
            "/openApi/copyTrading/v1/PFutures/profitHistorySummarys",
            auth=True,
        )

    async def get_perpetual_profit_details(
        self: HttpClientProtocol,
        page_index: int,
        page_size: int,
        start_time: int | None = None,
        end_time: int | None = None,
    ) -> Dict[str, Any]:
        """
        Get perpetual trader's profit details (paginated).

        See:
            https://bingx-api.github.io/docs-v3/#/en/Copy%20Trade/USDT-M%20Perpetual%20Contracts/Profit%20Details

        Args:
            page_index: Page number; must be > 0.
            page_size: Number of items per page; must be > 0, max 100.
            start_time: Start timestamp (ms) for profit distribution filter (optional).
            end_time: End timestamp (ms) for profit distribution filter (optional).

        Returns:
            Dict with page of profit detail results.
        """
        params: dict[str, Any] = {
            "pageIndex": page_index,
            "pageSize": page_size,
        }
        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time

        return await self.get(
            "/openApi/copyTrading/v1/PFutures/profitDetail",
            params=params,
            auth=True,
        )

    async def set_perpetual_commission_rate(
        self: HttpClientProtocol,
        new_commission: int,
    ) -> Dict[str, Any]:
        """
        Set perpetual trader's commission rate.

        See:
            https://bingx-api.github.io/docs-v3/#/en/Copy%20Trade/USDT-M%20Perpetual%20Contracts/Set%20Commission%20Rate

        Args:
            new_commission: The commission rate to set (int),
                must be > 10 and less than current level.
                Silver: 16%, Gold: 20%, Diamond: 32%.

        Returns:
            Dict with commission set response.
        """
        params = {"newCommission": f"{new_commission}%"}
        return await self.post(
            "/openApi/copyTrading/v1/PFutures/setCommission",
            params=params,
            auth=True,
        )

    async def get_perpetual_copy_trading_pairs(
        self: HttpClientProtocol,
        contract_type: Literal["SFUTURES", "PFUTURES"],
    ) -> Dict[str, Any]:
        """
        Get supported perpetual copy trading pairs.

        See:
            https://bingx-api.github.io/docs-v3/#/en/Copy%20Trade/USDT-M%20Perpetual%20Contracts/Trader%20Gets%20Copy%20Trading%20Pairs

        Args:
            contract_type: Contract type.

        Returns:
            Dict with supported pair info.
        """
        params = {"contractType": contract_type}
        return await self.get(
            "/openApi/copyTrading/v1/PFutures/tradingPairs",
            params=params,
            auth=True,
        )
