from typing import Any

from aiotrade._protocols import HttpClientProtocol


class AccountMixin:
    """Spot Account endpoints mixin."""

    async def get_spot_account_info(
        self: HttpClientProtocol,
        omit_zero_balances: bool = True,
    ) -> dict[str, Any]:
        """
        Get current SPOT account information.

        API Docs:
            GET /api/v3/account

        Rate Limit Weight: 20

        Args:
            omit_zero_balances: If True,
                emits only the non-zero balances of the account.
                Default: True.

        Returns:
            dict: API JSON response containing account information.
        """
        params: dict[str, Any] = {}
        if omit_zero_balances:
            params["omitZeroBalances"] = "true"
        return await self.get(
            "/api/v3/account",
            params=params,
            auth=True,
        )

    async def get_spot_open_orders(
        self: HttpClientProtocol,
        symbol: str | None = None,
    ) -> dict[str, Any]:
        """
        Get all current open spot orders for a symbol, or all symbols if not provided.

        API Docs:
            GET /api/v3/openOrders

        Weight: 6 (with symbol), 80 (without symbol)

        Args:
            symbol: The symbol to get open orders for. If omitted,
                all symbols' orders will be returned.


        Returns:
            dict: API JSON response containing open orders.
        """
        params: dict[str, Any] = {}
        if symbol is not None:
            params["symbol"] = symbol

        # Returns a list (array) of open orders
        return await self.get(
            "/api/v3/openOrders",
            params=params,
            auth=True,
        )

    async def get_spot_all_orders(
        self: HttpClientProtocol,
        symbol: str,
        order_id: int | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """
        Get all account orders; active, canceled, or filled.

        API Docs:
            GET /api/v3/allOrders

        Weight: 20

        Data Source: Database

        Args:
            symbol: The symbol to get orders for. (MANDATORY)
            order_id: Get orders >= that orderId. If not provided,
                most recent orders are returned.
            start_time: Start time in milliseconds. If provided,
                order_id is not required.
            end_time: End time in milliseconds. If provided, order_id is not required.
            limit: Default 500; max 1000.

        Notes:
            - If orderId is set, it will get orders >= that orderId.
                Otherwise most recent orders are returned.
            - If startTime and/or endTime provided, orderId is not required.
            - The difference between startTime and endTime
                can't be longer than 24 hours.
            - For some historical orders, cummulativeQuoteQty will be < 0,
                meaning the data is not available at this time.

        Returns:
            dict: API JSON response containing all orders.
        """
        params: dict[str, Any] = {
            "symbol": symbol,
        }
        if order_id is not None:
            params["orderId"] = order_id
        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time
        if limit is not None:
            params["limit"] = limit

        return await self.get(
            "/api/v3/allOrders",
            params=params,
            auth=True,
        )
