from collections.abc import Iterable
from typing import Any, Literal

from aiotrade._protocols import HttpClientProtocol
from aiotrade.types.okx import CancelOrderParams, PlaceOrderParams
from aiotrade.utils.formatters import join_iterable_field, to_str_fields


class TradeMixin:
    async def close_position(
        self: HttpClientProtocol,
        inst_id: str,
        mgn_mode: Literal["cross", "isolated"],
        pos_side: Literal["long", "short", "net"] | None = None,
        ccy: str | None = None,
        auto_cxl: bool | None = None,
        cl_ord_id: str | None = None,
        tag: str | None = None,
    ) -> dict[str, Any]:
        """
        Close the position of an instrument using a market order.

        Rate Limit: 20 requests per 2 seconds.

        See:
            https://www.okx.com/docs-v5/en/#order-book-trading-trade-post-close-positions

        Args:
            inst_id: Instrument ID, e.g., "BTC-USDT-SWAP".
            mgn_mode: Margin mode, either "cross" or "isolated".
            pos_side: Position side. Optional in net mode (default "net").
                Must be provided in long/short mode ("long" or "short").
            ccy: Margin currency. Required for closing cross
                MARGIN position for Futures.
            auto_cxl: Whether to automatically cancel any pending
                orders that would close this position (default: False).
            cl_ord_id: Client-supplied ID (up to 32 characters).
            tag: Order tag (up to 16 characters).

        Returns:
            Dict containing the result of the close position request.
        """
        params: dict[str, Any] = {
            "instId": inst_id,
            "mgnMode": mgn_mode,
        }
        if pos_side is not None:
            params["posSide"] = pos_side
        if ccy is not None:
            params["ccy"] = ccy
        if auto_cxl is not None:
            params["autoCxl"] = auto_cxl
        if cl_ord_id is not None:
            params["clOrdId"] = cl_ord_id
        if tag is not None:
            params["tag"] = tag

        return await self.post(
            "/api/v5/trade/close-position",
            params=params,
            auth=True,
        )

    async def batch_place_order(
        self: HttpClientProtocol,
        orders: list[PlaceOrderParams],
    ) -> dict[str, Any]:
        """
        Place multiple orders in a single batch request.

        You can place up to 20 orders per request.
        Rate Limit: 300 orders per 2 seconds.

        See:
            https://www.okx.com/docs-v5/en/#order-book-trading-trade-post-place-multiple-orders

        Args:
            orders: List of orders to place (max 20 per request)

        Returns:
            Dict containing the result of the batch place order request.
        """
        if len(orders) == 0:
            raise ValueError("orders list must not be empty")
        if len(orders) > 20:
            raise ValueError("Cannot place more than 20 orders per batch")

        def _convert_order_fields(order: PlaceOrderParams) -> dict[str, Any]:
            converted = to_str_fields(order, {"sz", "px", "pxUsd", "pxVol"})
            converted["attachAlgoOrds"] = [
                to_str_fields(
                    algo,
                    {
                        "tpTriggerPx",
                        "tpTriggerRatio",
                        "tpOrdPx",
                        "slTriggerPx",
                        "slTriggerRatio",
                        "slOrdPx",
                        "sz",
                        "px",
                        "pxUsd",
                        "pxVol",
                    },
                )
                for algo in converted.get("attachAlgoOrds", [])
            ]
            return converted

        payload = [_convert_order_fields(order) for order in orders]

        return await self.post(
            "/api/v5/trade/batch-orders",
            params=payload,
            auth=True,
        )

    async def cancel_batch_orders(
        self: HttpClientProtocol,
        orders: list[CancelOrderParams],
    ) -> dict[str, Any]:
        """
        Cancel incomplete orders in batches.

        Maximum 20 orders can be canceled per request.
        Rate Limit: 300 orders per 2 seconds.
        Rate limit rule (except Options): User ID + Instrument ID.
        Rate limit rule (Options only): User ID + Instrument Family.
        Permission: Trade.

        If there is only one order in the request, it consumes the rate limit
        of the single Cancel order endpoint.

        See:
            https://www.okx.com/docs-v5/en/#order-book-trading-trade-post-cancel-multiple-orders

        Args:
            orders: List of orders to cancel (max 20 per request).
                Each item must have instId and either ordId or clOrdId.

        Returns:
            Dict containing the result of the batch cancel request.
        """
        if len(orders) == 0:
            raise ValueError("orders list must not be empty")
        if len(orders) > 20:
            raise ValueError("Cannot cancel more than 20 orders per batch")
        for i, o in enumerate(orders):
            if not o.get("instId"):
                raise ValueError(f"Order {i}: instId is required")
            if not o.get("ordId") and not o.get("clOrdId"):
                raise ValueError(f"Order {i}: either ordId or clOrdId is required")
        return await self.post(
            "/api/v5/trade/cancel-batch-orders",
            params=orders,
            auth=True,
        )

    async def get_order(
        self: HttpClientProtocol,
        inst_id: str,
        ord_id: str | None = None,
        cl_ord_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Retrieve order details.

        Rate Limit: 60 requests per 2 seconds.
        Rate limit rule (except Options): User ID + Instrument ID.
        Rate limit rule (Options only): User ID + Instrument Family.
        Permission: Read.

        See:
            https://www.okx.com/docs-v5/en/#order-book-trading-trade-get-order-details

        Args:
            inst_id: Instrument ID (e.g. "BTC-USDT"). Live instruments only.
            ord_id: Order ID. Either ord_id or cl_ord_id is required.
                If both are passed, ord_id will be used.
            cl_ord_id: Client Order ID. Either ord_id or cl_ord_id is required.
                If the cl_ord_id is associated with multiple orders,
                only the latest one will be returned.

        Returns:
            Dict containing the order details.
        """
        if ord_id is None and cl_ord_id is None:
            raise ValueError("Either ord_id or cl_ord_id is required")
        params: dict[str, str] = {"instId": inst_id}
        if ord_id is not None:
            params["ordId"] = ord_id
        elif cl_ord_id is not None:
            params["clOrdId"] = cl_ord_id
        return await self.get(
            "/api/v5/trade/order",
            params=params,
            auth=True,
        )

    async def get_orders_pending(
        self: HttpClientProtocol,
        inst_type: Literal["SPOT", "MARGIN", "SWAP", "FUTURES", "OPTION"] | None = None,
        inst_family: str | None = None,
        inst_id: str | None = None,
        ord_type: str | Iterable[str] | None = None,
        state: Literal["live", "partially_filled"] | None = None,
        after: str | None = None,
        before: str | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """
        Retrieve all incomplete orders under the current account.

        Rate Limit: 60 requests per 2 seconds.
        Rate limit rule: User ID.
        Permission: Read.

        See:
            https://www.okx.com/docs-v5/en/#order-book-trading-trade-get-order-list

        Args:
            inst_type: Instrument type (optional).
            inst_family: Instrument family. Applicable to FUTURES/SWAP/OPTION.
            inst_id: Instrument ID, e.g. "BTC-USD-200927".
            ord_type: Order type(s), comma-separated.
                market, limit, post_only, fok, ioc, optimal_limit_ioc,
                mmp, mmp_and_post_only, op_fok, elp.
            state: Order state. "live" or "partially_filled".
            after: Pagination: return records earlier than the requested ordId.
            before: Pagination: return records newer than the requested ordId.
            limit: Number of results per request. Max 100, default 100.

        Returns:
            Dict containing the list of pending orders.
        """
        params: dict[str, Any] = {}
        if inst_type is not None:
            params["instType"] = inst_type
        if inst_family is not None:
            params["instFamily"] = inst_family
        if inst_id is not None:
            params["instId"] = inst_id
        if ord_type is not None:
            params["ordType"] = join_iterable_field(ord_type)
        if state is not None:
            params["state"] = state
        if after is not None:
            params["after"] = after
        if before is not None:
            params["before"] = before
        if limit is not None:
            params["limit"] = str(limit)
        return await self.get(
            "/api/v5/trade/orders-pending",
            params=params,
            auth=True,
        )

    async def get_orders_history(
        self: HttpClientProtocol,
        inst_type: Literal["SPOT", "MARGIN", "SWAP", "FUTURES", "OPTION"],
        inst_family: str | None = None,
        inst_id: str | None = None,
        ord_type: str | Iterable[str] | None = None,
        state: Literal["canceled", "filled", "mmp_canceled"] | None = None,
        category: Literal[
            "twap",
            "adl",
            "full_liquidation",
            "partial_liquidation",
            "delivery",
            "ddh",
        ]
        | None = None,
        after: str | None = None,
        before: str | None = None,
        begin: int | str | None = None,
        end: int | str | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """
        Get completed orders placed in the last 7 days.

        Includes orders placed 7 days ago but completed in the last 7 days.
        Incomplete orders that have been canceled are only reserved for 2 hours.

        Rate Limit: 40 requests per 2 seconds.
        Rate limit rule: User ID.
        Permission: Read.

        See:
            https://www.okx.com/docs-v5/en/#order-book-trading-trade-get-order-history-last-7-days

        Args:
            inst_type: Instrument type. Required.
            inst_family: Instrument family. Applicable to FUTURES/SWAP/OPTION.
            inst_id: Instrument ID, e.g. "BTC-USDT".
            ord_type: Order type(s), comma-separated.
                market, limit, post_only, fok, ioc, optimal_limit_ioc,
                mmp, mmp_and_post_only, op_fok, elp.
            state: Order state. "canceled", "filled", or "mmp_canceled".
            category: Order category. twap, adl, full_liquidation, partial_liquidation,
                delivery, ddh (Delta dynamic hedge).
            after: Pagination: return records earlier than the requested ordId.
            before: Pagination: return records newer than the requested ordId.
            begin: Filter with a begin timestamp cTime (Unix ms).
            end: Filter with an end timestamp cTime (Unix ms).
            limit: Number of results per request. Max 100, default 100.

        Returns:
            Dict containing the order history.
        """
        params: dict[str, Any] = {"instType": inst_type}
        if inst_family is not None:
            params["instFamily"] = inst_family
        if inst_id is not None:
            params["instId"] = inst_id
        if ord_type is not None:
            params["ordType"] = join_iterable_field(ord_type)
        if state is not None:
            params["state"] = state
        if category is not None:
            params["category"] = category
        if after is not None:
            params["after"] = after
        if before is not None:
            params["before"] = before
        if begin is not None:
            params["begin"] = str(begin)
        if end is not None:
            params["end"] = str(end)
        if limit is not None:
            params["limit"] = str(limit)
        return await self.get(
            "/api/v5/trade/orders-history",
            params=params,
            auth=True,
        )
