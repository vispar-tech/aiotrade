from typing import Any

from aiotrade._protocols import HttpClientProtocol
from aiotrade.types.bitget import (
    BatchCancelSpotOrderParams,
    BatchPlaceSpotOrderParams,
    PlaceSpotOrderParams,
    SpotOrdersQueryParams,
)
from aiotrade.utils import to_str_fields


class TradeMixin:
    async def place_spot_order(
        self: HttpClientProtocol,
        params: PlaceSpotOrderParams,
    ) -> dict[str, Any]:
        """
        Place a spot order.

        Rate limit:
        10 requests/second/UID;
        1 request/second/UID for copy trading traders

        Reference:
            https://www.bitget.com/api-doc/spot/trade/Place-Order

        HTTP Request:
            POST /api/v2/spot/trade/place-order

        Args:
            params: PlaceOrderParams
            channel_api_code: str. Value for "X-CHANNEL-API-CODE" header.
            use_exp: Whether to allow float conversion with scientific notation.

        Returns:
            dict: Response from Bitget
        """
        return await self.post(
            "/api/v2/spot/trade/place-order",
            params=to_str_fields(
                params,
                {
                    "price",
                    "size",
                    "triggerPrice",
                    "presetTakeProfitPrice",
                    "executeTakeProfitPrice",
                    "presetStopLossPrice",
                    "executeStopLossPrice",
                },
            ),
            auth=True,
        )

    async def batch_place_spot_orders(
        self: HttpClientProtocol,
        params: BatchPlaceSpotOrderParams,
    ) -> dict[str, Any]:
        """
        Place multiple spot orders in batch.

        Frequency limit: 5 times/1s (UID); Trader frequency limit: 1 times/1s (UID)

        Reference:
            https://www.bitget.com/api-doc/spot/trade/Batch-Order

        HTTP Request:
            POST /api/v2/spot/trade/batch-orders

        Args:
            params: BatchPlaceOrderParams - Parameters for the batch order.
            channel_api_code: str - Value for "X-CHANNEL-API-CODE" header.
            use_exp: Whether to allow float conversion with scientific notation.

        Returns:
            dict: Response from Bitget.


        """
        return await self.post(
            "/api/v2/spot/trade/batch-orders",
            params=to_str_fields(
                params,
                {
                    "price",
                    "size",
                    "presetTakeProfitPrice",
                    "executeTakeProfitPrice",
                    "presetStopLossPrice",
                    "executeStopLossPrice",
                },
            ),
            auth=True,
        )

    async def batch_cancel_spot_orders(
        self: HttpClientProtocol,
        params: BatchCancelSpotOrderParams,
    ) -> dict[str, Any]:
        """
        Cancel Spot Orders in Batch.

        Frequency limit: 10 times/1s (UID)

        Description:
            Cancel Orders in Batch

            For batch cancellation
            (simultaneously revoking multiple orders for the same symbol),
            it is not permitted to mix the use
            of orderId and clientOid.
            The identifiers used must be consistent across
            all orders in the batch. Otherwise, orders that
            only submit a clientOid will fail to be cancelled.

        Reference:
            https://www.bitget.com/api-doc/spot/trade/Batch-Cancel-Order

        HTTP Request:
            POST /api/v2/spot/trade/batch-cancel-order

        Args:
            params: BatchCancelOrderParams
                symbol: Trading pair name, e.g. BTCUSDT (optional)
                batchMode: 'single' (default) or 'multiple'
                orderList: List of objects with symbol (if needed),
                    orderId or clientOid (must not mix both types within a batch).

        Returns:
            dict: Response from Bitget API


        """
        return await self.post(
            "/api/v2/spot/trade/batch-cancel-order",
            params=params,
            auth=True,
        )

    async def cancel_order_by_symbol(
        self: HttpClientProtocol,
        symbol: str,
    ) -> dict[str, Any]:
        """
        Cancel order by symbol.

        Frequency limit: 5 times/1s (UID)

        HTTP Request:
            POST /api/v2/spot/trade/cancel-symbol-order

        Args:
            symbol: Trading pair name, e.g. BTCUSDT

        Returns:
            dict: Response from Bitget API


        """
        params: dict[str, str] = {"symbol": symbol}
        return await self.post(
            "/api/v2/spot/trade/cancel-symbol-order",
            params=params,
            auth=True,
        )

    async def get_unfilled_orders(
        self: HttpClientProtocol,
        params: SpotOrdersQueryParams | None = None,
    ) -> dict[str, Any]:
        """
        Get Current (Unfilled) Spot Orders.

        Frequency limit: 20 times/1s (UID)

        HTTP Request:
            GET /api/v2/spot/trade/unfilled-orders

        Args:
            params (SpotOrdersQueryParams): Query parameters for unfilled orders.

        Returns:
            dict: API response from Bitget


        """
        return await self.get(
            "/api/v2/spot/trade/unfilled-orders",
            params=params,
            auth=True,
        )

    async def get_spot_history_orders(
        self: HttpClientProtocol,
        params: SpotOrdersQueryParams | None = None,
    ) -> dict[str, Any]:
        """
        Get History Spot Orders (last 90 days only).

        Frequency limit: 20 times/1s (UID)

        HTTP Request:
            GET /api/v2/spot/trade/history-orders

        Args:
            params (SpotOrdersQueryParams): Query parameters for history orders.

        Returns:
            dict: API response from Bitget


        """
        return await self.get(
            "/api/v2/spot/trade/history-orders",
            params=params,
            auth=True,
        )
