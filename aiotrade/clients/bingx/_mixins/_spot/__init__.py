"""Spot trading mixins for BingX API client."""

from ._account import AccountMixin as SpotAccountMixin
from ._market import MarketMixin as SpotMarketMixin
from ._trade import TradeMixin as SpotTradeMixin
from ._wallet import WalletMixin as SpotWalletMixin


class SpotMixin(SpotAccountMixin, SpotMarketMixin, SpotTradeMixin, SpotWalletMixin):
    """Combined spot mixin with all spot trading functionality."""


__all__ = [
    "SpotMixin",
]
