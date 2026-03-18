"""KuCoin client package."""

from aiotrade.clients.kucoin._broker import BrokerClient
from aiotrade.clients.kucoin._mixins import AccountMixin, FuturesMixin

from ._helpers import KuCoinHelpers
from ._http import KuCoinHttpClient


class KuCoinClient(KuCoinHttpClient, AccountMixin, FuturesMixin):
    """
    KuCoin Trading API Client with all available methods.

    Supports **only KuCoin API v3** endpoints.
    """

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        passphrase: str | None = None,
        recv_window: int = 5000,
    ) -> None:
        """
        Initialize a KuCoinClient instance.

        **Only KuCoin API v3 is supported.**

        Args:
            api_key: KuCoin API key.
            api_secret: KuCoin API secret.
            passphrase: KuCoin API passphrase.
            recv_window: Optional custom receive window (ms) for requests.
                Default is 5000.

        Example:
            ```python
            from aiotrade.clients import KuCoinClient

            client = KuCoinClient(
                api_key="your_api_key",
                api_secret="your_api_secret",
                passphrase="your_passphrase",
            )
            ```
        """
        super().__init__(
            api_key=api_key,
            api_secret=api_secret,
            passphrase=passphrase,
            recv_window=recv_window,
        )

        # Utility class for helper methods
        self.helpers = KuCoinHelpers

    @staticmethod
    def broker(broker_name: str, broker_partner: str, broker_key: str) -> BrokerClient:
        """
        Return a KuCoin OAuth BrokerClient for API integration.

        Supports **only broker endpoints available in KuCoin API v3**.

        Usage:
            broker = KuCoinClient.broker(
                broker_name="name",
                broker_partner="partner",
                broker_key="key"
            )
        """
        return BrokerClient(
            broker_name=broker_name,
            broker_partner=broker_partner,
            broker_key=broker_key,
        )


__all__ = ["KuCoinClient"]
