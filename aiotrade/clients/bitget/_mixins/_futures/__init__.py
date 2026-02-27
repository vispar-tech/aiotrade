from ._account import AccountMixin
from ._market import MarketMixin
from ._position import PositionMixin
from ._trade import TradeMixin
from ._trigger import TriggerMixin


class FuturesMixin(
    AccountMixin,
    MarketMixin,
    PositionMixin,
    TradeMixin,
    TriggerMixin,
):
    """Combine futures mixins."""
