from typing import Any, Literal

from aiotrade._protocols import HttpClientProtocol
from aiotrade.clients.kucoin._consts import base_url
from aiotrade.types.kucoin import (
    BatchCancelOrdersPayload,
    PlaceOrderParams,
    TakeProfitStopLossOrderParams,
)
from aiotrade.utils import to_str_fields


class OrdersMixin:
    async def add_order(
        self: HttpClientProtocol,
        params: PlaceOrderParams,
    ) -> dict[str, Any]:
        """
        Place order in the futures trading system (Limit or Market).

        Args:
            params (PlaceOrderParams): See Kucoin Futures API Place Order parameters.

        Returns:
            dict[str, Any]: Example response:
                {
                  "code": "200000",
                  "data": {
                    "orderId": "234125150956625920",
                    "clientOid": "5c52e11203aa677f33e493fb"
                  }
                }
        """
        return await self.post(
            "/api/v1/orders",
            params=params,
            auth=True,
            base_url=base_url("futures"),
        )

    async def add_order_test(
        self: HttpClientProtocol,
        params: PlaceOrderParams,
    ) -> dict[str, Any]:
        """
        Place test order in the futures trading system.

        Same parameters and return structure as `add_order`, but does not actually enter
        the matching system (for dry-run/validation/testing).

        Args:
            params (PlaceOrderParams): See Kucoin Futures API Place Order parameters.

        Returns:
            dict[str, Any]: Example response:
                {
                  "code": "200000",
                  "data": {
                    "orderId": "234125150956625920",
                    "clientOid": "5c52e11203aa677f33e493fb"
                  }
                }
        """
        return await self.post(
            "/api/v1/orders/test",
            params=params,
            auth=True,
            base_url=base_url("futures"),
        )

    async def batch_add_orders(
        self: HttpClientProtocol,
        orders: list[PlaceOrderParams],
    ) -> dict[str, Any]:
        """
        Place multiple orders in the futures trading system.

        You can place up to 20 orders per request, including limit, market,
        and stop orders. Please refer to the KuCoin Futures API
        documentation for detailed parameter definitions and order limits.

        Args:
            orders (list[PlaceOrderParams]): List of order parameter dicts (max 20).

        Returns:
            dict[str, Any]: Example response:
                {
                  "code": "200000",
                  "data": [
                    {
                      "orderId": "235919387779985408",
                      "clientOid": "5c52e11203aa677f33e493fb",
                      "symbol": "XBTUSDTM",
                      "code": "200000",
                      "msg": "success"
                    },
                    {
                      "orderId": "235919387855482880",
                      "clientOid": "5c52e11203aa677f33e493fc",
                      "symbol": "XBTUSDTM",
                      "code": "200000",
                      "msg": "success"
                    }
                  ]
                }
        """
        params = to_str_fields(
            orders,
            {
                "stopPrice",
                "price",
                "qty",
                "valueQty",
                "visibleSize",
                "triggerStopUpPrice",
                "triggerStopDownPrice",
            },
        )

        return await self.post(
            "/api/v1/orders/multi",
            params=params,
            auth=True,
            base_url=base_url("futures"),
        )

    async def add_tp_sl_order(
        self: HttpClientProtocol,
        params: TakeProfitStopLossOrderParams,
    ) -> dict[str, Any]:
        """
        Add Take Profit And Stop Loss Order.

        Place take profit and stop loss order supports both take-profit and stop-loss
        functions, and other functions are exactly the same
        as the place order interface.

        Args:
            params (TakeProfitStopLossOrderParams): See Kucoin Futures
                API Add Take Profit and Stop Loss Order parameters.

        Returns:
            dict[str, Any]: Example response:
                {
                  "code": "200000",
                  "data": {
                    "orderId": "234125150956625920",
                    "clientOid": "5c52e11203aa677f33e493fb"
                  }
                }
        """
        return await self.post(
            "/api/v1/st-orders",
            params=to_str_fields(
                params,
                {
                    "stopPrice",
                    "price",
                    "qty",
                    "valueQty",
                    "visibleSize",
                    "triggerStopUpPrice",
                    "triggerStopDownPrice",
                },
            ),
            auth=True,
            base_url=base_url("futures"),
        )

    async def cancel_order_by_id(
        self: HttpClientProtocol,
        order_id: str,
    ) -> dict[str, Any]:
        """
        Cancel Order By OrderId (Futures).

        Cancel an order (including a stop order) by server-assigned orderId.

        You will receive a success message once the system has received the cancellation
        request. To know if the cancellation has been processed, check the order status
        or listen to websocket updates. If the order cannot be cancelled (already filled
        or previously cancelled), an error message will indicate the reason.

        Args:
            order_id (str): The server-assigned orderId to be cancelled.

        Returns:
            dict[str, Any]: Example response:
                {
                  "code": "200000",
                  "data": {
                    "cancelledOrderIds": ["235303670076489728"]
                  }
                }
        """
        return await self.delete(
            f"/api/v1/orders/{order_id}",
            auth=True,
            base_url=base_url("futures"),
        )

    async def cancel_order_by_client_oid(
        self: HttpClientProtocol,
        client_oid: str,
        symbol: str,
    ) -> dict[str, Any]:
        """
        Cancel Order By ClientOid (Futures).

        Cancel an order (including a stop order) by client-defined clientOid.

        You will receive a success message once the system has received the cancellation
        request. To know if the cancellation has been processed, check the order status
        or listen to websocket updates. If the order cannot be cancelled (already filled
        or previously cancelled), an error message will indicate the reason.

        Args:
            client_oid (str): The client-defined clientOid for the order.
            symbol (str): The symbol of the contract (e.g. "XBTUSDTM").

        Returns:
            dict[str, Any]: Example response:
                {
                  "code": "200000",
                  "data": {
                    "clientOid": "017485b0-2957-4681-8a14-5d46b35aee0d"
                  }
                }
        """
        return await self.delete(
            f"/api/v1/orders/client-order/{client_oid}",
            params={"symbol": symbol},
            auth=True,
            base_url=base_url("futures"),
        )

    async def batch_cancel_orders(
        self: HttpClientProtocol,
        payload: BatchCancelOrdersPayload,
    ) -> dict[str, Any]:
        """
        Batch Cancel Orders (Futures).

        Cancel orders in batches, by a list of order IDs (orderIdsList) or by a list of
        client OIDs with symbol (clientOidsList). If both are provided, orderIdsList
        takes precedence and clientOidsList is ignored.

        A maximum of 10 orders can be cancelled per request.

        Args:
            payload (BatchCancelOrdersPayload): Batch cancel request body.
        """
        return await self.delete(
            "/api/v1/orders/multi-cancel",
            params=payload,
            auth=True,
            base_url=base_url("futures"),
        )

    async def cancel_all_orders(
        self: HttpClientProtocol,
        symbol: str,
    ) -> dict[str, Any]:
        """
        Cancel All Orders (Futures).

        Cancel all open orders (excluding stop orders) for the specified
        symbol in batches.

        Args:
            symbol (str): The symbol of the contract to cancel orders
                for (e.g. "XBTUSDTM").
        """
        return await self.delete(
            "/api/v3/orders",
            params={"symbol": symbol},
            auth=True,
            base_url=base_url("futures"),
        )

    async def cancel_all_stop_orders(
        self: HttpClientProtocol,
        symbol: str | None = None,
    ) -> dict[str, Any]:
        """
        Cancel All Stop Orders (Futures).

        Cancel all untriggered stop orders in batches. If a symbol is specified, only
        untriggered stop orders for that symbol are canceled. If not specified,
        all untriggered stop orders will be canceled.

        Args:
            symbol (str, optional): The symbol of the contract (e.g. "XBTUSDTM").
                If None, cancels all untriggered stop orders.
        """
        params: dict[str, str] = {}
        if symbol is not None:
            params["symbol"] = symbol
        return await self.delete(
            "/api/v1/stopOrders",
            params=params,
            auth=True,
            base_url=base_url("futures"),
        )

    async def get_order_by_order_id(
        self: HttpClientProtocol,
        order_id: str,
    ) -> dict[str, Any]:
        """
        Get Order By OrderId (Futures).

        Get a single order by order id (including a stop order).

        Note:
            Historical orders can only be queried within a limited time window
            by status. For classic futures account, cancelled/filled orders can
            only be queried for last 3 months. If the time range is exceeded,
            system will limit to the maximum window.

        Args:
            order_id (str): The ID of the order to retrieve.
        """
        return await self.get(
            f"/api/v1/orders/{order_id}",
            auth=True,
            base_url=base_url("futures"),
        )

    async def get_order_by_client_oid(
        self: HttpClientProtocol,
        client_oid: str,
    ) -> dict[str, Any]:
        """
        Get Order By ClientOid (Futures).

        Get a single order by client order ID (including a stop order).

        Note:
            Historical orders can only be queried within a limited time window by
            status. For classic futures accounts, cancelled or filled orders can
            only be queried for the last 7 days. If the time range is exceeded,
            the system will limit queries to the allowed window.

        Args:
            client_oid (str): The user-defined order ID.
        """
        return await self.get(
            "/api/v1/orders/byClientOid",
            params={"clientOid": client_oid},
            auth=True,
            base_url=base_url("futures"),
        )

    async def get_order_list(
        self: HttpClientProtocol,
        status: Literal["active", "done"] | None = None,
        symbol: str | None = None,
        side: Literal["buy", "sell"] | None = None,
        type: Literal[
            "limit",
            "market",
            "limit_stop",
            "market_stop",
            "oco_limit",
            "oco_stop",
        ]
        | None = None,
        start_at: int | None = None,
        end_at: int | None = None,
        current_page: int | None = None,
        page_size: int | None = None,
    ) -> dict[str, Any]:
        """
        Get Order List (Futures).

        List your current orders. By default, returns orders with "done" status.
        You can filter by status, symbol, side, type, time range, and paginate results.

        Args:
            status (Literal["active", "done"], optional): The status to
                filter orders by.
            symbol (str, optional): The contract symbol (e.g., "XBTUSDTM").
            side (Literal["buy", "sell"], optional): "buy" or "sell".
            type (Literal["limit", "market", "limit_stop", "market_stop", "oco_limit",
                "oco_stop"], optional): Order type.
            start_at (int, optional): Start time (ms since epoch).
            end_at (int, optional): End time (ms since epoch).
            current_page (int, optional): Page number to fetch (default 1).
            page_size (int, optional): Number of results per page
                (default 50, max 1000).

        Returns:
            dict[str, Any]: KuCoin API response containing a paginated list of orders.
        """
        params: dict[str, Any] = {}
        if status is not None:
            params["status"] = status
        if symbol is not None:
            params["symbol"] = symbol
        if side is not None:
            params["side"] = side
        if type is not None:
            params["type"] = type
        if start_at is not None:
            params["startAt"] = start_at
        if end_at is not None:
            params["endAt"] = end_at
        if current_page is not None:
            params["currentPage"] = current_page
        if page_size is not None:
            params["pageSize"] = page_size

        return await self.get(
            "/api/v1/orders",
            params=params,
            auth=True,
            base_url=base_url("futures"),
        )

    async def get_recent_closed_orders(
        self: HttpClientProtocol,
        symbol: str | None = None,
    ) -> dict[str, Any]:
        """
        Get Recent Closed Orders (Futures).

        Get a list of recent 1000 closed orders in the last 24 hours. If you need to get
        your recent traded order history with low latency, you may query this endpoint.

        Args:
            symbol (str, optional): The contract symbol (e.g., "XBTUSDTM").

        Returns:
            dict[str, Any]: KuCoin API response containing
                a list of recently closed orders.
        """
        params: dict[str, Any] = {}
        if symbol is not None:
            params["symbol"] = symbol
        return await self.get(
            "/api/v1/recentDoneOrders",
            params=params,
            auth=True,
            base_url=base_url("futures"),
        )

    async def get_stop_orders(
        self: HttpClientProtocol,
        *,
        symbol: str | None = None,
        side: Literal["buy", "sell"] | None = None,
        order_type: Literal["limit", "market"] | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        page: int | None = None,
        page_size: int | None = None,
    ) -> dict[str, Any]:
        """
        Get Stop Order List (Futures).

        Retrieves the list of un-triggered stop orders. To view triggered stop orders,
        use the general order interface.

        Args:
            symbol (str, optional): Contract symbol (e.g. "XBTUSDTM").
            side (Literal["buy", "sell"], optional): buy or sell.
            order_type (Literal["limit", "market"], optional): limit or market.
            start_time (int, optional): Start time (ms since epoch).
            end_time (int, optional): End time (ms since epoch).
            page (int, optional): Page number (default: 1).
            page_size (int, optional): Number of results per page
                (default: 50, max: 1000).

        Returns:
            dict[str, Any]: KuCoin API paginated stop order list response.

        Example:
            {
              "code": "200000",
              "data": {
                "currentPage": 1,
                "pageSize": 50,
                "totalNum": 1,
                "totalPage": 1,
                "items": [
                  {
                    "id": "230181737576050688",
                    "symbol": "PEOPLEUSDTM",
                    "type": "limit",
                    "side": "buy",
                    "price": "0.05",
                    ...
                  }
                ]
              }
            }
        """
        params: dict[str, Any] = {}
        if symbol is not None:
            params["symbol"] = symbol
        if side is not None:
            params["side"] = side
        if order_type is not None:
            params["type"] = order_type
        if start_time is not None:
            params["startAt"] = start_time
        if end_time is not None:
            params["endAt"] = end_time
        if page is not None:
            params["currentPage"] = page
        if page_size is not None:
            params["pageSize"] = page_size

        return await self.get(
            "/api/v1/stopOrders",
            params=params,
            auth=True,
            base_url=base_url("futures"),
        )

    async def get_recent_trade_history(
        self: HttpClientProtocol,
        symbol: str | None = None,
    ) -> dict[str, Any]:
        """
        Get Recent Trade History (Futures).

        Get a list of recent 1000 fills in the last 24 hours. If you need to get your
        recently traded order history with low latency, you may query this endpoint.

        Args:
            symbol (str, optional): Contract symbol (e.g. "XBTUSDTM").

        Returns:
            dict[str, Any]: KuCoin API response.
        """
        params: dict[str, Any] = {}
        if symbol is not None:
            params["symbol"] = symbol

        return await self.get(
            "/api/v1/recentFills",
            params=params,
            auth=True,
            base_url=base_url("futures"),
        )

    async def get_trade_history(
        self: HttpClientProtocol,
        *,
        order_id: str | None = None,
        symbol: str | None = None,
        side: Literal["buy", "sell"] | None = None,
        type: Literal["limit", "market", "limit_stop", "market_stop"] | None = None,
        trade_types: str | None = None,
        start_at: int | None = None,
        end_at: int | None = None,
        current_page: int | None = None,
        page_size: int | None = None,
    ) -> dict[str, Any]:
        """
        Get Trade History (Fills) (Futures).

        Get a list of recent fills. For real-time fills, use get_recent_trade_history().

        Args:
            order_id (str, optional): List fills for a specific order only.
            symbol (str, optional): Contract symbol (e.g. "XBTUSDTM").
            side (Literal["buy", "sell"], optional): Order side.
            type (Literal["limit", "market", "limit_stop", "market_stop"], optional):
                Order type.
            trade_types (str, optional): Transaction type(s), comma-separated
                ("trade,adl,liquid,settlement").
            start_at (int, optional): Start time (milliseconds).
            end_at (int, optional): End time (milliseconds).
            current_page (int, optional): Current request page, default 1.
            page_size (int, optional): Number of results per page
                (default 50, max 1000).

        Returns:
            dict[str, Any]: KuCoin API paginated trade (fills) history response.
        """
        params: dict[str, Any] = {}
        if order_id is not None:
            params["orderId"] = order_id
        if symbol is not None:
            params["symbol"] = symbol
        if side is not None:
            params["side"] = side
        if type is not None:
            params["type"] = type
        if trade_types is not None:
            params["tradeTypes"] = trade_types
        if start_at is not None:
            params["startAt"] = start_at
        if end_at is not None:
            params["endAt"] = end_at
        if current_page is not None:
            params["currentPage"] = current_page
        if page_size is not None:
            params["pageSize"] = page_size

        return await self.get(
            "/api/v1/fills",
            params=params,
            auth=True,
            base_url=base_url("futures"),
        )
