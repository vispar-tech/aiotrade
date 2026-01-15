"""Futures-related mixins for BingX API client."""

from ._market import MarketMixin as FuturesMarketMixin
from ._trade import TradeMixin as FuturesTradeMixin


class FuturesMixin(FuturesMarketMixin, FuturesTradeMixin):
    """Combined futures mixin with market and trading functionality."""


__all__ = ["FuturesMixin"]
