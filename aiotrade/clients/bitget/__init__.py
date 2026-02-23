"""Bitget client package."""

from aiotrade.clients.bitget._mixins import FuturesMixin, PublicMixin, SpotMixin

from ._helpers import BitgetHelpers
from ._http import BitgetHttpClient


class BitgetClient(BitgetHttpClient, FuturesMixin, SpotMixin, PublicMixin):
    """Bitget Trading API Client with all available methods."""

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        passphrase: str | None = None,
        demo: bool = False,
        recv_window: int = 5000,
    ) -> None:
        """
        Initialize a BitgetClient instance.

        Args:
            api_key: Bitget API key.
            api_secret: Bitget API secret.
            passphrase: Bitget API passphrase.
            demo: Whether to use demo trading mode.
                Default is False.
            recv_window: Optional custom receive window (ms) for requests.
                Default is 5000.

        Example:
            ```python
            from aiotrade.clients import BitgetClient

            client = BitgetClient(
                api_key="your_api_key",
                api_secret="your_api_secret",
                passphrase="your_passphrase",
                demo=True,  # use demo trading
            )
            ```

        """
        super().__init__(api_key, api_secret, passphrase, demo, recv_window)

        # Utility class for helper methods
        self.helpers = BitgetHelpers


__all__ = ["BitgetClient"]
