from ._account import AccountMixin
from ._market import MarketMixin
from ._trade import TradeMixin


class SpotMixin(MarketMixin, TradeMixin, AccountMixin):
    pass
