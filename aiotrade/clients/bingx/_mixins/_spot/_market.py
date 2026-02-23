from typing import Any

from aiotrade._protocols import HttpClientProtocol


class MarketMixin:
    """Market data methods for BingX spot API client.

    This mixin provides methods for retrieving market data and prices
    for spot trading.
    """

    async def get_spot_symbols(
        self: "HttpClientProtocol",
        symbol: str | None = None,
    ) -> dict[str, Any]:
        """
        Query tradable spot pairs whose symbol contains the given string.

        GET /openApi/spot/v1/common/symbols

        https://bingx-api.github.io/docs-v3/#/en/Spot/Market%20Data/Spot%20trading%20symbols

        Args:
            symbol: Partial symbol (optional).

        Returns:
            dict[str, Any]: API response containing spot pairs matching the symbol.
        """
        params: dict[str, Any] = {}
        if symbol is not None:
            params["symbol"] = symbol
        return await self.get(
            "/openApi/spot/v1/common/symbols",
            params=params,
        )

    async def get_spot_klines(
        self: "HttpClientProtocol",
        symbol: str,
        interval: str,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """
        Retrieve Kline/Candlestick data for BingX Spot market.

        GET /openApi/spot/v2/market/kline

        https://bingx-api.github.io/docs-v3/#/en/Spot/Market%20Data/Kline%2FCandlestick%20Data

        Args:
            symbol: Trading pair symbol, e.g. "BTC-USDT".
                Must be uppercase and include a hyphen.
            interval: Candle interval, e.g. "1m", "5m", "1h", "1d", etc.
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
            "/openApi/spot/v2/market/kline",
            params=params,
        )
