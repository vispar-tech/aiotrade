from ._account import AccountMixin
from ._market import MarketMixin
from ._trade import TradeMixin


class UsdmFuturesMixin(MarketMixin, AccountMixin, TradeMixin):
    """USDM Futures endpoints."""
