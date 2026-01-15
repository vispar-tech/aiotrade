"""Account-related mixins for BingX API client."""

from ._fund import FundMixin
from ._sub import SubMixin
from ._wallet import WalletMixin


class AccountMixin(FundMixin, SubMixin, WalletMixin):
    """Combined account mixin with all account-related functionality."""


__all__ = ["AccountMixin"]
