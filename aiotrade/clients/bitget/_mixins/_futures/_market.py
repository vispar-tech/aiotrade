from typing import Any

from aiotrade._protocols import HttpClientProtocol
from aiotrade.types.bitget import ProductType


class MarketMixin:
    """Market data methods for Bitget Futures API client."""

    async def get_contract_config(
        self: HttpClientProtocol,
        product_type: ProductType,
        symbol: str | None = None,
    ) -> dict[str, Any]:
        """
        Get Futures Contract Configs (Details).

        Interface is used to get future contract details.

        GET /api/v2/mix/market/contracts

        Args:
            product_type: Product type.
            symbol: Trading pair in symbolName format, e.g. "BTCUSDT"

        Returns:
            dict: API response with contract details.

        """
        params: dict[str, str] = {"productType": product_type}
        if symbol is not None:
            params["symbol"] = symbol

        return await self.get(
            "/api/v2/mix/market/contracts",
            params=params,
        )
