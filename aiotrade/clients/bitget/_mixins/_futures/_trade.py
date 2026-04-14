from typing import Any, Literal

from aiotrade._protocols import HttpClientProtocol
from aiotrade.types.bitget import (
    BatchPlaceOrderItemParams,
    CancelOrderParams,
    PlaceOrderParams,
    ProductType,
)
from aiotrade.utils.formatters import to_str_fields


class TradeMixin:
    """Mixin for Bitget Futures Trade API endpoints."""

    async def place_futures_order(
        self: HttpClientProtocol,
        params: PlaceOrderParams,
    ) -> dict[str, Any]:
        """
        Place a futures order.

        Ignore tradeSide when in one-way position mode. In hedge-mode,
        tradeSide is required: open long (side=buy, tradeSide=open), etc.

        Rate limit: 10 requests/second/UID.

        API Docs:
            POST /api/v2/mix/order/place-order

        Args:
            params: Order parameters as PlaceOrderParams TypedDict.

        Returns:
            dict: API JSON response.
        """
        return await self.post(
            "/api/v2/mix/order/place-order",
            params=to_str_fields(
                params,
                {
                    "size",
                    "price",
                    "presetStopSurplusPrice",
                    "presetStopLossPrice",
                    "presetStopSurplusExecutePrice",
                    "presetStopLossExecutePrice",
                },
            ),
            auth=True,
        )

    async def batch_place_futures_orders(
        self: HttpClientProtocol,
        symbol: str,
        product_type: ProductType,
        margin_mode: Literal["isolated", "crossed"],
        margin_coin: str,
        order_list: list[BatchPlaceOrderItemParams],
    ) -> dict[str, Any]:
        """
        Place multiple orders in batch. Supports TP/SL. Max 50 orders per request.

        Ignore tradeSide when in one-way position mode.

        Rate limit: 5 req/s (1 req/s for copy trading).

        API Docs:
            POST /api/v2/mix/order/batch-place-order

        Args:
            symbol: Trading pair.
            product_type: Product type.
            margin_mode: "isolated" or "crossed".
            margin_coin: Margin coin (capitalized).
            order_list: List of BatchPlaceOrderItemParams. Each item: size, side,
                orderType (required); price, tradeSide, force, clientOid,
                reduceOnly, presetStopSurplusPrice, presetStopLossPrice,
                stpMode (optional).

        Returns:
            dict: API JSON response.
        """
        if len(order_list) > 50:
            raise ValueError("order_list max length is 50")

        body = {
            "symbol": symbol,
            "productType": product_type,
            "marginMode": margin_mode,
            "marginCoin": margin_coin,
            "orderList": to_str_fields(
                order_list,
                {"size", "price", "presetStopSurplusPrice", "presetStopLossPrice"},
            ),
        }
        return await self.post(
            "/api/v2/mix/order/batch-place-order",
            params=body,
            auth=True,
        )

    async def cancel_order(
        self: HttpClientProtocol,
        params: CancelOrderParams,
    ) -> dict[str, Any]:
        """
        Cancel a pending order. Either orderId or clientOid is required.

        Rate limit: 10 times/1s.

        API Docs:
            POST /api/v2/mix/order/cancel-order

        Args:
            params: Cancel parameters as CancelOrderParams TypedDict.

        Returns:
            dict: API JSON response.
        """
        if not params.get("orderId") and not params.get("clientOid"):
            raise ValueError("Either orderId or clientOid is required")
        return await self.post(
            "/api/v2/mix/order/cancel-order",
            params=params,
            auth=True,
        )

    async def batch_cancel_futures_orders(
        self: HttpClientProtocol,
        product_type: ProductType,
        *,
        order_id_list: list[dict[str, str]] | None = None,
        symbol: str | None = None,
        margin_coin: str | None = None,
    ) -> dict[str, Any]:
        """
        Cancel orders by product type and/or order IDs. Max 50 in orderIdList.

        When orderIdList is set, symbol is required.

        Rate limit: 10 times/s.

        API Docs:
            POST /api/v2/mix/order/batch-cancel-orders

        Args:
            product_type: Product type (required).
            order_id_list: List of {"orderId": "..."} or {"clientOid": "..."}.
            symbol: Trading pair (required when orderIdList is set).
            margin_coin: Margin coin (capitalized, optional).

        Returns:
            dict: API JSON response.
        """
        if order_id_list is not None and symbol is None:
            raise ValueError("symbol is required when order_id_list is set")
        if order_id_list is not None and len(order_id_list) > 50:
            raise ValueError("order_id_list max length is 50")
        body: dict[str, Any] = {"productType": product_type}
        if order_id_list is not None:
            body["orderIdList"] = order_id_list
        if symbol is not None:
            body["symbol"] = symbol
        if margin_coin is not None:
            body["marginCoin"] = margin_coin
        return await self.post(
            "/api/v2/mix/order/batch-cancel-orders",
            params=body,
            auth=True,
        )

    async def get_order_detail(
        self: HttpClientProtocol,
        symbol: str,
        product_type: ProductType,
        *,
        order_id: str | None = None,
        client_oid: str | None = None,
    ) -> dict[str, Any]:
        """
        Get order detail. Either orderId or clientOid is required.

        Rate limit: 10 times/1s.

        API Docs:
            GET /api/v2/mix/order/detail

        Args:
            symbol: Trading pair (capitalized).
            product_type: Product type.
            order_id: Order ID.
            client_oid: Custom order ID.

        Returns:
            dict: API JSON response.
        """
        if order_id is None and client_oid is None:
            raise ValueError("Either order_id or client_oid is required")
        params: dict[str, Any] = {
            "symbol": symbol,
            "productType": product_type,
        }
        if order_id is not None:
            params["orderId"] = order_id
        if client_oid is not None:
            params["clientOid"] = client_oid
        return await self.get(
            "/api/v2/mix/order/detail",
            params=params,
            auth=True,
        )

    async def get_pending_orders(
        self: HttpClientProtocol,
        product_type: ProductType,
        *,
        order_id: str | None = None,
        client_oid: str | None = None,
        symbol: str | None = None,
        status: Literal["live", "partially_filled"] | None = None,
        id_less_than: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """
        Query all pending orders.

        Rate limit: 10 req/sec/UID.

        API Docs:
            GET /api/v2/mix/order/orders-pending

        Args:
            product_type: Product type (required).
            order_id: Filter by order ID.
            client_oid: Filter by client order ID.
            symbol: Trading pair.
            status: "live" (pending) or "partially_filled".
            id_less_than: Pagination cursor (endId from previous response).
            start_time: Start timestamp (ms).
            end_time: End timestamp (ms). Max range 3 months.
            limit: Max 100, default 100.

        Returns:
            dict: API JSON response.
        """
        params: dict[str, Any] = {"productType": product_type}
        if order_id is not None:
            params["orderId"] = order_id
        if client_oid is not None:
            params["clientOid"] = client_oid
        if symbol is not None:
            params["symbol"] = symbol
        if status is not None:
            params["status"] = status
        if id_less_than is not None:
            params["idLessThan"] = id_less_than
        if start_time is not None:
            params["startTime"] = str(start_time)
        if end_time is not None:
            params["endTime"] = str(end_time)
        if limit is not None:
            params["limit"] = str(limit)
        return await self.get(
            "/api/v2/mix/order/orders-pending",
            params=params,
            auth=True,
        )

    async def get_futures_history_orders(
        self: HttpClientProtocol,
        product_type: ProductType,
        *,
        order_id: str | None = None,
        client_oid: str | None = None,
        symbol: str | None = None,
        id_less_than: str | None = None,
        order_source: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """
        Get order history (within 90 days).

        Rate limit: 10 req/sec/UID.

        API Docs:
            GET /api/v2/mix/order/orders-history

        Args:
            product_type: Product type (required).
            order_id: Filter by order ID.
            client_oid: Filter by client order ID.
            symbol: Trading pair.
            id_less_than: Pagination cursor.
            order_source: Order source (e.g. "normal", "market", "liquidation").
            start_time: Start timestamp (ms).
            end_time: End timestamp (ms).
            limit: Max 100, default 100.

        Returns:
            dict: API JSON response.
        """
        params: dict[str, Any] = {"productType": product_type}
        if order_id is not None:
            params["orderId"] = order_id
        if client_oid is not None:
            params["clientOid"] = client_oid
        if symbol is not None:
            params["symbol"] = symbol
        if id_less_than is not None:
            params["idLessThan"] = id_less_than
        if order_source is not None:
            params["orderSource"] = order_source
        if start_time is not None:
            params["startTime"] = str(start_time)
        if end_time is not None:
            params["endTime"] = str(end_time)
        if limit is not None:
            params["limit"] = str(limit)
        return await self.get(
            "/api/v2/mix/order/orders-history",
            params=params,
            auth=True,
        )

    async def cancel_all_futures_orders(
        self: HttpClientProtocol,
        product_type: ProductType,
        *,
        margin_coin: str | None = None,
        request_time: str | None = None,
        receive_window: str | None = None,
    ) -> dict[str, Any]:
        """
        Cancel all orders for the given product type.

        Rate limit: 10 req/sec/UID.

        API Docs:
            POST /api/v2/mix/order/cancel-all-orders

        Args:
            product_type: Product type (required).
            margin_coin: Margin coin (capitalized, optional).
            request_time: Request time Unix ms timestamp (optional).
            receive_window: Valid window period Unix ms (optional).

        Returns:
            dict: API JSON response.
        """
        body: dict[str, Any] = {"productType": product_type}
        if margin_coin is not None:
            body["marginCoin"] = margin_coin
        if request_time is not None:
            body["requestTime"] = request_time
        if receive_window is not None:
            body["receiveWindow"] = receive_window
        return await self.post(
            "/api/v2/mix/order/cancel-all-orders",
            params=body,
            auth=True,
        )
