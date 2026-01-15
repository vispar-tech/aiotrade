from typing import Any, Dict, Literal, Optional

from aiotrade._protocols import HttpClientProtocol


class TradeMixin:
    """Trading methods for BingX spot API client.

    This mixin provides methods for placing and managing trades
    in spot markets.
    """

    async def get_spot_order_history(
        self: HttpClientProtocol,
        symbol: Optional[str] = None,
        order_id: Optional[int] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        page_index: Optional[int] = None,
        page_size: Optional[int] = None,
        status: Optional[Literal["FILLED", "CANCELED", "FAILED"]] = None,
        order_type: Optional[
            Literal[
                "MARKET",
                "LIMIT",
                "TAKE_STOP_LIMIT",
                "TAKE_STOP_MARKET",
                "TRIGGER_LIMIT",
                "TRIGGER_MARKET",
            ]
        ] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve the order history for BingX spot trading.

        Endpoint:
            GET /openApi/spot/v1/trade/historyOrders

        Docs:
            https://bingx-api.github.io/docs-v3/#/en/Spot/Trades%20Endpoints/Query%20Order%20history

        Parameters:
            symbol (str, optional):
                Spot trading pair symbol, e.g. "BTC-USDT".
                If not provided, returns all symbols.
            order_id (int, optional):
                Returns all orders with orderId >= this value.
                If set, start/end time are ignored.
            start_time (int, optional):
                Start timestamp in ms. Used with end_time.
            end_time (int, optional):
                End timestamp in ms.
            page_index (int, optional):
                Page number (starts from 1). Default is 1.
            page_size (int, optional):
                Results per page. Max 100. Default is 100.
            status (str, optional):
                Filter order status: "FILLED", "CANCELED", "FAILED".
            order_type (str, optional):
                Filter order type:
                "MARKET", "LIMIT", "TAKE_STOP_LIMIT",
                "TAKE_STOP_MARKET", "TRIGGER_LIMIT",
                "TRIGGER_MARKET".

        Returns:
            Dict[str, Any]: API response with list of historical order records.

        Notes:
            - If order_id is set, takes precedence; ignores times.
            - With start_time/end_time, order_id not required.
            - page_index * page_size must not exceed 10,000.
        """
        params: Dict[str, Any] = {}

        if symbol is not None:
            params["symbol"] = symbol
        if order_id is not None:
            params["orderId"] = order_id
        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time
        if page_index is not None:
            params["pageIndex"] = page_index
        if page_size is not None:
            params["pageSize"] = page_size
        if status is not None:
            params["status"] = status
        if order_type is not None:
            params["type"] = order_type

        return await self.get(
            "/openApi/spot/v1/trade/historyOrders",
            params=params,
            auth=True,
        )

    async def get_spot_order_details(
        self: HttpClientProtocol,
        symbol: str,
        order_id: Optional[int] = None,
        client_order_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Query Order details for BingX spot trading.

        Endpoint:
            GET /openApi/spot/v1/trade/query

        Docs:
            https://bingx-api.github.io/docs-v3/#/en/Spot/Trades%20Endpoints/Query%20Order%20details

        Parameters:
            symbol (str, required):
                Trading pair, e.g., "BTC-USDT".
            order_id (int, optional):
                Order ID.
            client_order_id (str, optional):
                Custom user order ID (1~40 chars).
                    Only supports a query range of 2 hours.

        Returns:
            Dict[str, Any]: API response with details of the queried order.

        Notes:
            - Must provide either order_id or client_order_id.
            - Signature is required.
            - UID Rate Limit: 10/second.
            - Master and sub accounts supported.
        """
        params: Dict[str, Any] = {"symbol": symbol}
        if order_id is not None:
            params["orderId"] = order_id
        if client_order_id is not None:
            params["clientOrderID"] = client_order_id

        return await self.get(
            "/openApi/spot/v1/trade/query",
            params=params,
            auth=True,
        )

    async def get_spot_open_orders(
        self: HttpClientProtocol,
        symbol: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Query current open (pending) orders for BingX spot trading.

        Endpoint:
            GET /openApi/spot/v1/trade/openOrders

        Docs:
            https://bingx-api.github.io/docs-v3/#/en/Spot/Trades%20Endpoints/Current%20Open%20Orders

        Parameters:
            symbol (str, optional): Trading pair, e.g., "BTC-USDT".
                Query all pending orders when left blank.

        Returns:
            Dict[str, Any]: API response with the list of current open orders.

        Notes:
            - UID Rate Limit: 10/second.
            - Signature is required.
            - Master and sub accounts supported.
        """
        params: Dict[str, Any] = {}
        if symbol is not None:
            params["symbol"] = symbol

        return await self.get(
            "/openApi/spot/v1/trade/openOrders",
            params=params,
            auth=True,
        )

    async def cancel_spot_batch_orders(
        self: HttpClientProtocol,
        symbol: str,
        order_ids: Optional[list[str]] = None,
        client_order_ids: Optional[list[str]] = None,
        process: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Cancel multiple spot orders in a batch.

        Endpoint:
            POST /openApi/spot/v1/trade/cancelOrders

        Docs:
            https://bingx-api.github.io/docs-v3/#/en/Spot/Trades%20Endpoints/Cancel%20multiple%20orders

        Parameters:
            symbol: Trading pair (required)
            order_ids: List of order IDs (optional)
            client_order_ids: List of client order IDs (optional)
            process: 0 or 1 (optional)

        Returns:
            Dict[str, Any]: API response indicating cancellation results.

        Notes:
            - At least one of order_ids or client_order_ids must be provided.
            - UID Rate Limit: 2/second.
            - Signature is required.
            - Master and sub accounts supported.
        """
        if not order_ids and not client_order_ids:
            raise ValueError(
                "At least one of order_ids or client_order_ids must be provided."
            )

        params: Dict[str, Any] = {"symbol": symbol}
        if order_ids is not None:
            params["orderIds"] = ",".join(order_ids)
        if client_order_ids is not None:
            params["clientOrderIDs"] = ",".join(client_order_ids)
        if process is not None:
            params["process"] = process

        return await self.post(
            "/openApi/spot/v1/trade/cancelOrders",
            params=params,
            auth=True,
        )

    async def get_spot_trade_details(
        self: HttpClientProtocol,
        symbol: str,
        order_id: Optional[int] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        from_id: Optional[int] = None,
        limit: int = 500,
    ) -> Dict[str, Any]:
        """
        Query transaction (trade) details for BingX spot orders.

        Endpoint:
            GET /openApi/spot/v1/trade/myTrades

        Docs:
            https://bingx-api.github.io/docs-v3/#/en/Spot/Trades%20Endpoints/Query%20transaction%20details

        Parameters:
            symbol (str): Trading pair, e.g. "BTC-USDT" (required, UPPERCASE)
            order_id (int, optional): Order ID
            start_time (int, optional): Start timestamp in milliseconds
            end_time (int, optional): End timestamp in milliseconds
            from_id (int, optional): Starting trade ID;
                by default retrieves the latest trade
            limit (int, optional): Number of returned results (default 500, max 1000)

        Returns:
            Dict[str, Any]: API response with trade details.

        Notes:
            - Can only check data within the past 7 days.
            - If start_time/end_time not filled or invalid,
                 past 24 hours returned by default.
            - Max returns limited to 500 (default); maximum 1000 per request.
            - Returns a list sorted by 'time' field, from smallest to largest.
            - UID Rate Limit: 5/second.
            - Signature is required.
            - Master and sub accounts supported.
        """
        params: Dict[str, Any] = {"symbol": symbol, "limit": limit}
        if order_id is not None:
            params["orderId"] = order_id
        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time
        if from_id is not None:
            params["fromId"] = from_id

        return await self.get(
            "/openApi/spot/v1/trade/myTrades",
            params=params,
            auth=True,
        )

    async def cancel_all_spot_open_orders(
        self: HttpClientProtocol,
        symbol: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Cancel all open spot orders on a symbol (or all symbols if not specified).

        Endpoint:
            POST /openApi/spot/v1/trade/cancelOpenOrders

        Docs:
            https://bingx-api.github.io/docs-v3/#/en/Spot/Trades%20Endpoints/Cancel%20all%20Open%20Orders%20on%20a%20Symbol

        Parameters:
            symbol (str, optional): Trading pair, e.g., "BTC-USDT".
                If not filled, cancel all orders.

        Returns:
            Dict[str, Any]: API response.

        Notes:
            - UID Rate Limit: 2/second.
            - Signature is required.
            - Applicable to Master and Sub Accounts.
        """
        params: Dict[str, Any] = {}
        if symbol is not None:
            params["symbol"] = symbol

        return await self.post(
            "/openApi/spot/v1/trade/cancelOpenOrders",
            params=params,
            auth=True,
        )
