"""Binance client package."""

from typing import Any

from aiotrade._protocols import ParamsType
from aiotrade._types import HttpMethod

from ._helpers import BinanceHelpers
from ._http import BinanceHttpClient
from ._mixins import AccountWalletMixin, SpotMixin, UsdmFuturesMixin
from ._url_resolver import BinanceUrlResolver


class BinanceClient(BinanceHttpClient, AccountWalletMixin, UsdmFuturesMixin, SpotMixin):
    """Binance Trading API Client with all available methods."""

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        demo: bool = False,
        recv_window: int = 5000,
    ) -> None:
        """
        Initialize a BinanceClient instance.

        Args:
            api_key: Binance API key.
            api_secret: Binance API secret.
            demo: Whether to use testnet/demo trading mode.
                Default is False.
            recv_window: Optional custom receive window (ms) for requests.
                Default is 5000.

        Example:
            ```python
            from aiotrade.clients import BinanceClient

            client = BinanceClient(
                api_key="your_api_key",
                api_secret="your_api_secret",
                demo=True,  # use testnet/demo trading
            )
            ```

        """
        super().__init__(api_key, api_secret, demo, recv_window)

        # Utility class for helper methods
        self.helpers = BinanceHelpers
        # Utility class for build urls
        self.url_resolver = BinanceUrlResolver

    async def _async_request(
        self,
        method: HttpMethod,
        endpoint: str,
        params: ParamsType | None = None,
        headers: dict[str, str] | None = None,
        auth: bool = False,
        base_url: str | None = None,
    ) -> dict[str, Any]:
        return await super()._async_request(
            method,
            endpoint,
            params,
            headers,
            auth,
            self.url_resolver.resolve(self.demo, endpoint),
        )


__all__ = ["BinanceClient"]
