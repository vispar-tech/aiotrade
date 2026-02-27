from typing import Any, Literal

from aiotrade._protocols import HttpClientProtocol
from aiotrade.types.binance import SpotOrderParams


class TradeMixin:
    """Spot Trade endpoints mixin."""

    async def create_spot_order(
        self: HttpClientProtocol,
        params: SpotOrderParams,
    ) -> dict[str, Any]:
        """
        Send in a new spot order.

        API Docs:
            POST /api/v3/order

        Weight: 1

        Args:
            params (SpotOrderParams): Parameters for the new spot order.

        Returns:
            dict: API JSON response with order result.

        Notes:
            - See SpotOrderParams for required and optional arguments.
            - Some required fields depend on the order type (LIMIT, MARKET, etc.).
            - This endpoint requires a signed request.
        """
        return await self.post(
            "/api/v3/order",
            params=params,
            auth=True,
        )

    async def cancel_spot_order(
        self: HttpClientProtocol,
        symbol: str,
        order_id: int | None = None,
        orig_client_order_id: str | None = None,
        new_client_order_id: str | None = None,
        cancel_restrictions: Literal["ONLY_NEW", "ONLY_PARTIALLY_FILLED"] | None = None,
    ) -> dict[str, Any]:
        """
        Cancel an active spot order.

        API Docs:
            DELETE /api/v3/order

        Weight: 1

        Args:
            symbol: Symbol of the order to cancel.
            order_id: Order ID to cancel.
            orig_client_order_id: Original client order ID.
            new_client_order_id: New client order ID for this cancel action.
            cancel_restrictions: Cancel restriction.

        Returns:
            dict: API JSON response with cancel result.

        Notes:
            - Either order_id or orig_client_order_id must be provided.
            - If both order_id and orig_client_order_id are provided,
              order_id is searched first, then the orig_client_order_id from
              that result is checked against that order.
        """
        if order_id is None and orig_client_order_id is None:
            raise ValueError(
                "Either 'order_id' or 'orig_client_order_id' must be provided."
            )

        params: dict[str, Any] = {
            "symbol": symbol,
        }
        if order_id is not None:
            params["orderId"] = order_id
        if orig_client_order_id is not None:
            params["origClientOrderId"] = orig_client_order_id
        if new_client_order_id is not None:
            params["newClientOrderId"] = new_client_order_id
        if cancel_restrictions is not None:
            params["cancelRestrictions"] = cancel_restrictions

        return await self.delete(
            "/api/v3/order",
            params=params,
            auth=True,
        )
