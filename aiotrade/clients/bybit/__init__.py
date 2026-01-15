"""Bybit client package."""

from ._http import BybitHttpClient
from ._mixins import AccountMixin, MarketMixin, PositionMixin, TradeMixin


class BybitClient(
    BybitHttpClient, AccountMixin, TradeMixin, MarketMixin, PositionMixin
):
    """ByBit Trading API Client with all available methods."""

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
            api_key (str | None): Bybit API key.
            api_secret (str | None): Bybit API secret.
            testnet (bool): Whether to use Bybit testnet environment.
                Default is False.
            demo (bool): Whether to use demo trading mode.
                Default is False.
            recv_window (int): Optional custom receive window (ms) for requests.
                Default is 5000.
            referral_id (str | None): Optional referral code.
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


__all__ = ["BybitClient"]
