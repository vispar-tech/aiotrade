"""Spot trading mixins for BingX API client."""

from ._account import AccountMixin
from ._market import MarketMixin
from ._trade import TradeMixin
from ._wallet import WalletMixin


class SpotMixin(AccountMixin, MarketMixin, TradeMixin, WalletMixin):
    """Combined spot mixin with all spot trading functionality."""


__all__ = [
    "SpotMixin",
]
