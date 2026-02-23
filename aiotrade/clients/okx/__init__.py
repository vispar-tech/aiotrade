"""OKX client package."""

from ._helpers import OkxHelpers
from ._http import OkxHttpClient
from ._mixins import FundingAccountMixin, PublicMixin, TradeMixin, TradingAccountMixin


class OkxClient(
    OkxHttpClient, TradingAccountMixin, FundingAccountMixin, PublicMixin, TradeMixin
):
    """OKX Trading API Client with all available methods."""

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        passphrase: str | None = None,
        demo: bool = False,
        recv_window: int = 5000,
    ) -> None:
        """
        Initialize an OkxClient instance.

        Args:
            api_key (str | None): OKX API key.
            api_secret (str | None): OKX API secret.
            passphrase (str | None): OKX API passphrase.
            demo (bool): Whether to use demo trading mode.
                Default is False.
            recv_window (int): Optional custom receive window (ms) for requests.
                Default is 5000.

        Example:
            ```python
            from aiotrade.clients import OkxClient

            client = OkxClient(
                api_key="your_api_key",
                api_secret="your_api_secret",
                passphrase="your_passphrase",
                demo=True,  # use demo trading
            )
            ```

        """
        super().__init__(api_key, api_secret, passphrase, demo, recv_window)

        # Utility class for helper methods
        self.helpers = OkxHelpers


__all__ = ["OkxClient"]
