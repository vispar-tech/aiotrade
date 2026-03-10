"""Bitget client package."""

from aiotrade.clients.bitget._broker import BrokerClient
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
        channel_api_code: str | None = None,
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
        super().__init__(
            api_key=api_key,
            api_secret=api_secret,
            passphrase=passphrase,
            demo=demo,
            recv_window=recv_window,
            channel_api_code=channel_api_code,
        )

        # Utility class for helper methods
        self.helpers = BitgetHelpers

    @staticmethod
    def broker(
        client_id: str,
        bybit_client_user_id: str,
        rsa_public_key: str | None = None,
        rsa_private_key: str | None = None,
    ) -> BrokerClient:
        """
        Return a Bitget OAuth BrokerClient for API integration.

        Args:
            client_id: Bitget app client ID.
            rsa_public_key: (optional) RSA public key for encryption.
            rsa_private_key: (optional) RSA private key for decryption.

        Usage:
            broker = BitgetClient.broker(
                client_id="...",
                rsa_public_key="...",
                rsa_private_key="...",
            )
        """
        return BrokerClient(
            client_id,
            bybit_client_user_id,
            rsa_public_key=rsa_public_key,
            rsa_private_key=rsa_private_key,
        )


__all__ = ["BitgetClient"]
