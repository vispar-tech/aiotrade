from typing import Any

from aiotrade._protocols import HttpClientProtocol
from aiotrade.clients.kucoin._consts import base_url
from aiotrade.types.kucoin import MarginMode


class PositionMixin:
    async def get_margin_mode(self: HttpClientProtocol, symbol: str) -> dict[str, Any]:
        """
        Get the margin mode for a specific contract symbol.

        Args:
            symbol (str): Symbol of the contract (e.g., "XBTUSDTM").

        Returns:
            dict[str, Any]: KuCoin API response. Example:
                {
                    "code": "200000",
                    "data": {
                        "symbol": "XBTUSDTM",
                        "marginMode": "ISOLATED"  # or "CROSS"
                    }
                }
        """
        return await self.get(
            "/api/v2/position/getMarginMode",
            params={"symbol": symbol},
            auth=True,
            base_url=base_url("futures"),
        )

    async def get_position_mode(self: HttpClientProtocol) -> dict[str, Any]:
        """
        Get the position mode for the account.

        Returns:
            dict[str, Any]: KuCoin API response. Example:
                {
                    "code": "200000",
                    "data": {
                        "positionMode": 1  # 0: one-way mode, 1: hedge mode
                    }
                }
        """
        return await self.get(
            "/api/v2/position/getPositionMode",
            auth=True,
            base_url=base_url("futures"),
        )

    async def switch_position_mode(
        self: HttpClientProtocol,
        position_mode: bool,
    ) -> dict[str, Any]:
        """
        Switch position mode (one-way or hedge) for all futures pairs.

        Args:
            position_mode (bool): Position mode setting.
                - False: "0" (one-way mode, one-way position)
                - True:  "1" (hedge mode, two-way position)

        Returns:
            dict[str, Any]: KuCoin API response. Example:
                {
                    "code": "200000",
                    "data": {
                        "positionMode": "0"  # "0": one-way mode,
                                             # "1": hedge mode
                    }
                }
        """
        mode = "1" if position_mode else "0"

        return await self.post(
            "/api/v2/position/switchPositionMode",
            params={"positionMode": mode},
            auth=True,
            base_url=base_url("futures"),
        )

    async def switch_margin_mode(
        self: HttpClientProtocol,
        symbol: str,
        margin_mode: MarginMode,
    ) -> dict[str, Any]:
        """
        Switch the margin mode for a given contract symbol.

        Args:
            symbol (str): Contract symbol (e.g., "XBTUSDTM").
            margin_mode (MarginMode): New margin mode.

        Returns:
            dict[str, Any]: KuCoin API response. Example:
                {
                    "code": "200000",
                    "data": {
                        "symbol": "XBTUSDTM",
                        "marginMode": "ISOLATED"
                    }
                }
        """
        return await self.post(
            "/api/v2/position/changeMarginMode",
            params={
                "symbol": symbol,
                "marginMode": margin_mode,
            },
            auth=True,
            base_url=base_url("futures"),
        )

    async def batch_switch_margin_mode(
        self: HttpClientProtocol,
        margin_mode: MarginMode,
        symbols: list[str],
    ) -> dict[str, Any]:
        """
        Batch modify the margin mode of the given contract symbols.

        Args:
            margin_mode (MarginMode): Target margin mode ("ISOLATED" or "CROSS")
            symbols (list[str]): List of contract symbols
                                 (e.g., ["XBTUSDTM", "ETHUSDTM"])

        Returns:
            dict[str, Any]: KuCoin API response. Example:
                {
                    "code": "200000",
                    "data": {
                        "marginMode": {
                            "ETHUSDTM": "ISOLATED",
                            "XBTUSDTM": "CROSS"
                        },
                        "errors": [
                            {
                                "code": "50002",
                                "msg": "exist.order.or.position",
                                "symbol": "XBTUSDTM"
                            }
                        ]
                    }
                }
        """
        return await self.post(
            "/api/v2/position/batchChangeMarginMode",
            params={
                "marginMode": margin_mode,
                "symbols": symbols,
            },
            auth=True,
            base_url=base_url("futures"),
        )

    async def get_position_details(
        self: HttpClientProtocol,
        symbol: str,
    ) -> dict[str, Any]:
        """
        Get the position details of a specified position.

        Args:
            symbol (str): Symbol of the contract, e.g. 'XBTUSDTM', 'ETHUSDTM'

        Returns:
            dict[str, Any]: KuCoin API response.
        """
        return await self.get(
            "/api/v2/position",
            params={"symbol": symbol},
            auth=True,
            base_url=base_url("futures"),
        )

    async def get_positions(
        self: HttpClientProtocol,
        currency: str | None = None,
    ) -> dict[str, Any]:
        """
        Get Position List.

        Get the list of position details for the account.
        If `currency` is provided, filter by specified
        quote currency (e.g. "USDT", "XBT").
        Otherwise, returns all positions.

        Args:
            currency (str, optional): Quote currency code.
                Query all positions if not provided.

        Returns:
            dict[str, Any]: KuCoin API response.
        """
        params: dict[str, Any] = {}
        if currency is not None:
            params["currency"] = currency
        return await self.get(
            "/api/v1/positions",
            params=params,
            auth=True,
            base_url=base_url("futures"),
        )

    async def get_positions_history(
        self: HttpClientProtocol,
        symbol: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        page_size: int | None = None,
        page: int | None = None,
    ) -> dict[str, Any]:
        """
        Get Positions History.

        Query position history information records within a time window of up to 7 days.

        Args:
            symbol (str, optional): Contract symbol (e.g. 'XBTUSDTM', 'ETHUSDTM').
            start_time (int, optional): Closing start time (milliseconds since epoch).
            end_time (int, optional): Closing end time (milliseconds since epoch).
            page_size (int, optional): Number of results per page (max 200, default 10).
            page (int, optional): Page number (default 1).

        Returns:
            dict[str, Any]: KuCoin API response.
        """
        params: dict[str, Any] = {}
        if symbol is not None:
            params["symbol"] = symbol
        if start_time is not None:
            params["from"] = start_time
        if end_time is not None:
            params["to"] = end_time
        if page_size is not None:
            params["limit"] = page_size
        if page is not None:
            params["pageId"] = page

        return await self.get(
            "/api/v1/history-positions",
            params=params,
            auth=True,
            base_url=base_url("futures"),
        )

    async def get_isolated_margin_risk_limit(
        self: HttpClientProtocol,
        symbol: str,
    ) -> dict[str, Any]:
        """
        Get Isolated Margin Risk Limit.

        This interface can be used to obtain information about risk limit level
        of a specific contract (only valid for Isolated Margin).

        Args:
            symbol (str): Symbol of the contract, e.g. 'XBTUSDTM', 'ETHUSDTM'

        Returns:
            dict[str, Any]: KuCoin API response.

        Example KuCoin response:
            {
              "code": "200000",
              "data": [
                {
                  "symbol": "XBTUSDTM",
                  "level": 1,
                  "maxRiskLimit": 100000,
                  "minRiskLimit": 0,
                  "maxLeverage": 125,
                  "initialMargin": 0.008,
                  "maintainMargin": 0.004
                },
                ...
              ]
            }
        """
        return await self.get(
            f"/api/v1/contracts/risk-limit/{symbol}",
            auth=True,
            base_url=base_url("futures"),
        )
