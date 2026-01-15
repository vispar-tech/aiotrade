"""Swap trading mixins for BingX API client."""

from ._account import AccountMixin as SwapAccountMixin
from ._market import MarketMixin as SwapMarketMixin
from ._trade import TradeMixin as SwapTradeMixin


class SwapMixin(SwapAccountMixin, SwapMarketMixin, SwapTradeMixin):
    """Combined swap mixin with all swap trading functionality."""


__all__ = ["SwapMixin"]
