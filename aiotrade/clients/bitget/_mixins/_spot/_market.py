from typing import Any

from aiotrade._protocols import HttpClientProtocol


class MarketMixin:
    """Spot market REST endpoints for Bitget."""

    async def get_symbol_info(
        self: HttpClientProtocol,
        symbol: str | None,
    ) -> dict[str, Any]:
        """
        Get spot trading pair information.

        Frequency limit: 20 times/1s (IP)

        Reference:
            https://www.bitget.com/api-doc/spot/market/Get-Symbols

        HTTP Request:
            GET /api/v2/spot/public/symbols

        Args:
            symbol: trading pair name, e.g. BTCUSDT.
                If the field is left blank,
                    all trading pair information will be returned.

        Returns:
            dict: Response with spot symbols information.

        Example:
            >>> await client.get_symbol_info()  # all symbols
            >>> await client.get_symbol_info("BTCUSDT")
        """
        params: dict[str, Any] = {}
        if symbol:
            params["symbol"] = symbol
        return await self.get(
            "/api/v2/spot/public/symbols",
            params=params,
            auth=False,
        )
