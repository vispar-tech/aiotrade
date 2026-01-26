import json
from typing import Any, Dict, Literal, Optional

import orjson

from aiotrade._protocols import HttpClientProtocol
from aiotrade.types.bingx import (
    MarginMode,
    PlaceSwapOrderParams,
    PositionSide,
    SwapOrderType,
    TpSlStruct,
)


class TradeMixin:
    """Trading methods for BingX swap API client.

    This mixin provides methods for placing and managing trades
    in swap markets.
    """

    async def place_swap_order(
        self: "HttpClientProtocol", params: PlaceSwapOrderParams
    ) -> Dict[str, Any]:
        """Place a new swap order.

        Endpoint: POST /openApi/swap/v2/trade/order

        Args:
            params: PlaceOrderParams - Order parameters compliant with BingX API.

        Returns:
            Dict: The API response.
        """
        field_mapping = {
            "symbol": "symbol",
            "order_type": "type",
            "side": "side",
            "position_side": "positionSide",
            "reduce_only": "reduceOnly",
            "price": "price",
            "quantity": "quantity",
            "quote_order_qty": "quoteOrderQty",
            "stop_price": "stopPrice",
            "price_rate": "priceRate",
            "working_type": "workingType",
            "take_profit": "takeProfit",
            "stop_loss": "stopLoss",
            "client_order_id": "clientOrderId",
            "time_in_force": "timeInForce",
            "close_position": "closePosition",
            "activation_price": "activationPrice",
            "stop_guaranteed": "stopGuaranteed",
            "position_id": "positionId",
        }

        order_data: Dict[str, Any] = {}
        for key, value in params.items():
            if value is None:
                continue
            mapped_key = field_mapping.get(key, key)
            if key in {"reduce_only", "close_position"}:
                order_data[mapped_key] = str(value).lower()
                continue
            if key in {"take_profit", "stop_loss"} and isinstance(value, dict):
                struct: TpSlStruct = value  # type: ignore
                order_data[mapped_key] = json.dumps(
                    {field_mapping.get(k, k): v for k, v in struct.items()}
                )
                continue
            order_data[mapped_key] = value

        return await self.post(
            "/openApi/swap/v2/trade/order",
            params=order_data,
            auth=True,
        )

    async def place_swap_batch_orders(
        self: "HttpClientProtocol", batch_orders: list[PlaceSwapOrderParams]
    ) -> Dict[str, Any]:
        """
        Place multiple swap orders (batch).

        Endpoint: POST /openApi/swap/v2/trade/batchOrders

        See:
            https://bingx-api.github.io/docs-v3/#/en/Swap/Trades%20Endpoints/Place%20multiple%20orders

        Args:
            batch_orders: List[PlaceSwapOrderParams] - Up to 5 order dicts.

        Returns:
            Dict: The API response.
        """
        field_mapping = {
            "symbol": "symbol",
            "order_type": "type",
            "side": "side",
            "position_side": "positionSide",
            "reduce_only": "reduceOnly",
            "price": "price",
            "quantity": "quantity",
            "quote_order_qty": "quoteOrderQty",
            "stop_price": "stopPrice",
            "price_rate": "priceRate",
            "working_type": "workingType",
            "take_profit": "takeProfit",
            "stop_loss": "stopLoss",
            "client_order_id": "clientOrderId",
            "time_in_force": "timeInForce",
            "close_position": "closePosition",
            "activation_price": "activationPrice",
            "stop_guaranteed": "stopGuaranteed",
            "position_id": "positionId",
        }

        def serialize_order(params: PlaceSwapOrderParams) -> Dict[str, Any]:
            order: Dict[str, Any] = {}
            for key, value in params.items():
                if value is None:
                    continue
                mapped_key = field_mapping.get(key, key)
                if key in {"reduce_only", "close_position"}:
                    order[mapped_key] = str(value).lower()
                    continue
                if key in {"take_profit", "stop_loss"} and isinstance(value, dict):
                    struct: TpSlStruct = value  # type: ignore
                    order[mapped_key] = json.dumps(
                        {field_mapping.get(k, k): v for k, v in struct.items()}
                    )
                    continue
                order[mapped_key] = value
            return order

        if not (1 <= len(batch_orders) <= 5):
            raise ValueError("batch_orders must contain between 1 and 5 orders.")

        batch_order_data = [serialize_order(order) for order in batch_orders]
        payload = {
            "batchOrders": orjson.dumps(batch_order_data).decode(),
        }

        return await self.post(
            "/openApi/swap/v2/trade/batchOrders",
            params=payload,
            auth=True,
        )

    async def close_swap_position(
        self: "HttpClientProtocol",
        position_id: str,
    ) -> Dict[str, Any]:
        """Close a Perpetual Swap position.

        POST /openApi/swap/v1/trade/closePosition

        https://bingx-api.github.io/docs-v3/#/en/Swap/Trades%20Endpoints/Close%20position%20by%20position%20ID
        """
        params = {
            "positionId": position_id,
        }
        return await self.post(
            "/openApi/swap/v1/trade/closePosition", params=params, auth=True
        )

    async def get_swap_order_history(
        self: "HttpClientProtocol",
        symbol: Optional[str] = None,
        currency: Optional[Literal["USDT", "USDC"]] = None,
        order_id: Optional[int] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 500,
    ) -> Dict[str, Any]:
        """
        Query swap order history (completed or canceled orders).

        GET /openApi/swap/v2/trade/allOrders

        https://bingx-api.github.io/docs-v3/#/en/Swap/Trades%20Endpoints/Query%20Order%20history

        Args:
            symbol (str, optional): Trading pair symbol, e.g. "BTC-USDT".
            If not specified, returns all.
            currency (str, optional): USDT or USDC.
            order_id (int, optional): Return orders after this orderId.
            start_time (int, optional): Start timestamp (ms).
            end_time (int, optional): End timestamp (ms).
            limit (int, required): Number of results to return.
            Default 500, max 1000.

        Returns:
            Dict[str, Any]: API response with order history.
        """
        params: Dict[str, Any] = {}

        if symbol is not None:
            params["symbol"] = symbol
        if currency is not None:
            params["currency"] = currency
        if order_id is not None:
            params["orderId"] = order_id
        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time

        params["limit"] = limit

        return await self.get(
            "/openApi/swap/v2/trade/allOrders",
            params=params,
            auth=True,
        )

    async def get_swap_order_details(
        self: "HttpClientProtocol",
        symbol: str,
        order_id: Optional[int] = None,
        client_order_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Query swap order details (active/completed/canceled orders).

        GET /openApi/swap/v2/trade/order

        https://bingx-api.github.io/docs-v3/#/en/Swap/Trades%20Endpoints/Query%20Order%20details

        Args:
            symbol (str, required): Trading pair symbol, e.g. "BTC-USDT".
            order_id (int, optional): Order ID.
            client_order_id (str, optional): Custom user order ID
                (1~40 chars, lowercase).

        Returns:
            Dict[str, Any]: API response with order details.
        """
        params: Dict[str, Any] = {"symbol": symbol}
        if order_id is not None:
            params["orderId"] = order_id
        if client_order_id is not None:
            params["clientOrderId"] = client_order_id

        return await self.get(
            "/openApi/swap/v2/trade/order",
            params=params,
            auth=True,
        )

    async def get_swap_open_orders(
        self: "HttpClientProtocol",
        symbol: Optional[str] = None,
        order_type: Optional[SwapOrderType] = None,
    ) -> Dict[str, Any]:
        """
        Query all currently open swap orders (open entrusts).

        GET /openApi/swap/v2/trade/openOrders

        https://bingx-api.github.io/docs-v3/#/en/Swap/Trades%20Endpoints/Current%20All%20Open%20Orders

        Args:
            symbol: Optional symbol to filter.
            order_type: Optional order type.

        Returns:
            Dict[str, Any]: API response with list of open orders.
        """
        params: Dict[str, Any] = {}
        if symbol is not None:
            params["symbol"] = symbol
        if order_type is not None:
            params["type"] = order_type

        return await self.get(
            "/openApi/swap/v2/trade/openOrders",
            params=params,
            auth=True,
        )

    async def cancel_swap_batch_orders(
        self: "HttpClientProtocol",
        symbol: str,
        order_id_list: Optional[list[int]] = None,
        client_order_id_list: Optional[list[str]] = None,
    ) -> Dict[str, Any]:
        """
        Cancel multiple swap orders in a batch (max 10 per request).

        DELETE /openApi/swap/v2/trade/batchOrders

        https://bingx-api.github.io/docs-v3/#/en/Swap/Trades%20Endpoints/Cancel%20multiple%20orders

        Args:
            symbol: Symbol string, e.g. "BTC-USDT"
            order_id_list: Optional list of up to 10 system order IDs
            client_order_id_list: Optional list of up to 10 custom IDs

        Returns:
            Dict[str, Any]: API response indicating cancellation results.

        Notes:
            - At least one of order_id_list or client_order_id_list must be provided.
            - Signature required. UID rate limit: 5/sec.
            - Master and sub accounts supported.
        """
        if not order_id_list and not client_order_id_list:
            raise ValueError(
                "At least one of order_id_list or "
                "client_order_id_list must be provided."
            )

        params: Dict[str, Any] = {
            "symbol": symbol,
        }
        if order_id_list is not None:
            params["orderIdList"] = orjson.dumps(order_id_list).decode()
        if client_order_id_list is not None:
            params["clientOrderIdList"] = orjson.dumps(client_order_id_list).decode()

        return await self.delete(
            "/openApi/swap/v2/trade/batchOrders",
            params=params,
            auth=True,
        )

    async def get_swap_position_history(
        self: "HttpClientProtocol",
        symbol: str,
        currency: Optional[Literal["USDC", "USDT"]] = None,
        position_id: Optional[int] = None,
        start_ts: Optional[int] = None,
        end_ts: Optional[int] = None,
        page_index: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Query the position history of perpetual contracts for the specified symbol.

        GET /openApi/swap/v1/trade/positionHistory

        https://bingx-api.github.io/docs-v3/#/en/Swap/Trades%20Endpoints/Query%20Position%20History

        Args:
            symbol (str): Trading pair, e.g. "BTC-USDT"
            currency (str, optional): USDC or USDT
            position_id (int, optional): Position ID to filter by
            start_ts (int, optional): Start timestamp in milliseconds
                (default: 90 days ago)
            end_ts (int, optional): End timestamp in milliseconds (default: now)
            page_index (int, optional): Page number (default: 1)
            page_size (int, optional): Page size, max 100 (default: 1000)

        Returns:
            Dict[str, Any]: API response containing position history records.

        Notes:
            - Time window max is three months.
            - Signature required.
            - UID rate limit: 5/sec.
            - Master and sub accounts supported.
        """
        params: Dict[str, Any] = {
            "symbol": symbol,
        }
        if currency is not None:
            params["currency"] = currency
        if position_id is not None:
            params["positionId"] = position_id
        if start_ts is not None:
            params["startTs"] = start_ts
        if end_ts is not None:
            params["endTs"] = end_ts
        if page_index is not None:
            params["pageIndex"] = page_index
        if page_size is not None:
            params["pageSize"] = page_size

        return await self.get(
            "/openApi/swap/v1/trade/positionHistory",
            params=params,
            auth=True,
        )

    async def set_swap_leverage(
        self: "HttpClientProtocol",
        symbol: str,
        side: PositionSide,
        leverage: int,
    ) -> Dict[str, Any]:
        """
        Adjust the user's opening leverage in the specified symbol contract.

        POST /openApi/swap/v2/trade/leverage

        https://bingx-api.github.io/docs-v3/#/en/Swap/Trades%20Endpoints/Set%20Leverage

        Args:
            symbol (str): Trading pair symbol (e.g., "BTC-USDT"), must include a hyphen.
            side (PositionSide): Leverage side, e.g., "LONG", "SHORT", or "BOTH".
            leverage (int): Leverage value.


        Returns:
            Dict[str, Any]: Response from BingX API.

        Notes:
            - UID rate limit: 5/sec.
            - Signature required.
            - Supported for master and sub accounts.
        """
        params: Dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "leverage": leverage,
        }

        return await self.post(
            "/openApi/swap/v2/trade/leverage",
            params=params,
            auth=True,
        )

    async def set_swap_position_mode(
        self: "HttpClientProtocol",
        dual_side_position: bool,
    ) -> Dict[str, Any]:
        """
        Set the position mode of perpetual contract (dual or single position mode).

        POST /openApi/swap/v1/positionSide/dual

        https://bingx-api.github.io/docs-v3/#/en/Swap/Trades%20Endpoints/Set%20Position%20Mode

        Args:
            dual_side_position (bool): True for dual position mode,
                False for single position mode.

        Returns:
            Dict[str, Any]: Response from BingX API.

        Notes:
            - "dualSidePosition" POST param: "true" for dual, "false" for single.
            - UID rate limit: 4/sec per UID.
            - Signature required.
            - Supported for master and sub accounts.
        """
        params: Dict[str, Any] = {"dualSidePosition": str(dual_side_position).lower()}

        return await self.post(
            "/openApi/swap/v1/positionSide/dual",
            params=params,
            auth=True,
        )

    async def get_swap_position_mode(
        self: "HttpClientProtocol",
    ) -> Dict[str, Any]:
        """
        Get the position mode of perpetual contract (dual or single position mode).

        GET /openApi/swap/v1/positionSide/dual

        https://bingx-api.github.io/docs-v3/#/en/Swap/Trades%20Endpoints/Query%20position%20mode

        Returns:
            Dict[str, Any]: API response with the current position mode.

        Notes:
            - UID rate limit: 2/sec per UID.
            - Signature required.
            - Supported for master and sub accounts.
        """
        return await self.get(
            "/openApi/swap/v1/positionSide/dual",
            auth=True,
        )

    async def get_swap_leverage_and_available_positions(
        self: "HttpClientProtocol",
        symbol: str,
    ) -> Dict[str, Any]:
        """
        Query leverage and available positions for the contract symbol.

        GET /openApi/swap/v2/trade/leverage

        https://bingx-api.github.io/docs-v3/#/en/Swap/Trades%20Endpoints/Query%20Leverage%20and%20Available%20Positions

        Args:
            symbol (str): Trading pair symbol, e.g., "BTC-USDT".

        Returns:
            Dict[str, Any]: API response with leverage and available positions.

        Notes:
            - UID rate limit: 5/sec per UID.
            - Signature required.
            - Supported for master and sub accounts.
        """
        params: Dict[str, Any] = {"symbol": symbol}
        return await self.get(
            "/openApi/swap/v2/trade/leverage",
            params=params,
            auth=True,
        )

    async def cancel_all_swap_open_orders(
        self: "HttpClientProtocol",
        symbol: Optional[str] = None,
        order_type: Optional[SwapOrderType] = None,
    ) -> Dict[str, Any]:
        """
        Cancel all open swap orders for the account or symbol/type, if specified.

        DELETE /openApi/swap/v2/trade/allOpenOrders

        https://bingx-api.github.io/docs-v3/#/en/Swap/Trades%20Endpoints/Cancel%20All%20Open%20Orders

        Args:
            symbol (Optional[str]): Trading pair symbol, e.g. "BTC-USDT".
                If omitted, cancels all orders of all symbols.
            order_type (Optional[SwapOrderType]): Order type to cancel.

        Returns:
            Dict[str, Any]: API response.

        Notes:
            - UID Rate Limit: 5/sec per UID.
            - Signature verification required.
            - Supported for master and sub accounts.
        """
        params: Dict[str, Any] = {}
        if symbol is not None:
            params["symbol"] = symbol
        if order_type is not None:
            params["type"] = order_type

        return await self.delete(
            "/openApi/swap/v2/trade/allOpenOrders",
            params=params,
            auth=True,
        )

    async def change_swap_margin_type(
        self: "HttpClientProtocol",
        symbol: str,
        margin_type: MarginMode,
    ) -> Dict[str, Any]:
        """
        Change the user's margin mode on the specified symbol contract.

        POST /openApi/swap/v2/trade/marginType

        https://bingx-api.github.io/docs-v3/#/en/Swap/Trades%20Endpoints/Change%20Margin%20Type

        Args:
            symbol (str): Trading pair symbol, e.g., "BTC-USDT" (must contain '-').
            margin_type (Literal): "ISOLATED", "CROSSED", or "SEPARATE_ISOLATED".

        Returns:
            Dict[str, Any]: API response indicating margin type result.

        Notes:
            - UID Rate Limit: 2/second per UID.
            - Signature verification required.
            - Supported for master and sub accounts.
        """
        params: Dict[str, Any] = {
            "symbol": symbol,
            "marginType": margin_type,
        }
        return await self.post(
            "/openApi/swap/v2/trade/marginType",
            params=params,
            auth=True,
        )

    async def get_swap_margin_type(
        self: "HttpClientProtocol",
        symbol: str,
    ) -> Dict[str, Any]:
        """
        Query the user's margin mode on the specified symbol contract.

        GET /openApi/swap/v2/trade/marginType

        https://bingx-api.github.io/docs-v3/#/en/Swap/Trades%20Endpoints/Query%20Margin%20Type

        Args:
            symbol (str): Trading pair symbol, e.g., "BTC-USDT" (must contain '-').

        Returns:
            Dict[str, Any]: API response indicating the margin type for the contract.

        Notes:
            - UID Rate Limit: 2/second per UID.
            - Signature verification required.
            - Supported for master and sub accounts.
        """
        params: Dict[str, Any] = {
            "symbol": symbol,
        }
        return await self.get(
            "/openApi/swap/v2/trade/marginType",
            params=params,
            auth=True,
        )

    async def get_swap_full_orders(
        self: "HttpClientProtocol",
        symbol: str | None = None,
        order_id: int | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int = 500,
    ) -> Dict[str, Any]:
        """
        Query all swap orders (history and open) for BingX.

        GET /openApi/swap/v1/trade/fullOrder

        https://bingx-api.github.io/docs-v3/#/en/Swap/Trades%20Endpoints/All%20Orders

        Args:
            symbol (str, optional): Trading pair symbol. If None, query all pairs.
            order_id (int, optional): Return orders after this ID.
            start_time (int, optional): Start time (ms).
            end_time (int, optional): End time (ms).
            limit (int, optional): Results to return. Default 500, max 1000.

        Returns:
            Dict[str, Any]: API response containing list of full orders.
        """
        params: Dict[str, Any] = {}
        if symbol:
            params["symbol"] = symbol
        if order_id is not None:
            params["orderId"] = order_id
        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time
        params["limit"] = limit

        return await self.get(
            "/openApi/swap/v1/trade/fullOrder",
            params=params,
            auth=True,
        )
