from typing import Any, Dict, List, Literal

from aiotrade._protocols import HttpClientProtocol
from aiotrade.types.bybit import (
    CancelOrderParams,
    GetOrderHistoryParams,
    PlaceOrderParams,
)


class TradeMixin:
    """Mixin for trade endpoints."""

    async def place_order(
        self: HttpClientProtocol,
        category: Literal["linear", "inverse", "spot", "option"],
        params: PlaceOrderParams,
    ) -> Dict[str, Any]:
        """
        Place an order from Bybit API.

        Only uses fields defined in PlaceOrderParams.

        Args:
            category: Product type (linear, inverse, spot, option)
            params: Order parameters as PlaceOrderParams TypedDict

        Returns:
            Dict with order creation response containing orderId and orderLinkId.
        """
        api_params: Dict[str, Any] = {"category": category}
        fields_to_str = {"qty", "price", "trigger_price", "take_profit", "stop_loss"}
        field_mapping = {
            "symbol": "symbol",
            "is_leverage": "isLeverage",
            "side": "side",
            "order_type": "orderType",
            "qty": "qty",
            "market_unit": "marketUnit",
            "price": "price",
            "trigger_price": "triggerPrice",
            "trigger_by": "triggerBy",
            "time_in_force": "timeInForce",
            "position_idx": "positionIdx",
            "order_link_id": "orderLinkId",
            "take_profit": "takeProfit",
            "stop_loss": "stopLoss",
            "tp_trigger_by": "tpTriggerBy",
            "sl_trigger_by": "slTriggerBy",
            "reduce_only": "reduceOnly",
            "tpsl_mode": "tpslMode",
            "tp_limit_price": "tpLimitPrice",
            "sl_limit_price": "slLimitPrice",
            "tp_order_type": "tpOrderType",
            "sl_order_type": "slOrderType",
        }
        for typed_key, api_key in field_mapping.items():
            v = params.get(typed_key)
            if v is not None:
                if typed_key in fields_to_str:
                    v = str(v)
                api_params[api_key] = v
        return await self.post("/v5/order/create", params=api_params, auth=True)

    async def amend_order(self: HttpClientProtocol) -> None:
        """Amend an existing order."""
        raise NotImplementedError

    async def cancel_order(
        self: "HttpClientProtocol",
        category: Literal["linear", "inverse", "spot", "option"],
        symbol: str,
        order_id: str | None = None,
        order_link_id: str | None = None,
        order_filter: Literal["Order", "tpslOrder", "StopOrder"] | None = None,
    ) -> Dict[str, Any]:
        """
        Cancel a single order.

        See:
            https://bybit-exchange.github.io/docs/v5/order/cancel-order

        Args:
            category (str): Product type (linear, inverse, spot, option).
                REQUIRED.
            symbol (str): Symbol name, like BTCUSDT, uppercase only.
                REQUIRED.
            order_id (str, optional): Order ID. Either order_id or
                order_link_id is REQUIRED.
            order_link_id (str, optional): User customized order ID.
                Either order_id or order_link_id is REQUIRED.
            order_filter (str, optional): Spot trading only. "Order",
                "tpslOrder", "StopOrder". Default is "Order" if not passed.

        Returns:
            Dict with order cancellation response.
        """
        api_params = {
            "category": category,
            "symbol": symbol,
        }
        if order_id is not None:
            api_params["orderId"] = order_id
        if order_link_id is not None:
            api_params["orderLinkId"] = order_link_id
        if order_filter is not None:
            api_params["orderFilter"] = order_filter

        # Must provide at least order_id or order_link_id
        if not (order_id or order_link_id):
            raise ValueError("Either order_id or order_link_id must be provided.")

        return await self.post("/v5/order/cancel", params=api_params, auth=True)

    async def get_open_and_closed_orders(
        self: HttpClientProtocol,
        category: Literal["linear", "inverse", "spot", "option"],
        symbol: str | None = None,
        base_coin: str | None = None,
        settle_coin: str | None = None,
        order_id: str | None = None,
        order_link_id: str | None = None,
        open_only: Literal[0, 1] | None = None,
        order_filter: Literal[
            "Order", "StopOrder", "tpslOrder", "OcoOrder", "BidirectionalTpslOrder"
        ]
        | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> Dict[str, Any]:
        """
        Get open and closed orders from Bybit API.

        Primarily query unfilled or partially filled orders in real-time,
        but also supports querying recent 500 closed status (Cancelled, Filled) orders.

        See:
            https://bybit-exchange.github.io/docs/v5/order/open-order

        Args:
            category: Product type (linear, inverse, spot, option)
            params: Query parameters as GetOrdersParams TypedDict

        Returns:
            Dict with orders response containing list of orders.

        Raises:
            Any exception raised by the underlying HTTP request.
        """
        api_params: Dict[str, str | int] = {"category": category}
        if symbol is not None:
            api_params["symbol"] = symbol
        if base_coin is not None:
            api_params["baseCoin"] = base_coin
        if settle_coin is not None:
            api_params["settleCoin"] = settle_coin
        if order_id is not None:
            api_params["orderId"] = order_id
        if order_link_id is not None:
            api_params["orderLinkId"] = order_link_id
        if open_only is not None:
            api_params["openOnly"] = open_only
        if order_filter is not None:
            api_params["orderFilter"] = order_filter
        if limit is not None:
            api_params["limit"] = limit
        if cursor is not None:
            api_params["cursor"] = cursor

        return await self.get(
            "/v5/order/realtime",
            params=api_params,
            auth=True,
        )

    async def cancel_all_orders(
        self: HttpClientProtocol,
        category: Literal["linear", "inverse", "spot", "option"],
        symbol: str | None = None,
        base_coin: str | None = None,
        settle_coin: Literal["USDT", "USDC"] | None = None,
        order_filter: Literal[
            "Order",
            "tpslOrder",
            "StopOrder",
            "OcoOrder",
            "BidirectionalTpslOrder",
            "OpenOrder",
        ]
        | None = None,
        stop_order_type: Literal["Stop"] | None = None,
    ) -> Dict[str, Any]:
        """
        Cancel all active orders for the given category and optional filters.

        Args:
            category: Product type. One of "linear", "inverse", "spot", "option".
            symbol: Symbol name (e.g. "BTCUSDT"), uppercase only.
                linear/inverse: Required if not passing base_coin or
                settle_coin.
            base_coin: Base coin, uppercase only.
                linear/inverse: If cancel all by baseCoin, cancels all of
                the corresponding category's orders. Required if not
                passing symbol or settle_coin.
            settle_coin: Settle coin, uppercase only.
                linear/inverse: Required if not passing symbol or
                base_coin. option: "USDT" or "USDC". Not supported for
                spot.
            order_filter: For spot: Order, tpslOrder, StopOrder,
                OcoOrder, BidirectionalTpslOrder (default Order). For
                linear/inverse: Order, StopOrder, OpenOrder (default:
                all kinds). For option: Order, StopOrder (default: all
                kinds).
            stop_order_type: Stop order type "Stop". Only for
                category=linear or inverse and order_filter=StopOrder
                (cancels conditional orders except TP/SL and trailing
                stops).

        Returns:
            Dict[str, Any]: API response from cancelling all active orders.

        Raises:
            ValueError: If required parameters are missing.
            Exception: Any exception raised by the underlying HTTP request.
        """
        api_params: Dict[str, str] = {"category": category}

        # Validations for requirements
        if category in ("linear", "inverse") and not (
            symbol or base_coin or settle_coin
        ):
            raise ValueError(
                "For linear/inverse, provide symbol or base_coin or settle_coin."
            )
        if category == "option" and not (symbol or base_coin or settle_coin):
            raise ValueError("For option, provide symbol or base_coin or settle_coin.")

        if symbol is not None:
            api_params["symbol"] = symbol
        if base_coin is not None:
            api_params["baseCoin"] = base_coin
        if settle_coin is not None:
            api_params["settleCoin"] = settle_coin
        if order_filter is not None:
            api_params["orderFilter"] = order_filter
        if stop_order_type is not None:
            api_params["stopOrderType"] = stop_order_type

        return await self.post(
            "/v5/order/cancel-all",
            params=api_params,
            auth=True,
        )

    async def get_order_history(
        self: HttpClientProtocol,
        category: Literal["linear", "inverse", "spot", "option"],
        params: GetOrderHistoryParams | None = None,
    ) -> Dict[str, Any]:
        """
        Get order history from Bybit API.

        Query order history. As order creation/cancellation is asynchronous,
        the data returned from this endpoint may be delayed.

        The orders in the last 7 days: support querying all closed status
        except "Cancelled", "Rejected", "Deactivated" status.
        The orders in the last 24 hours: orders with "Cancelled", "Rejected",
        "Deactivated" can be queried.
        The orders beyond 7 days: supports querying orders which have fills only.

        See:
            https://bybit-exchange.github.io/docs/v5/order/order-list

        Args:
            category: Product type (linear, inverse, spot, option)
            params: Query parameters as GetOrderHistoryParams TypedDict

        Returns:
            Dict with order history response containing list of orders.

        Raises:
            Any exception raised by the underlying HTTP request.
        """
        api_params: Dict[str, Any] = {"category": category}

        if params:
            # Map TypedDict fields to API parameter names
            field_mapping = {
                "symbol": "symbol",
                "base_coin": "baseCoin",
                "settle_coin": "settleCoin",
                "order_id": "orderId",
                "order_link_id": "orderLinkId",
                "order_filter": "orderFilter",
                "order_status": "orderStatus",
                "start_time": "startTime",
                "end_time": "endTime",
                "limit": "limit",
                "cursor": "cursor",
            }

            # Add non-None parameters
            for field_name, api_name in field_mapping.items():
                value = params.get(field_name)
                if value is not None:
                    api_params[api_name] = value

        return await self.get(
            "/v5/order/history",
            params=api_params,
            auth=True,
        )

    async def get_trade_history(self: HttpClientProtocol) -> None:
        """Get trade history (up to 2 years)."""
        raise NotImplementedError

    async def batch_place_order(
        self: HttpClientProtocol,
        category: str,
        orders: List[PlaceOrderParams],
    ) -> Dict[str, Any]:
        """
        Batch place multiple orders.

        See:
            https://bybit-exchange.github.io/docs/v5/order/batch-place

        Args:
            category: Product type ("linear", "option", "spot", "inverse").
            orders: List of PlaceOrderParams dicts, each containing order parameters.

        Returns:
            Dict with API response from batch order placement.

        Raises:
            Any exception raised by the underlying HTTP request.
        """
        field_mapping = {
            "symbol": "symbol",
            "is_leverage": "isLeverage",
            "side": "side",
            "order_type": "orderType",
            "qty": "qty",
            "market_unit": "marketUnit",
            "price": "price",
            "trigger_price": "triggerPrice",
            "trigger_by": "triggerBy",
            "time_in_force": "timeInForce",
            "position_idx": "positionIdx",
            "order_link_id": "orderLinkId",
            "take_profit": "takeProfit",
            "stop_loss": "stopLoss",
            "tp_trigger_by": "tpTriggerBy",
            "sl_trigger_by": "slTriggerBy",
            "reduce_only": "reduceOnly",
            "tpsl_mode": "tpslMode",
            "tp_limit_price": "tpLimitPrice",
            "sl_limit_price": "slLimitPrice",
            "tp_order_type": "tpOrderType",
            "sl_order_type": "slOrderType",
        }

        # Fields needing string conversion
        fields_to_str = {"qty", "price", "trigger_price", "take_profit", "stop_loss"}

        api_orders: List[Dict[str, Any]] = []
        for order in orders:
            api_order: Dict[str, Any] = {}
            for typed_key, api_key in field_mapping.items():
                value = order.get(typed_key)
                if value is not None:
                    if typed_key in fields_to_str:
                        value = str(value)
                    api_order[api_key] = value
            api_orders.append(api_order)

        data = {
            "category": category,
            "request": api_orders,
        }
        return await self.post(
            "/v5/order/create-batch",
            params=data,
            auth=True,
        )

    async def batch_amend_order(self: HttpClientProtocol) -> None:
        """Batch amend multiple orders."""
        raise NotImplementedError

    async def batch_cancel_order(
        self: HttpClientProtocol,
        category: Literal["linear", "option", "spot", "inverse"],
        orders: List[CancelOrderParams],
    ) -> Dict[str, Any]:
        """
        Batch cancel multiple orders from Bybit API.

        This endpoint allows you to cancel more than one open order in a single request.
        You can cancel unfilled or partially filled orders.

        Limits:
        - A maximum of 20 orders (option), 20 orders (inverse), 20 orders (linear),
          10 orders (spot) can be cancelled per request.
        - You must specify orderId or orderLinkId for each order.

        See:
            https://bybit-exchange.github.io/docs/v5/order/batch-cancel

        Args:
            category: Product type (linear, option, spot, inverse)
            orders: List of CancelOrderParams, each containing symbol and
                   either orderId or orderLinkId

        Returns:
            Dict with batch cancel response containing list of cancelled orders
            and retExtInfo with success/error codes for each order.

        Raises:
            Any exception raised by the underlying HTTP request.
        """
        # Validate that each order has either orderId or orderLinkId
        for i, order in enumerate(orders):
            if not (order.get("order_id") or order.get("order_link_id")):
                raise ValueError(
                    f"Order at index {i} must have either 'order_id' or 'order_link_id'"
                )

        # Convert CancelOrderParams to API format
        request_data: List[Dict[str, str]] = []
        for order in orders:
            order_dict = {"symbol": order["symbol"]}
            order_id = order.get("order_id")
            if order_id is not None:
                order_dict["orderId"] = order_id
            order_link_id = order.get("order_link_id")
            if order_link_id is not None:
                order_dict["orderLinkId"] = order_link_id

            request_data.append(order_dict)

        params: Dict[str, str | List[Dict[str, str]]] = {
            "category": category,
            "request": request_data,
        }

        return await self.post(
            "/v5/order/cancel-batch",
            params=params,
            auth=True,
        )

    async def get_borrow_quota_spot(self: HttpClientProtocol) -> None:
        """Get borrow quota for spot trading."""
        raise NotImplementedError

    async def set_dcp(self: HttpClientProtocol) -> None:
        """Set DCP (Dynamic Contract Parameters)."""
        raise NotImplementedError

    async def pre_check_order(self: HttpClientProtocol) -> None:
        """Pre-check order before placement."""
        raise NotImplementedError
