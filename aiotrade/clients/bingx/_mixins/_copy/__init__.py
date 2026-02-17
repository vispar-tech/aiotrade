"""Copytrading mixins for BingX API client."""

from ._perpetual import PerpetualMixin
from ._spot import SpotMixin


class CopyTradingMixin(PerpetualMixin, SpotMixin):
    """Combined copytrading mixin with all copytrading-related functionality."""


__all__ = ["CopyTradingMixin"]
