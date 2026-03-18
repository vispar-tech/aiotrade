from typing import Any, Literal, Protocol

from .types import (
    UnifiedCancelOrderRequest,
    UnifiedMarginMode,
    UnifiedPendingOrder,
    UnifiedPlaceOrderRequest,
    UnifiedPlaceSpotOrderRequest,
    UnifiedPositionInfo,
    UnifiedSide,
)


class ExchangeClient(Protocol):
    """Protocol defining common interface for exchange clients."""

    # Account/Balance methods
    async def get_margin_mode(self, symbol: str | None) -> UnifiedMarginMode:
        """Query user margin mode."""
        ...

    async def update_margin_mode(
        self, symbol: str | None, mode: UnifiedMarginMode
    ) -> None:
        """Update user margin mode."""
        ...

    async def get_hedge_mode(self, symbol: str | None) -> bool | None:
        """Query whether hedge mode is enabled."""
        ...

    async def set_hedge_mode(self, enabled: bool) -> None:
        """Enable or disable hedge mode."""
        ...

    async def get_asset_mode(self) -> Literal["single", "union"] | None:
        """Query the current asset mode (e.g., 'USDT', 'multi-asset', etc)."""
        ...

    async def set_asset_mode(self, mode: Literal["single", "union"]) -> None:
        """Set the asset mode (e.g., 'USDT', 'multi-asset', etc)."""
        ...

    async def get_usdt_available_balance(self) -> float | None:
        """Get the available USDT balance for the account."""
        ...

    async def get_spot_usdt_balance(self) -> float | None:
        """Get the spot USDT balance for the account."""
        ...

    # Position methods
    async def get_position_info(
        self, symbol: str | None = None
    ) -> list[UnifiedPositionInfo]:
        """Get current position information."""
        ...

    async def close_position(
        self, position: UnifiedPositionInfo, order: UnifiedPlaceOrderRequest
    ) -> dict[str, Any]:
        """Cancel position."""
        ...

    async def place_spot_order(
        self, params: UnifiedPlaceSpotOrderRequest
    ) -> dict[str, Any]:
        """Place spot order."""
        ...

    async def get_spot_order_exec_qty(self, response: dict[str, Any]) -> float:
        """Get the executed quantity for a placed spot order.

        Accepts the response as returned from place_spot_order.
        """
        ...

    async def batch_place_order(
        self, has_existing_position: bool, requests: list[UnifiedPlaceOrderRequest]
    ) -> dict[str, Any]:
        """Place multiple orders at once."""
        ...

    async def batch_cancel_order(
        self, requests: list[UnifiedCancelOrderRequest]
    ) -> None:
        """Cancel multiple orders at once."""
        ...

    async def get_pending_orders(self) -> list[UnifiedPendingOrder]:
        """Retrieve pending orders."""
        ...

    # Trading methods
    async def set_trading_stop(
        self,
        symbol: str,
        take_profit: float | None = None,
        stop_loss: float | None = None,
        active_price: float | None = None,
        trailing_delivation: float | None = None,
        position: UnifiedPositionInfo | None = None,
        side: UnifiedSide | None = None,
        qty: float | None = None,
    ) -> None:
        """Set trading stop-loss/take-profit."""
        ...

    async def set_leverage(self, symbol: str, leverage: float) -> None:
        """Set leverage for a symbol or account."""
        ...
