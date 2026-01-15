from typing import Any, Dict, Literal, Optional

from aiotrade._protocols import HttpClientProtocol
from aiotrade.types.bybit import InstrumentStatus, SymbolType


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

    async def get_instruments_info(
        self: HttpClientProtocol,
        category: Literal["spot", "linear", "inverse", "option"],
        symbol: Optional[str] = None,
        symbol_type: Optional[SymbolType] = None,
        status: Optional[InstrumentStatus] = None,
        base_coin: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get instruments info from Bybit API.

        Query for the instrument specification of online trading pairs.

        See:
            https://bybit-exchange.github.io/docs/v5/market/instrument

        Args:
            category: Product type. One of: "spot", "linear", "inverse", "option"
            symbol: Symbol name (e.g. "BTCUSDT"), uppercase only
            symbol_type: Region to which the trading pair belongs
                (for linear/inverse/spot)
            status: Symbol status filter. One of: "Trading", "PreLaunch", "Delivering"
            base_coin: Base coin, uppercase only (applies to linear/inverse/option)
            limit: Limit for data size per page [1, 1000]. Default: 500
            cursor: Cursor for pagination. Use nextPageCursor from response

        Returns:
            Dict with instruments info response as received from Bybit API.

        Raises:
            Any exception raised by the underlying HTTP request.
        """
        params: Dict[str, int | str] = {"category": category}

        if symbol is not None:
            params["symbol"] = symbol
        if symbol_type is not None:
            params["symbolType"] = symbol_type
        if status is not None:
            params["status"] = status
        if base_coin is not None:
            params["baseCoin"] = base_coin
        if limit is not None:
            params["limit"] = limit
        if cursor is not None:
            params["cursor"] = cursor

        return await self.get(
            "/v5/market/instruments-info",
            params=params,
        )

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
