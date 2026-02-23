from collections.abc import Iterable
from typing import Any, Literal

from aiotrade._protocols import HttpClientProtocol
from aiotrade.clients._utils import join_iterable_field, to_str_fields
from aiotrade.types.okx import (
    AlgoOrderHistoryState,
    AlgoOrderType,
    AlgorithmOrderParams,
    CancelAlgorithmOrderParams,
)


class AlgorithmTradeMixin:
    """Mixin for algo trading endpoints."""

    async def cancel_algo_orders(
        self: HttpClientProtocol,
        orders: list[CancelAlgorithmOrderParams],
    ) -> dict[str, Any]:
        """
        Cancel unfilled algo orders (max 10 per request).

        See: https://www.okx.com/docs-v5/en/#order-book-trading-trade-post-cancel-algo-order

        Args:
            orders: A list of dicts, each containing at least "instrument_id" and
                either "algorithm_id" or "algorithm_client_order_id".

        Returns:
            Dict with response data.
        """
        # Defensive check: at least one order, not more than 10.
        if not orders or len(orders) == 0:
            raise ValueError("At least one order param must be provided.")
        if len(orders) > 10:
            raise ValueError("A maximum of 10 orders can be canceled per request.")

        return await self.post(
            "/api/v5/trade/cancel-algos",
            params=orders,
            auth=True,
        )

    async def place_algo_order(
        self: HttpClientProtocol,
        order: AlgorithmOrderParams,
    ) -> dict[str, Any]:
        """
        Place an algo order (trigger, oco, chase, conditional, twap, trailing, etc.).

        See: https://www.okx.com/docs-v5/en/#order-book-trading-trade-post-place-algo-order

        Args:
            order: Dictionary of algo order parameters.

        Returns:
            Dict with response data containing algoId, algoClOrdId, etc.
        """
        converted = to_str_fields(
            order,
            {
                "sz",
                "closeFraction",
                "tpTriggerPx",
                "tpOrdPx",
                "slTriggerPx",
                "slOrdPx",
                "chaseVal",
                "maxChaseVal",
                "triggerPx",
                "ordPx",
                "orderPx",
                "callbackRatio",
                "callbackSpread",
                "activePx",
                "pxVar",
                "pxSpread",
                "szLimit",
                "pxLimit",
                "timeInterval",
            },
        )
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
                },
            )
            for algo in converted.get("attachAlgoOrds", [])
        ]
        return await self.post(
            "/api/v5/trade/order-algo",
            params=converted,
            auth=True,
        )

    async def get_algo_order(
        self: HttpClientProtocol,
        algo_id: str | None = None,
        algo_cl_ord_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Retrieve algo order details.

        Rate Limit: 20 requests per 2 seconds.
        Rate limit rule: User ID.
        Permission: Read.

        See:
            https://www.okx.com/docs-v5/en/#order-book-trading-trade-get-algo-order-details

        Args:
            algo_id: Algo ID. Either algo_id or algo_cl_ord_id is required.
                If both are passed, algo_id will be used.
            algo_cl_ord_id: Client-supplied Algo ID (up to 32 characters).
                Either algo_id or algo_cl_ord_id is required.

        Returns:
            Dict containing the algo order details.
        """
        if algo_id is None and algo_cl_ord_id is None:
            raise ValueError("Either algo_id or algo_cl_ord_id is required")
        params: dict[str, str] = {}
        if algo_id is not None:
            params["algoId"] = algo_id
        elif algo_cl_ord_id is not None:
            params["algoClOrdId"] = algo_cl_ord_id
        return await self.get(
            "/api/v5/trade/order-algo",
            params=params,
            auth=True,
        )

    async def get_algo_orders_pending(
        self: HttpClientProtocol,
        ord_type: AlgoOrderType | Iterable[AlgoOrderType],
        algo_id: str | None = None,
        inst_type: Literal["SPOT", "MARGIN", "SWAP", "FUTURES"] | None = None,
        inst_id: str | None = None,
        after: str | None = None,
        before: str | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """
        Retrieve a list of untriggered Algo orders under the current account.

        Rate Limit: 20 requests per 2 seconds.
        Rate limit rule: User ID.
        Permission: Read.

        See:
            https://www.okx.com/docs-v5/en/#order-book-trading-trade-get-algo-order-list

        Args:
            ord_type: Order type. conditional, oco, chase, trigger,
                move_order_stop, iceberg, twap.
                conditional and oco can be used together, comma-separated.
            algo_id: Algo ID filter.
            inst_type: Instrument type.
            inst_id: Instrument ID, e.g. "BTC-USDT".
            after: Pagination: records earlier than the requested algoId.
            before: Pagination: records newer than the requested algoId.
            limit: Number of results per request. Max 100, default 100.

        Returns:
            Dict containing the list of pending algo orders.
        """
        params: dict[str, Any] = {
            "ordType": join_iterable_field(ord_type),
        }
        if algo_id is not None:
            params["algoId"] = algo_id
        if inst_type is not None:
            params["instType"] = inst_type
        if inst_id is not None:
            params["instId"] = inst_id
        if after is not None:
            params["after"] = after
        if before is not None:
            params["before"] = before
        if limit is not None:
            params["limit"] = str(limit)
        return await self.get(
            "/api/v5/trade/orders-algo-pending",
            params=params,
            auth=True,
        )

    async def get_algo_orders_history(
        self: HttpClientProtocol,
        ord_type: AlgoOrderType | Iterable[AlgoOrderType],
        state: AlgoOrderHistoryState | None = None,
        algo_id: str | None = None,
        inst_type: Literal["SPOT", "MARGIN", "SWAP", "FUTURES"] | None = None,
        inst_id: str | None = None,
        after: str | None = None,
        before: str | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """
        Retrieve algo orders under the current account in the last 3 months.

        Rate Limit: 20 requests per 2 seconds.
        Rate limit rule: User ID.
        Permission: Read.

        See:
            https://www.okx.com/docs-v5/en/#order-book-trading-trade-get-algo-order-history

        Args:
            ord_type: Order type. conditional, oco, chase, trigger,
                move_order_stop, iceberg, twap.
                conditional and oco can be used together, comma-separated.
            state: Order state. effective, canceled, order_failed.
                Either state or algo_id is required.
            algo_id: Algo ID. Either state or algo_id is required.
            inst_type: Instrument type.
            inst_id: Instrument ID, e.g. "BTC-USDT".
            after: Pagination: records earlier than the requested algoId.
            before: Pagination: records newer than the requested algoId.
            limit: Number of results per request. Max 100, default 100.

        Returns:
            Dict containing the algo order history.
        """
        if state is None and algo_id is None:
            raise ValueError("Either state or algo_id is required")
        params: dict[str, Any] = {
            "ordType": join_iterable_field(ord_type),
        }
        if state is not None:
            params["state"] = state
        if algo_id is not None:
            params["algoId"] = algo_id
        if inst_type is not None:
            params["instType"] = inst_type
        if inst_id is not None:
            params["instId"] = inst_id
        if after is not None:
            params["after"] = after
        if before is not None:
            params["before"] = before
        if limit is not None:
            params["limit"] = str(limit)
        return await self.get(
            "/api/v5/trade/orders-algo-history",
            params=params,
            auth=True,
        )
