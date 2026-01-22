"""Position management HTTP methods."""

from typing import Any, Dict, Literal, Optional

from aiotrade._protocols import HttpClientProtocol
from aiotrade.types.bybit import SetTradingStopParams


class PositionMixin:
    """Mixin for position endpoints."""

    async def get_position_info(
        self: HttpClientProtocol,
        category: Literal["linear", "inverse", "option"],
        symbol: Optional[str] = None,
        base_coin: Optional[str] = None,
        settle_coin: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get position info from Bybit API.

        Query real-time position data, such as position size,
        cumulative realized PNL, etc.

        See:
            https://bybit-exchange.github.io/docs/v5/position

        Args:
            category: Product type (linear, inverse, option)
            symbol: Symbol name, like BTCUSDT, uppercase only
            base_coin: Base coin, uppercase only (option only)
            settle_coin: Settle coin (linear: either symbol or settleCoin required)
            limit: Limit for data size per page [1, 200]. Default: 20
            cursor: Cursor for pagination

        Returns:
            Dict with position info response containing list of positions.

        Raises:
            Any exception raised by the underlying HTTP request.
        """
        params: Dict[str, str | int] = {"category": category}

        if symbol is not None:
            params["symbol"] = symbol
        if base_coin is not None:
            params["baseCoin"] = base_coin
        if settle_coin is not None:
            params["settleCoin"] = settle_coin
        if limit is not None:
            params["limit"] = limit
        if cursor is not None:
            params["cursor"] = cursor

        return await self.get(
            "/v5/position/list",
            params=params,
            auth=True,
        )

    async def set_leverage(
        self: HttpClientProtocol,
        category: Literal["linear", "inverse"],
        symbol: str,
        buy_leverage: float,
        sell_leverage: float,
    ) -> Dict[str, Any]:
        """
        Set leverage from Bybit API.

        According to the risk limit, leverage affects the maximum position value
        that can be opened. The greater the leverage, the smaller the maximum
        position value that can be opened, and vice versa.

        See:
            https://bybit-exchange.github.io/docs/v5/position/leverage

        Args:
            category: Product type (linear, inverse)
            symbol: Symbol name, like BTCUSDT, uppercase only
            buy_leverage: Buy leverage [1, max leverage] as integer
            sell_leverage: Sell leverage [1, max leverage] as integer

        Returns:
            Dict with set leverage response (empty result object).

        Raises:
            Any exception raised by the underlying HTTP request.
        """
        params = {
            "category": category,
            "symbol": symbol,
            "buyLeverage": str(buy_leverage),
            "sellLeverage": str(sell_leverage),
        }

        return await self.post(
            "/v5/position/set-leverage",
            params=params,
            auth=True,
        )

    async def switch_position_mode(
        self: HttpClientProtocol,
        category: Literal["linear"],
        mode: Literal[0, 3],
        symbol: Optional[str] = None,
        coin: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Switch position mode from Bybit API.

        Supports switching between one-way mode and hedge mode for USDT perpetual.
        In one-way mode, you can only open one position on Buy or Sell side.
        In hedge mode, you can open both Buy and Sell side positions simultaneously.

        Priority for configuration: symbol > coin > system default

        See:
            https://bybit-exchange.github.io/docs/v5/position/position-mode

        Args:
            category: Product type (linear for USDT Contract)
            symbol: Symbol name, like BTCUSDT, uppercase only
            coin: Coin, uppercase only (either symbol or coin is required)
            mode: Position mode - 0: Merged Single (one-way), 3: Both Sides (hedge)

        Returns:
            Dict with switch position mode response (empty result object).

        Raises:
            Any exception raised by the underlying HTTP request.
            ValueError: If neither symbol nor coin is provided.
        """
        if not symbol and not coin:
            raise ValueError("Either symbol or coin must be provided")

        params: Dict[str, Any] = {
            "category": category,
            "mode": mode,
        }

        if symbol is not None:
            params["symbol"] = symbol
        if coin is not None:
            params["coin"] = coin

        return await self.post(
            "/v5/position/switch-mode",
            params=params,
            auth=True,
        )

    async def set_trading_stop(
        self: HttpClientProtocol,
        category: Literal["linear", "inverse"],
        params: SetTradingStopParams,
    ) -> Dict[str, Any]:
        """
        Set trading stop (take profit/stop loss) from Bybit API.

        Set the take profit, stop loss or trailing stop for the position.
        Supports both full position and partial position TP/SL orders.

        Note: Passing these parameters creates conditional orders internally.
        The system will cancel these orders if the position is closed.

        See:
            https://bybit-exchange.github.io/docs/v5/position/trading-stop

        Args:
            category: Product type (linear, inverse)
            params: Trading stop parameters as SetTradingStopParams TypedDict

        Returns:
            Dict with set trading stop response (empty result object).

        Raises:
            Any exception raised by the underlying HTTP request.
        """
        # Convert TypedDict to API parameters
        api_params: Dict[str, Any] = {"category": category}

        # Fields that need to be converted to string
        fields_to_str = {
            "take_profit",
            "stop_loss",
            "trailing_stop",
            "active_price",
            "tp_size",
            "sl_size",
            "tp_limit_price",
            "sl_limit_price",
        }

        # Map TypedDict fields to API parameter names
        field_mapping = {
            "symbol": "symbol",
            "tpsl_mode": "tpslMode",
            "position_idx": "positionIdx",
            "take_profit": "takeProfit",
            "stop_loss": "stopLoss",
            "trailing_stop": "trailingStop",
            "tp_trigger_by": "tpTriggerBy",
            "sl_trigger_by": "slTriggerBy",
            "active_price": "activePrice",
            "tp_size": "tpSize",
            "sl_size": "slSize",
            "tp_limit_price": "tpLimitPrice",
            "sl_limit_price": "slLimitPrice",
            "tp_order_type": "tpOrderType",
            "sl_order_type": "slOrderType",
        }

        # Add non-None parameters
        for field_name, api_name in field_mapping.items():
            value = params.get(field_name)
            if value is not None:
                if field_name in fields_to_str:
                    value = str(value)
                api_params[api_name] = value

        return await self.post(
            "/v5/position/trading-stop",
            params=api_params,
            auth=True,
        )

    async def set_auto_add_margin(self: HttpClientProtocol) -> Dict[str, Any]:
        """Set auto add margin."""
        raise NotImplementedError

    async def add_or_reduce_margin(self: HttpClientProtocol) -> Dict[str, Any]:
        """Add or reduce margin."""
        raise NotImplementedError

    async def get_closed_pnl(
        self: HttpClientProtocol,
        category: Literal["linear"],
        symbol: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get closed PnL from Bybit API.

        Query user's closed profit and loss records.
        Returns records for the last 7 days by default.

        See:
            https://bybit-exchange.github.io/docs/v5/position/close-pnl

        Args:
            category: Product type (linear for USDT/USDC contracts)
            symbol: Symbol name, like BTCUSDT, uppercase only
            start_time: Start timestamp (ms). Default returns last 7 days
            end_time: End timestamp (ms)
            limit: Limit for data size per page [1, 100]. Default: 50
            cursor: Cursor for pagination

        Returns:
            Dict with closed PnL response containing list of PnL records.

        Raises:
            Any exception raised by the underlying HTTP request.
        """
        params: Dict[str, str | int] = {"category": category}

        if symbol is not None:
            params["symbol"] = symbol
        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time
        if limit is not None:
            params["limit"] = limit
        if cursor is not None:
            params["cursor"] = cursor

        return await self.get(
            "/v5/position/closed-pnl",
            params=params,
            auth=True,
        )

    async def get_closed_options_positions(self: HttpClientProtocol) -> Dict[str, Any]:
        """Get closed options positions (6 months)."""
        raise NotImplementedError

    async def move_position(self: HttpClientProtocol) -> Dict[str, Any]:
        """Move position."""
        raise NotImplementedError

    async def get_move_position_history(self: HttpClientProtocol) -> Dict[str, Any]:
        """Get move position history."""
        raise NotImplementedError

    async def confirm_new_risk_limit(self: HttpClientProtocol) -> Dict[str, Any]:
        """Confirm new risk limit."""
        raise NotImplementedError
