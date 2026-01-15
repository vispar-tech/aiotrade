"""BingX client package."""

from ._http import BingxHttpClient
from ._mixins import AccountMixin, CommonMixin, FuturesMixin, SpotMixin, SwapMixin


class BingxClient(
    BingxHttpClient, AccountMixin, FuturesMixin, SpotMixin, SwapMixin, CommonMixin
):
    """BingX Trading API Client with all available methods."""

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        demo: bool = False,
        recv_window: int = 5000,
    ) -> None:
        """
        Initialize a BingxClient instance.

        Args:
            api_key (str | None): BingX API key.
            api_secret (str | None): BingX API secret.
            demo (bool): Whether to use demo trading mode.
                Default is False.
            recv_window (int): Optional custom receive window (ms) for requests.
                Default is 5000.

        Example:
            ```python
            from aiotrade.clients import BingxClient

            client = BingxClient(
                api_key="your_api_key",
                api_secret="your_api_secret",
                testnet=True,  # use testnet environment
            )
            ```

        """
        super().__init__(api_key, api_secret, demo, recv_window)


__all__ = ["BingxClient"]
