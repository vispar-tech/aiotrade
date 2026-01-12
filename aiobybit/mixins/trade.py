"""Trade management HTTP methods."""

from ..protocols import HttpClientProtocol


class TradeMixin:
    """Mixin for trade endpoints."""

    async def place_order(self: HttpClientProtocol) -> None:
        """Place an order."""
        raise NotImplementedError

    async def amend_order(self: HttpClientProtocol) -> None:
        """Amend an existing order."""
        raise NotImplementedError

    async def cancel_order(self: HttpClientProtocol) -> None:
        """Cancel a single order."""
        raise NotImplementedError

    async def get_open_and_closed_orders(self: HttpClientProtocol) -> None:
        """Get open and closed orders."""
        raise NotImplementedError

    async def cancel_all_orders(self: HttpClientProtocol) -> None:
        """Cancel all active orders."""
        raise NotImplementedError

    async def get_order_history(self: HttpClientProtocol) -> None:
        """Get order history (up to 2 years)."""
        raise NotImplementedError

    async def get_trade_history(self: HttpClientProtocol) -> None:
        """Get trade history (up to 2 years)."""
        raise NotImplementedError

    async def batch_place_order(self: HttpClientProtocol) -> None:
        """Batch place multiple orders."""
        raise NotImplementedError

    async def batch_amend_order(self: HttpClientProtocol) -> None:
        """Batch amend multiple orders."""
        raise NotImplementedError

    async def batch_cancel_order(self: HttpClientProtocol) -> None:
        """Batch cancel multiple orders."""
        raise NotImplementedError

    async def get_borrow_quota_spot(self: HttpClientProtocol) -> None:
        """Get borrow quota for spot trading."""
        raise NotImplementedError

    async def set_dcp(self: HttpClientProtocol) -> None:
        """Set DCP (Dynamic Contract Parameters)."""
        raise NotImplementedError

    async def pre_check_order(self: HttpClientProtocol) -> None:
        """Pre-check order before placement."""
        raise NotImplementedError
