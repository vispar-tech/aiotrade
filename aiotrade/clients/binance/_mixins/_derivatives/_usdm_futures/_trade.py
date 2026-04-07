from typing import Any

from aiotrade._protocols import HttpClientProtocol
from aiotrade.types.binance import AlgorithmOrderParams, CreateOrderParams, MarginType
from aiotrade.utils import to_str_fields


class TradeMixin:
    """Trade endpoints."""

    async def create_order(
        self: "HttpClientProtocol", params: CreateOrderParams
    ) -> dict[str, Any]:
        """
        Send in a new order.

        API Docs:
            POST /fapi/v1/order

        Args:
            params: CreateOrderParams

        Returns:
            dict: API JSON response containing order details.
        """
        return await self.post(
            "/fapi/v1/order",
            params=to_str_fields(params, {"quantity", "price"}),
            auth=True,
        )

    async def create_batch_orders(
        self: "HttpClientProtocol",
        params: list[CreateOrderParams],
    ) -> dict[str, Any]:
        """
        Place Multiple Orders.

        API Docs:
            POST /fapi/v1/batchOrders

        Args:
            batch_orders: List of order dictionaries. Max 5 orders.
                Each order dict should contain parameters like symbol,
                    side, type, quantity, etc., similar to create_order.

        Returns:
            dict: API JSON response containing batch order results.
        """
        return await self.post(
            "/fapi/v1/batchOrders",
            params={
                "batchOrders": to_str_fields(params, {"quantity", "price"}),
            },
            auth=True,
        )

    async def cancel_order(
        self: "HttpClientProtocol",
        symbol: str,
        order_id: int | None = None,
        orig_client_order_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Cancel an active order.

        API Docs:
            DELETE /fapi/v1/order

        Args:
            symbol: Trading pair symbol.
            order_id: Order ID to cancel.
            orig_client_order_id: Original client order ID to cancel.
                Either order_id or orig_client_order_id must be provided.

        Returns:
            dict: API JSON response containing cancellation details.
        """
        if order_id is None and orig_client_order_id is None:
            raise ValueError(
                "Either order_id or orig_client_order_id must be provided."
            )
        params: dict[str, Any] = {
            "symbol": symbol,
        }
        if order_id is not None:
            params["orderId"] = order_id
        if orig_client_order_id is not None:
            params["origClientOrderId"] = orig_client_order_id
        return await self.delete(
            "/fapi/v1/order",
            params=params,
            auth=True,
        )

    async def cancel_batch_orders(
        self: "HttpClientProtocol",
        symbol: str,
        order_id_list: list[int] | None = None,
        orig_client_order_id_list: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Cancel Multiple Orders.

        API Docs:
            DELETE /fapi/v1/batchOrders

        Args:
            symbol: Trading pair symbol.
            order_id_list: List of order IDs to cancel (max 10).
            orig_client_order_id_list: List of original client order IDs
                to cancel (max 10).
            Either order_id_list or orig_client_order_id_list must be provided.

        Returns:
            dict: API JSON response containing batch cancellation details.
        """
        if order_id_list is None and orig_client_order_id_list is None:
            raise ValueError(
                "Either order_id_list or orig_client_order_id_list must be provided."
            )
        params: dict[str, Any] = {
            "symbol": symbol,
        }
        if order_id_list is not None:
            params["orderIdList"] = order_id_list
        if orig_client_order_id_list is not None:
            params["origClientOrderIdList"] = orig_client_order_id_list
        return await self.delete(
            "/fapi/v1/batchOrders",
            params=params,
            auth=True,
        )

    async def cancel_all_open_orders(
        self: "HttpClientProtocol",
        symbol: str,
    ) -> dict[str, Any]:
        """
        Cancel All Open Orders.

        API Docs:
            DELETE /fapi/v1/allOpenOrders

        Args:
            symbol: Trading pair symbol.

        Returns:
            dict: API JSON response containing cancellation details for all open orders.
        """
        params: dict[str, Any] = {
            "symbol": symbol,
        }
        return await self.delete(
            "/fapi/v1/allOpenOrders",
            params=params,
            auth=True,
        )

    async def get_order(
        self: "HttpClientProtocol",
        symbol: str,
        order_id: int | None = None,
        orig_client_order_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Check an order's status.

        API Docs:
            GET /fapi/v1/order

        Args:
            symbol: Trading pair symbol.
            order_id: Order ID to query.
            orig_client_order_id: Original client order ID to query.
                Either order_id or orig_client_order_id must be provided.

        Returns:
            dict: API JSON response containing order status details.
        """
        if order_id is None and orig_client_order_id is None:
            raise ValueError(
                "Either order_id or orig_client_order_id must be provided."
            )
        params: dict[str, Any] = {
            "symbol": symbol,
        }
        if order_id is not None:
            params["orderId"] = order_id
        if orig_client_order_id is not None:
            params["origClientOrderId"] = orig_client_order_id
        return await self.get(
            "/fapi/v1/order",
            params=params,
            auth=True,
        )

    async def get_all_orders(
        self: "HttpClientProtocol",
        symbol: str,
        order_id: int | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """
        Get all account orders; active, canceled, or filled.

        API Docs:
            GET /fapi/v1/allOrders

        Args:
            symbol: Trading pair symbol.
            order_id: Order ID to start from (returns orders >= orderId).
            start_time: Start time in milliseconds.
            end_time: End time in milliseconds.
            limit: Number of orders to retrieve (default 500, max 1000).

        Returns:
            dict: API JSON response containing list of orders.
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
            "/fapi/v1/allOrders",
            params=params,
            auth=True,
        )

    async def get_open_orders(
        self: "HttpClientProtocol",
        symbol: str | None = None,
    ) -> dict[str, Any]:
        """
        Get all open orders on a symbol.

        API Docs:
            GET /fapi/v1/openOrders

        Args:
            symbol: Trading pair symbol (optional).
                If not provided, returns orders for all symbols.

        Returns:
            dict: API JSON response containing list of open orders.
        """
        params: dict[str, Any] = {}
        if symbol is not None:
            params["symbol"] = symbol
        return await self.get(
            "/fapi/v1/openOrders",
            params=params,
            auth=True,
        )

    async def get_open_order(
        self: "HttpClientProtocol",
        symbol: str,
        order_id: int | None = None,
        orig_client_order_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Query open order.

        API Docs:
            GET /fapi/v1/openOrder

        Args:
            symbol: Trading pair symbol.
            order_id: Order ID to query.
            orig_client_order_id: Original client order ID to query.
                Either orderId or origClientOrderId must be provided.

        Returns:
            dict: API JSON response containing open order details.
        """
        if order_id is None and orig_client_order_id is None:
            raise ValueError("Either orderId or origClientOrderId must be provided.")
        params: dict[str, Any] = {
            "symbol": symbol,
        }
        if order_id is not None:
            params["orderId"] = order_id
        if orig_client_order_id is not None:
            params["origClientOrderId"] = orig_client_order_id
        return await self.get(
            "/fapi/v1/openOrder",
            params=params,
            auth=True,
        )

    async def change_margin_type(
        self: "HttpClientProtocol",
        symbol: str,
        margin_type: MarginType,
    ) -> dict[str, Any]:
        """
        Change symbol level margin type.

        API Docs:
            POST /fapi/v1/marginType

        Args:
            symbol: Trading pair symbol.
            margin_type: Margin type ("ISOLATED" or "CROSSED").

        Returns:
            dict: API JSON response confirming margin type change.
        """
        params: dict[str, Any] = {
            "symbol": symbol,
            "marginType": margin_type,
        }
        return await self.post(
            "/fapi/v1/marginType",
            params=params,
            auth=True,
        )

    async def change_position_mode(
        self: "HttpClientProtocol",
        dual_side_position: bool,
    ) -> dict[str, Any]:
        """
        Change user's position mode (Hedge Mode or One-way Mode) on EVERY symbol.

        API Docs:
            POST /fapi/v1/positionSide/dual

        Args:
            dual_side_position: True for Hedge Mode, False for One-way Mode.

        Returns:
            dict: API JSON response confirming position mode change.
        """
        params: dict[str, Any] = {
            "dualSidePosition": "true" if dual_side_position else "false",
        }
        return await self.post(
            "/fapi/v1/positionSide/dual",
            params=params,
            auth=True,
        )

    async def change_leverage(
        self: "HttpClientProtocol",
        symbol: str,
        leverage: int,
    ) -> dict[str, Any]:
        """
        Change user's initial leverage of specific symbol market.

        API Docs:
            POST /fapi/v1/leverage

        Args:
            symbol: Trading pair symbol.
            leverage: Target initial leverage (int from 1 to 125).

        Returns:
            dict: API JSON response confirming leverage change.
        """
        params: dict[str, Any] = {
            "symbol": symbol,
            "leverage": leverage,
        }
        return await self.post(
            "/fapi/v1/leverage",
            params=params,
            auth=True,
        )

    async def change_multi_assets_mode(
        self: "HttpClientProtocol",
        multi_assets_margin: bool,
    ) -> dict[str, Any]:
        """
        Change user's Multi-Assets mode on Every symbol.

        API Docs:
            POST /fapi/v1/multiAssetsMargin

        Args:
            multi_assets_margin: True for Multi-Assets Mode,
                False for Single-Asset Mode.

        Returns:
            dict: API JSON response confirming multi-assets mode change.
        """
        params: dict[str, Any] = {
            "multiAssetsMargin": "true" if multi_assets_margin else "false",
        }
        return await self.post(
            "/fapi/v1/multiAssetsMargin",
            params=params,
            auth=True,
        )

    async def get_position_info(
        self: "HttpClientProtocol",
        symbol: str | None = None,
    ) -> dict[str, Any]:
        """
        Get current position information.

        (only symbol that has position or open orders will be returned).

        API Docs:
            GET /fapi/v2/positionRisk

        Args:
            symbol: Trading pair symbol (optional). If not provided,
                returns positions for all symbols.

        Returns:
            dict: API JSON response containing position risk information.
        """
        params: dict[str, Any] = {}
        if symbol is not None:
            params["symbol"] = symbol
        return await self.get(
            "/fapi/v2/positionRisk",
            params=params,
            auth=True,
        )

    async def get_position_info_v3(
        self: "HttpClientProtocol",
        symbol: str | None = None,
    ) -> dict[str, Any]:
        """
        Get current position information.

        (only symbol that has position or open orders will be returned).

        API Docs:
            GET /fapi/v3/positionRisk

        Args:
            symbol: Trading pair symbol (optional). If not provided,
                returns positions for all symbols.

        Returns:
            dict: API JSON response containing position risk information.
        """
        params: dict[str, Any] = {}
        if symbol is not None:
            params["symbol"] = symbol
        return await self.get(
            "/fapi/v3/positionRisk",
            params=params,
            auth=True,
        )

    async def create_algo_order(
        self: "HttpClientProtocol",
        params: AlgorithmOrderParams,
    ) -> dict[str, Any]:
        """
        Send in a new Algo (conditional) order.

        API Docs:
            POST /fapi/v1/algoOrder

        Args:
            params: TypedDict for the given algo order, depending on type.
              See TrailingStopMarketAlgoOrderParams and StopTakeProfitAlgoOrderParams.

        Returns:
            dict: API JSON response containing algo order details.
        """
        return await self.post(
            "/fapi/v1/algoOrder",
            params=to_str_fields(
                params,
                {"activatePrice", "callbackRate", "quantity", "price", "triggerPrice"},
            ),
            auth=True,
        )

    async def cancel_algo_order(
        self: "HttpClientProtocol",
        algo_id: int | None = None,
        client_algo_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Cancel an active algo order.

        API Docs:
            DELETE /fapi/v1/algoOrder

        Args:
            algo_id: Algo order ID to cancel.
            client_algo_id: Client algo order ID to cancel.
                Either algo_id or client_algo_id must be provided.

        Returns:
            dict: API JSON response containing cancellation details.
        """
        if algo_id is None and client_algo_id is None:
            raise ValueError("Either algo_id or client_algo_id must be provided.")
        params: dict[str, Any] = {}
        if algo_id is not None:
            params["algoId"] = algo_id
        if client_algo_id is not None:
            params["clientAlgoId"] = client_algo_id
        return await self.delete(
            "/fapi/v1/algoOrder",
            params=params,
            auth=True,
        )

    async def cancel_all_algo_open_orders(
        self: "HttpClientProtocol",
        symbol: str,
    ) -> dict[str, Any]:
        """
        Cancel All Algo Open Orders.

        API Docs:
            DELETE /fapi/v1/algoOpenOrders

        Args:
            symbol: Trading pair symbol.

        Returns:
            dict: API JSON response containing cancellation details for
                all algo open orders.
        """
        params: dict[str, Any] = {
            "symbol": symbol,
        }
        return await self.delete(
            "/fapi/v1/algoOpenOrders",
            params=params,
            auth=True,
        )

    async def get_algo_order(
        self: "HttpClientProtocol",
        algo_id: int | None = None,
        client_algo_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Check an algo order's status.

        API Docs:
            GET /fapi/v1/algoOrder

        Args:
            algo_id: Algo order ID to query.
            client_algo_id: Client algo order ID to query.
                Either algo_id or client_algo_id must be provided.

        Returns:
            dict: API JSON response containing algo order status details.
        """
        if algo_id is None and client_algo_id is None:
            raise ValueError("Either algo_id or client_algo_id must be provided.")
        params: dict[str, Any] = {}
        if algo_id is not None:
            params["algoId"] = algo_id
        if client_algo_id is not None:
            params["clientAlgoId"] = client_algo_id
        return await self.get(
            "/fapi/v1/algoOrder",
            params=params,
            auth=True,
        )

    async def get_open_algo_orders(
        self: "HttpClientProtocol",
        algo_type: str | None = None,
        symbol: str | None = None,
        algo_id: int | None = None,
    ) -> dict[str, Any]:
        """
        Get all algo open orders on a symbol.

        API Docs:
            GET /fapi/v1/openAlgoOrders

        Args:
            algo_type: Algo type (optional).
            symbol: Trading pair symbol (optional). If not provided, returns orders
                for all symbols.
            algo_id: Algo order ID (optional).

        Returns:
            dict: API JSON response containing list of open algo orders.
        """
        params: dict[str, Any] = {}
        if algo_type is not None:
            params["algoType"] = algo_type
        if symbol is not None:
            params["symbol"] = symbol
        if algo_id is not None:
            params["algoId"] = algo_id
        return await self.get(
            "/fapi/v1/openAlgoOrders",
            params=params,
            auth=True,
        )

    async def get_all_algo_orders(
        self: "HttpClientProtocol",
        symbol: str,
        algo_id: int | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        page: int | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """
        Get all algo orders; active, CANCELED, TRIGGERED or FINISHED.

        API Docs:
            GET /fapi/v1/allAlgoOrders

        Args:
            symbol: Trading pair symbol.
            algo_id: Algo order ID to start from (returns orders >= algoId).
            start_time: Start time in milliseconds.
            end_time: End time in milliseconds.
            page: Page number.
            limit: Number of orders to retrieve (default 500, max 1000).

        Returns:
            dict: API JSON response containing list of algo orders.
        """
        params: dict[str, Any] = {
            "symbol": symbol,
        }
        if algo_id is not None:
            params["algoId"] = algo_id
        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit
        return await self.get(
            "/fapi/v1/allAlgoOrders",
            params=params,
            auth=True,
        )
