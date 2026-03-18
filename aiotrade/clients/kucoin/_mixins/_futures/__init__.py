"""Futures-related mixins for BingX API client."""

from ._market import MarketMixin
from ._orders import OrdersMixin
from ._position import PositionMixin


class FuturesMixin(MarketMixin, OrdersMixin, PositionMixin):
    """Combined futures mixin with market, orders and position functionality."""
