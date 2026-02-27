"""Bybit client package."""

from ._broker import BrokerClient
from ._helpers import BybitHelpers
from ._http import BybitHttpClient
from ._mixins import AccountMixin, MarketMixin, PositionMixin, TradeMixin, UserMixin


class BybitClient(
    BybitHttpClient, AccountMixin, TradeMixin, MarketMixin, PositionMixin, UserMixin
):
    """ByBit Trading API Client with all available methods."""

    @staticmethod
    def broker(client_id: str, client_secret: str) -> BrokerClient:
        """
        Return a Bybit OAuth BrokerClient for API integration.

        Usage:
            broker = BybitClient.broker(client_id="...", client_secret="...")
        """
        return BrokerClient(client_id, client_secret)

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        testnet: bool = False,
        demo: bool = False,
        recv_window: int = 5000,
        referral_id: str | None = None,
    ) -> None:
        """
        Initialize a BybitClient instance.

        Args:
            api_key: Bybit API key.
            api_secret: Bybit API secret.
            testnet: Whether to use Bybit testnet environment.
                Default is False.
            demo: Whether to use demo trading mode.
                Default is False.
            recv_window: Optional custom receive window (ms) for requests.
                Default is 5000.
            referral_id: Optional referral code.
                Default is None.

        Example:
            ```python
            from aiotrade.clients import BybitClient

            client = BybitClient(
                api_key="your_api_key",
                api_secret="your_api_secret",
                testnet=True,  # use testnet environment
            )
            ```

        """
        super().__init__(api_key, api_secret, testnet, demo, recv_window, referral_id)

        # Utility class for helper methods
        self.helpers = BybitHelpers


__all__ = ["BybitClient"]
