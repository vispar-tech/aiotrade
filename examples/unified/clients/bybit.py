import contextlib
import logging
from typing import Any, Literal

from aiotrade import BybitClient
from aiotrade.types.bybit import (
    CancelOrderParams,
    SetTradingStopParams,
)

from ..helpers import retry_async_function
from ..types import (
    UnifiedCancelOrderRequest,
    UnifiedMarginMode,
    UnifiedPendingOrder,
    UnifiedPlaceOrderRequest,
    UnifiedPlaceSpotOrderRequest,
    UnifiedPositionInfo,
    UnifiedSide,
    convert_unified_spot_to_bybit,
    convert_unified_to_bybit,
    unified_history_order_from_bybit,
    unified_position_info_from_bybit,
)

logger = logging.getLogger(__name__)


class UnifiedBybitClient:
    """Bybit client implementing ExchangeClient."""

    def __init__(
        self,
        account_display: str,
        api_key: str | None = None,
        api_secret: str | None = None,
        testnet: bool = False,
        demo: bool = False,
        referral_id: str | None = None,
        recv_window: int = 5000,
    ) -> None:
        """Initialize Bybit client wrapper."""
        self._account_display = account_display
        self._client = BybitClient(
            api_key=api_key,
            api_secret=api_secret,
            testnet=testnet,
            demo=demo,
            recv_window=recv_window,
            referral_id=referral_id,
        )

    # Account/Balance methods
    async def get_margin_mode(self, symbol: str | None) -> UnifiedMarginMode:
        """
        Query user margin mode.

        For Bybit, margin mode is global for the account (not per-symbol).
        No caching.
        """
        resp = await self._client.get_account_info()
        margin_mode_raw = resp.get("result", {}).get("marginMode")

        if margin_mode_raw == "ISOLATED_MARGIN":
            margin_mode = UnifiedMarginMode.ISOLATED
        elif margin_mode_raw == "REGULAR_MARGIN":
            margin_mode = UnifiedMarginMode.CROSS
        else:
            margin_mode = UnifiedMarginMode.OTHER

        return margin_mode

    async def update_margin_mode(
        self, symbol: str | None, mode: UnifiedMarginMode
    ) -> None:
        """Update user margin mode."""
        await self._client.set_margin_mode(set_margin_mode=mode.to_bybit())

    async def get_hedge_mode(self, symbol: str | None) -> bool | None:
        """
        Query whether hedge mode is enabled for the specified symbol.

        For Bybit, query the /v5/position/list endpoint with a symbol:
        - If a single object is returned with positionIdx == 0, hedge mode is off.
        - If two objects are returned with positionIdx 1 and 2, hedge mode is on.
        Always return one position by filtering down to the first found if present.
        """
        if not symbol:
            return None
        resp = await self._client.get_position_info(category="linear", symbol=symbol)
        positions = resp.get("result", {}).get("list", [])
        if not positions:
            return False
        # Always consider only the first position for the "one position" policy
        first_position = positions[0]
        if first_position.get("positionIdx") == 0:
            return False  # Hedge mode off

        return True if first_position.get("positionIdx") in (1, 2) else None

    async def set_hedge_mode(self, enabled: bool) -> None:
        """Enable or disable hedge mode."""
        await self._client.switch_position_mode(
            category="linear",
            coin="USDT",
            mode=3 if enabled else 0,
        )

    async def get_asset_mode(self) -> Literal["single", "union"] | None:
        """Query the current asset mode (e.g., 'USDT', 'multi-asset', etc)."""
        raise NotImplementedError(
            f"Don't use this method in {self.__class__.__name__} client"
        )

    async def set_asset_mode(self, mode: Literal["single", "union"]) -> None:
        """Set the asset mode (e.g., 'USDT', 'multi-asset', etc)."""
        raise NotImplementedError(
            f"Don't use this method in {self.__class__.__name__} client"
        )

    async def get_usdt_available_balance(self) -> float | None:
        """Get wallet balance from Bybit."""

        usdt_balance: float | None = None
        resp = await self._client.get_wallet_balance(
            account_type="UNIFIED", coin="USDT"
        )
        data = resp.get("result", {}).get("list", [])
        if data:
            entry = data[0]
            available = entry.get("totalAvailableBalance")
            try:
                usdt_balance = float(available) if available not in (None, "") else None
            except Exception:
                usdt_balance = None
            # Fallback: search in 'coin' details
            if usdt_balance is None:
                for coin in entry.get("coin", []):
                    if coin.get("coin") == "USDT":
                        with contextlib.suppress(Exception):
                            wb = float(coin.get("walletBalance") or 0)
                            im = float(coin.get("totalPositionIM") or 0)
                            upnl = float(coin.get("unrealisedPnl") or 0)
                            usdt_balance = wb - im + upnl
                        break
        if usdt_balance is None:
            logger.warning(
                "Could not find USDT available balance "
                "(wallet and fallback both failed). Response: %s",
                resp,
            )
        return usdt_balance

    async def get_spot_usdt_balance(self) -> float | None:
        """Get the spot USDT balance for the account."""

        usdt_balance: float | None = None
        resp = await self._client.get_wallet_balance(
            account_type="UNIFIED", coin="USDT"
        )
        data = resp.get("result", {}).get("list", [])
        if data:
            entry = data[0]
            available = entry.get("totalAvailableBalance")
            try:
                usdt_balance = float(available) if available not in (None, "") else None
            except Exception:
                usdt_balance = None
            # Fallback: search in 'coin' details
            if usdt_balance is None:
                for coin in entry.get("coin", []):
                    if coin.get("coin") == "USDT":
                        with contextlib.suppress(Exception):
                            wb = float(coin.get("walletBalance") or 0)
                            im = float(coin.get("totalPositionIM") or 0)
                            upnl = float(coin.get("unrealisedPnl") or 0)
                            calc = wb - im + upnl
                            if calc > 0:
                                usdt_balance = calc
                        break
        return usdt_balance

    # Position methods
    async def get_position_info(
        self,
        symbol: str | None = None,
    ) -> list[UnifiedPositionInfo]:
        """Get position info from Bybit."""
        response = await self._client.get_position_info(
            category="linear",
            symbol=symbol,
            settle_coin="USDT",
        )
        orders_response = await self._client.get_open_and_closed_orders(
            category="linear", settle_coin="USDT", limit=500
        )
        orders = orders_response.get("result", {}).get("list", [])

        return [
            unified_position_info_from_bybit(orders, x)
            for x in response.get("result", {}).get("list", [])
            if x["avgPrice"] != "" and x["side"] != ""
        ]

    # Order methods
    async def close_position(
        self, position: UnifiedPositionInfo, order: UnifiedPlaceOrderRequest
    ) -> dict[str, Any]:
        """Place an order on Bybit."""
        return await self._client.place_order(
            "linear", params=convert_unified_to_bybit(order)
        )

    async def place_spot_order(
        self, params: UnifiedPlaceSpotOrderRequest
    ) -> dict[str, Any]:
        """Place spot order on Bybit."""

        return await self._client.place_order(
            category="spot", params=convert_unified_spot_to_bybit(params)
        )

    async def get_spot_order_exec_qty(self, response: dict[str, Any]) -> float:
        """Get the executed quantity for a placed spot order (Bybit).

        Extracts the orderId from the Bybit response and get the executed qty.
        """
        order_id = response.get("result", {}).get("orderId")
        if not order_id:
            raise ValueError("order_id not presented in response")

        def _condition(result: dict[str, Any] | None) -> bool:
            return result is not None

        spot_order = await retry_async_function(
            condition=_condition,
            async_func=self._get_spot_order_by_id,
            max_attempts=5,
            delay_seconds=1.0,
            order_id=order_id,
        )
        return float(spot_order["cumExecQty"]) - float(spot_order["cumExecFee"])

    async def batch_place_order(
        self, has_existing_position: bool, requests: list[UnifiedPlaceOrderRequest]
    ) -> dict[str, Any]:
        """Batch place orders on Bybit."""

        return await self._client.batch_place_order(
            category="linear",
            orders=[convert_unified_to_bybit(order) for order in requests],
        )

    async def batch_cancel_order(
        self, requests: list[UnifiedCancelOrderRequest]
    ) -> None:
        """Batch cancel orders on Bybit."""
        converted_arrays: list[CancelOrderParams] = []
        for order in requests:
            obj = CancelOrderParams(symbol=order["symbol"])
            if order_id := order.get("order_id"):
                obj["order_id"] = str(order_id)
            if order_link_id := order.get("order_link_id"):
                obj["order_link_id"] = order_link_id
            converted_arrays.append(obj)

        await self._client.batch_cancel_order(
            category="linear", orders=converted_arrays
        )

    async def get_pending_orders(self) -> list[UnifiedPendingOrder]:
        """Get pending orders from Bybit."""
        orders_response = await self._client.get_open_and_closed_orders(
            category="linear", settle_coin="USDT", limit=500
        )
        return [
            unified_history_order_from_bybit(x)
            for x in orders_response.get("result", {}).get("list", [])
        ]

    # Trading methods
    async def set_trading_stop(
        self,
        symbol: str,
        take_profit: float | None = None,
        stop_loss: float | None = None,
        active_price: float | None = None,
        trailing_delivation: float | None = None,
        position: UnifiedPositionInfo | None = None,
        side: UnifiedSide | None = None,
        qty: float | None = None,
    ) -> None:
        """Set trading stop on Bybit."""
        params = SetTradingStopParams(
            symbol=symbol,
            position_idx=0,
            tpsl_mode="Full",
        )
        if stop_loss is not None:
            params["stop_loss"] = stop_loss
        if take_profit is not None:
            params["take_profit"] = take_profit
        if active_price is not None:
            params["active_price"] = active_price
        if trailing_delivation is not None:
            params["trailing_stop"] = trailing_delivation

        await self._client.set_trading_stop(
            category="linear",
            params=params,
        )

    async def set_leverage(self, symbol: str, leverage: float) -> None:
        """Set leverage on Bybit."""
        await self._client.set_leverage(
            category="linear",
            symbol=symbol,
            sell_leverage=leverage,
            buy_leverage=leverage,
        )

    async def _get_spot_order_by_id(self, order_id: str) -> dict[str, Any] | None:
        """Retrieve a spot order by its order ID from Bybit."""
        response = await self._client.get_open_and_closed_orders(
            category="spot", order_id=order_id, settle_coin="USDT"
        )
        return next(
            (
                x
                for x in response.get("result", {}).get("list", [])
                if x.get("orderId") == order_id
            ),
            None,
        )
