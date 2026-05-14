from typing import Any, Literal

from aiotrade._protocols import HttpClientProtocol


class MarketMixin:
    """Market endpoints."""

    async def get_exchange_info(
        self: HttpClientProtocol,
    ) -> dict[str, Any]:
        """
        Get exchange trading rules and symbol information.

        API Docs:
            GET /fapi/v1/exchangeInfo

        Returns:
            dict: API JSON response.
        """
        return await self.get(
            "/fapi/v1/exchangeInfo",
        )

    async def get_klines(
        self: HttpClientProtocol,
        symbol: str,
        interval: Literal[
            "1m",
            "3m",
            "5m",
            "15m",
            "30m",
            "1h",
            "2h",
            "4h",
            "6h",
            "8h",
            "12h",
            "1d",
            "3d",
            "1w",
            "1M",
        ],
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """
        Kline bars for a symbol. Klines are uniquely identified by their open time.

        API Docs:
            GET /fapi/v1/klines

        Request Weight:
            based on parameter LIMIT
            LIMIT    weight
            [1,100)  1
            [100, 500)   2
            [500, 1000]  5
            > 1000   10

        Args:
            symbol: Symbol name (e.g., BTCUSDT).
            interval: Kline interval.
            start_time: Start time in milliseconds.
            end_time: End time in milliseconds.
            limit: Number of klines to return. Default 500; max 1500.

        Returns:
            dict: API JSON response containing kline data.
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
            "/fapi/v1/klines",
            params=params,
        )

    async def get_24hr_ticker(
        self: HttpClientProtocol,
        symbol: str | None = None,
    ) -> dict[str, Any]:
        """
        24hr Ticker Price Change Statistics.

        24 hour rolling window price change statistics.

        API Docs:
            GET /fapi/v1/ticker/24hr

        Request Weight:
            - 1 for a single symbol
            - 40 when the symbol parameter is omitted

        Args:
            symbol: Symbol name (e.g., BTCUSDT).
            If omitted, tickers for all symbols will be returned (list).

        Returns:
            dict: 24hr ticker statistics for one symbol
            OR
            list[dict]: Array of ticker statistics for all symbols

        Example:
            await client.get_24hr_ticker(symbol="BTCUSDT")
            await client.get_24hr_ticker()  # all symbols
        """
        params: dict[str, Any] = {}
        if symbol is not None:
            params["symbol"] = symbol

        return await self.get("/fapi/v1/ticker/24hr", params=params)
