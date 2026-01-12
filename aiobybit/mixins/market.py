"""Market data HTTP methods."""

from typing import Any, Dict, Literal, Optional

from ..protocols import HttpClientProtocol


class MarketMixin:
    """Mixin for market data endpoints."""

    async def get_server_time(self: HttpClientProtocol) -> Dict[str, Any]:
        """Get Bybit server time.

        Returns:
            Server time response containing timeSecond and timeNano.
        """
        return await self.get("/v5/market/time")

    async def get_kline(
        self: HttpClientProtocol,
        symbol: str,
        interval: str,
        category: Optional[Literal["spot", "linear", "inverse"]] = None,
        start: Optional[int] = None,
        end: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get historical klines (candlesticks).

        Args:
            symbol: Symbol name (e.g., BTCUSDT).
            interval: Kline interval (1,3,5,15,30,60,120,240,360,720,D,W,M).
            category: Product type ("spot", "linear", "inverse"). Defaults to
                linear if not provided.
            start: Start timestamp in milliseconds.
            end: End timestamp in milliseconds.
            limit: Number of records per page (1-1000). Default: 200.

        Returns:
            Kline data response containing symbol, category, and list of candles.
            Each candle contains [startTime, openPrice, highPrice, lowPrice,
            closePrice, volume, turnover].
        """
        params: Dict[str, Any] = {
            "symbol": symbol,
            "interval": interval,
        }

        if category is not None:
            params["category"] = category
        if start is not None:
            params["start"] = start
        if end is not None:
            params["end"] = end
        if limit is not None:
            params["limit"] = limit

        return await self.get("/v5/market/kline", params=params)

    async def get_mark_price_kline(self: HttpClientProtocol) -> Dict[str, Any]:
        """Get mark price kline."""
        raise NotImplementedError

    async def get_index_price_kline(self: HttpClientProtocol) -> Dict[str, Any]:
        """Get index price kline."""
        raise NotImplementedError

    async def get_premium_index_price_kline(self: HttpClientProtocol) -> Dict[str, Any]:
        """Get premium index price kline."""
        raise NotImplementedError

    async def get_instruments_info(self: HttpClientProtocol) -> Dict[str, Any]:
        """Get instruments info."""
        raise NotImplementedError

    async def get_orderbook(self: HttpClientProtocol) -> Dict[str, Any]:
        """Get orderbook."""
        raise NotImplementedError

    async def get_rpi_orderbook(self: HttpClientProtocol) -> Dict[str, Any]:
        """Get RPI orderbook."""
        raise NotImplementedError

    async def get_tickers(self: HttpClientProtocol) -> Dict[str, Any]:
        """Get tickers."""
        raise NotImplementedError

    async def get_funding_rate_history(self: HttpClientProtocol) -> Dict[str, Any]:
        """Get funding rate history."""
        raise NotImplementedError

    async def get_recent_public_trades(self: HttpClientProtocol) -> Dict[str, Any]:
        """Get recent public trades."""
        raise NotImplementedError

    async def get_open_interest(self: HttpClientProtocol) -> Dict[str, Any]:
        """Get open interest."""
        raise NotImplementedError

    async def get_historical_volatility(self: HttpClientProtocol) -> Dict[str, Any]:
        """Get historical volatility."""
        raise NotImplementedError

    async def get_insurance_pool(self: HttpClientProtocol) -> Dict[str, Any]:
        """Get insurance pool."""
        raise NotImplementedError

    async def get_risk_limit(self: HttpClientProtocol) -> Dict[str, Any]:
        """Get risk limit."""
        raise NotImplementedError

    async def get_delivery_price(self: HttpClientProtocol) -> Dict[str, Any]:
        """Get delivery price."""
        raise NotImplementedError

    async def get_new_delivery_price(self: HttpClientProtocol) -> Dict[str, Any]:
        """Get new delivery price."""
        raise NotImplementedError

    async def get_long_short_ratio(self: HttpClientProtocol) -> Dict[str, Any]:
        """Get long short ratio."""
        raise NotImplementedError

    async def get_index_price_components(self: HttpClientProtocol) -> Dict[str, Any]:
        """Get index price components."""
        raise NotImplementedError

    async def get_order_price_limit(self: HttpClientProtocol) -> Dict[str, Any]:
        """Get order price limit."""
        raise NotImplementedError

    async def get_adl_alert(self: HttpClientProtocol) -> Dict[str, Any]:
        """Get ADL alert."""
        raise NotImplementedError

    async def get_fee_group_structure(self: HttpClientProtocol) -> Dict[str, Any]:
        """Get fee group structure."""
        raise NotImplementedError
