"""GATE client package."""

from ._helpers import GateHelpers
from ._http import GateHttpClient
from ._mixins import AccountMixin, FuturesMixin, UnifiedMixin


class GateClient(GateHttpClient, FuturesMixin, UnifiedMixin, AccountMixin):
    """GATE Trading API Client with all available methods."""

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        demo: bool = False,
        broker_tag: str | None = None,
    ) -> None:
        """
        Initialize an GateClient instance.

        Args:
            api_key: GATE API key.
            api_secret: GATE API secret.
            demo: Whether to use demo trading mode.
                Default is False.
            broker_tag: Optional broker tag

        Example:
            ```python
            from aiotrade.clients import GateClient

            client = GateClient(
                api_key="your_api_key",
                api_secret="your_api_secret",
                demo=True,  # use demo trading
            )
            ```

        """
        super().__init__(
            api_key=api_key,
            api_secret=api_secret,
            demo=demo,
            broker_tag=broker_tag,
        )

        # Utility class for helper methods
        self.helpers = GateHelpers


__all__ = ["GateClient"]
