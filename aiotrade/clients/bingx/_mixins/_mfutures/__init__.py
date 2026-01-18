"""Futures-related mixins for BingX API client."""

from ._market import MarketMixin
from ._trade import TradeMixin


class FuturesMixin(MarketMixin, TradeMixin):
    """Combined futures mixin with market and trading functionality."""


__all__ = ["FuturesMixin"]
