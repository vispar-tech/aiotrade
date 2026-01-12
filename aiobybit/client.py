"""Main ByBit client class."""

from .http import BybitHttpClient
from .mixins import AccountMixin, MarketMixin, PositionMixin, TradeMixin


class BybitClient(
    BybitHttpClient, AccountMixin, TradeMixin, MarketMixin, PositionMixin
):
    """ByBit Trading API Client with all available methods."""
