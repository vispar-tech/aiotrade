"""Position management HTTP methods."""

from typing import Any, Dict

from ..protocols import HttpClientProtocol


class PositionMixin:
    """Mixin for position endpoints."""

    async def get_position_info(self: HttpClientProtocol) -> Dict[str, Any]:
        """Get position info."""
        raise NotImplementedError

    async def set_leverage(self: HttpClientProtocol) -> Dict[str, Any]:
        """Set leverage."""
        raise NotImplementedError

    async def switch_position_mode(self: HttpClientProtocol) -> Dict[str, Any]:
        """Switch position mode."""
        raise NotImplementedError

    async def set_trading_stop(self: HttpClientProtocol) -> Dict[str, Any]:
        """Set trading stop."""
        raise NotImplementedError

    async def set_auto_add_margin(self: HttpClientProtocol) -> Dict[str, Any]:
        """Set auto add margin."""
        raise NotImplementedError

    async def add_or_reduce_margin(self: HttpClientProtocol) -> Dict[str, Any]:
        """Add or reduce margin."""
        raise NotImplementedError

    async def get_closed_pnl(self: HttpClientProtocol) -> Dict[str, Any]:
        """Get closed PnL (2 years)."""
        raise NotImplementedError

    async def get_closed_options_positions(self: HttpClientProtocol) -> Dict[str, Any]:
        """Get closed options positions (6 months)."""
        raise NotImplementedError

    async def move_position(self: HttpClientProtocol) -> Dict[str, Any]:
        """Move position."""
        raise NotImplementedError

    async def get_move_position_history(self: HttpClientProtocol) -> Dict[str, Any]:
        """Get move position history."""
        raise NotImplementedError

    async def confirm_new_risk_limit(self: HttpClientProtocol) -> Dict[str, Any]:
        """Confirm new risk limit."""
        raise NotImplementedError
