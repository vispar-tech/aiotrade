from typing import Any, Dict, Optional

from aiotrade._protocols import HttpClientProtocol


class MarketMixin:
    """Market data methods for BingX swap API client.

    This mixin provides methods for retrieving market data and prices
    for swap trading.
    """

    async def get_swap_contracts(
        self: "HttpClientProtocol",
        symbol: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve contract information for BingX Perpetual Swaps.

        GET /openApi/swap/v2/quote/contracts

        https://bingx-api.github.io/docs-v3/#/en/Swap/Market%20Data/USDT-M%20Perp%20Futures%20symbols

        Args:
            symbol: Optional; contract symbol
                (e.g., "BTC-USDT"). If None, returns all contracts.

        Returns:
            Dict[str, Any]: API response containing contracts information.
        """
        params: Dict[str, Any] = {}
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
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve Kline/Candlestick data for BingX Perpetual Swap contracts.

        GET /openApi/swap/v3/quote/klines

        https://bingx-api.github.io/docs-v3/#/en/Swap/Market%20Data/Kline%2FCandlestick%20Data

        Args:
            symbol (str): The trading pair symbol (e.g., "BTC-USDT"),
                must contain a hyphen.
            interval (str): Kline interval (e.g. "1m", "5m", "1h", "1d").
            start_time (Optional[int]): Start timestamp (ms), inclusive. (optional)
            end_time (Optional[int]): End timestamp (ms), inclusive. (optional)
            limit (Optional[int]): How many klines to return
                (default 500, max 1440). (optional)

        Returns:
            Dict[str, Any]: API response with candlestick/kline data.
        """
        params: Dict[str, Any] = {
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
