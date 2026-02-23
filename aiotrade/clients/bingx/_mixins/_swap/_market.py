from typing import Any

from aiotrade._protocols import HttpClientProtocol


class MarketMixin:
    """Market data methods for BingX swap API client.

    This mixin provides methods for retrieving market data and prices
    for swap trading.
    """

    async def get_swap_contracts(
        self: "HttpClientProtocol",
        symbol: str | None = None,
    ) -> dict[str, Any]:
        """
        Retrieve contract information for BingX Perpetual Swaps.

        GET /openApi/swap/v2/quote/contracts

        https://bingx-api.github.io/docs-v3/#/en/Swap/Market%20Data/USDT-M%20Perp%20Futures%20symbols

        Args:
            symbol: Optional; contract symbol
                (e.g., "BTC-USDT"). If None, returns all contracts.

        Returns:
            dict[str, Any]: API response containing contracts information.
        """
        params: dict[str, Any] = {}
        if symbol is not None:
            params["symbol"] = symbol

        return await self.get(
            "/openApi/swap/v2/quote/contracts",
            params=params,
        )

    async def get_swap_klines(
        self: "HttpClientProtocol",
        symbol: str,
        interval: str,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """
        Retrieve Kline/Candlestick data for BingX Perpetual Swap contracts.

        GET /openApi/swap/v3/quote/klines

        https://bingx-api.github.io/docs-v3/#/en/Swap/Market%20Data/Kline%2FCandlestick%20Data

        Args:
            symbol: The trading pair symbol (e.g., "BTC-USDT"),
                must contain a hyphen.
            interval: Kline interval (e.g. "1m", "5m", "1h", "1d").
            start_time: Start timestamp (ms), inclusive. (optional)
            end_time: End timestamp (ms), inclusive. (optional)
            limit: How many klines to return
                (default 500, max 1440). (optional)

        Returns:
            dict[str, Any]: API response with candlestick/kline data.
        """
        params: dict[str, Any] = {
            "symbol": symbol,
            "interval": interval,
        }
        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time
        if limit is not None:
            params["limit"] = limit

        return await self.get(
            "/openApi/swap/v3/quote/klines",
            params=params,
        )
