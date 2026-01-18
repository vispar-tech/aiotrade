"""Swap trading mixins for BingX API client."""

from ._account import AccountMixin
from ._market import MarketMixin
from ._trade import TradeMixin


class SwapMixin(AccountMixin, MarketMixin, TradeMixin):
    """Combined swap mixin with all swap trading functionality."""


__all__ = ["SwapMixin"]
