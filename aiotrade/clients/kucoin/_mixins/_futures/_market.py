from typing import Any, Literal

from aiotrade._protocols import HttpClientProtocol
from aiotrade.clients.kucoin._consts import base_url

FuturesGranularity = Literal[1, 5, 15, 30, 60, 120, 240, 480, 720, 1440, 10080]


class MarketMixin:
    async def get_all_symbols(self: HttpClientProtocol) -> dict[str, Any]:
        """
        Get all symbols (contracts) tradable on KuCoin Futures.

        Returns:
            dict[str, Any]: Response with "code" and "data" containing a list
                of contract objects.

        Endpoint:
            GET /api/v1/contracts/active

        Example:
            result = await client.get_all_symbols()
            print(result['data'])

        """
        return await self.get(
            "/api/v1/contracts/active",
            base_url=base_url("futures"),
        )

    async def get_all_tickers(self: HttpClientProtocol) -> dict[str, Any]:
        """
        Get all tickers for KuCoin Futures.

        This endpoint returns "last traded price/size", "best bid/ask price/size",
        etc. of all symbols.

        Endpoint:
            GET /api/v1/allTickers

        Example:
            result = await client.get_all_tickers()
            print(result['data'])

        Returns:
            dict[str, Any]: Response with "code" and "data", where "data" is a
                list of tickers.
        """
        return await self.get(
            "/api/v1/allTickers",
            base_url=base_url("futures"),
        )

    async def get_klines(
        self: HttpClientProtocol,
        symbol: str,
        interval: FuturesGranularity,
        time_from: int | None = None,
        time_to: int | None = None,
    ) -> dict[str, Any]:
        """
        Get klines (candlestick data) for a contract trading symbol on KuCoin Futures.

        Args:
            symbol (str): Symbol of the contract, e.g., "XBTUSDTM".
            interval (FuturesGranularity): Candlestick timeframe in minutes.
                Allowed values: 1, 5, 15, 30, 60, 120, 240, 480, 720, 1440, 10080.
            time_from (int, optional): Start time in milliseconds (Unix ms).
            time_to (int, optional): End time in milliseconds (Unix ms).

        Returns:
            dict[str, Any]: Response with "code" and "data" (list of klines).

        Endpoint:
            GET /api/v1/kline/query

        Example:
            result = await client.get_klines("XBTUSDTM", 1)
            print(result['data'])
        """
        params: dict[str, Any] = {
            "symbol": symbol,
            "granularity": interval,
        }
        if time_from is not None:
            params["from"] = time_from
        if time_to is not None:
            params["to"] = time_to

        return await self.get(
            "/api/v1/kline/query",
            params=params,
            base_url=base_url("futures"),
        )

    async def get_server_time(self: HttpClientProtocol) -> dict[str, Any]:
        """
        Get server time (KuCoin Futures).

        Retrieves the API server's current Unix timestamp in milliseconds.

        Endpoint:
            GET /api/v1/timestamp

        Returns:
            dict[str, Any]: Response with "code" (str) and "data"
                (int, server time in ms).

        Example:
            result = await client.get_server_time()
            print(result['data'])  # 1729260030774
        """
        return await self.get(
            "/api/v1/timestamp",
            base_url=base_url("futures"),
        )

    async def get_service_status(self: HttpClientProtocol) -> dict[str, Any]:
        """
        Get service status (KuCoin Futures).

        Retrieves the status of the Futures service. The status may be:
            - "open": normal transaction
            - "close": stop trading/maintenance
            - "cancelonly": can only cancel orders, but not place new ones.

        Endpoint:
            GET /api/v1/status

        Returns:
            dict[str, Any]: Response with "code" (str) and "data" (dict) with
                keys "msg" and "status".

        Example:
            result = await client.get_service_status()
            print(result['data'])  # Example: {'msg': '', 'status': 'open'}
        """
        return await self.get(
            "/api/v1/status",
            base_url=base_url("futures"),
        )
