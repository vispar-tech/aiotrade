import asyncio
import logging
from typing import Any, Literal

from aiohttp import ClientResponseError

from aiotrade import BingxClient
from aiotrade.types.bingx import PlaceSwapOrderParams
from aiotrade.unified.converters.pending_order import unified_pending_order_from_bingx
from aiotrade.unified.converters.place.futures import (
    convert_unified_place_order_to_bingx,
)
from aiotrade.unified.converters.place.spot import (
    convert_unified_place_spot_order_to_bingx,
)
from aiotrade.unified.converters.position import unified_position_info_from_bingx
from aiotrade.unified.types import (
    UnifiedAssetMode,
    UnifiedCancelOrderRequest,
    UnifiedMarginMode,
    UnifiedPendingOrder,
    UnifiedPlaceOrderRequest,
    UnifiedPlaceSpotOrderRequest,
    UnifiedPositionInfo,
    UnifiedSide,
)

logger = logging.getLogger("aiotrade.unified")
SET_TRADING_STOP_MAX_RETRIES = 3
SET_TRADING_STOP_RETRY_DELAY = 2  # seconds


class UnifiedBingxClient:
    """Bingx client implementing ExchangeClient."""

    def __init__(
        self,
        account_display: str,
        api_key: str | None = None,
        api_secret: str | None = None,
        demo: bool = False,
        recv_window: int = 5000,
    ) -> None:
        """Initialize Bingx client wrapper."""
        self._account_display = account_display
        self._client = BingxClient(
            api_key=api_key, api_secret=api_secret, demo=demo, recv_window=recv_window
        )

    # Account/Balance methods
    async def get_margin_mode(self, symbol: str | None) -> UnifiedMarginMode:
        """
        Query user margin mode.

        For Bingx, margin mode is per-symbol (but with a default if None).
        """
        if not symbol:
            raise ValueError(
                "symbol must be specified when updating margin mode on BingX"
            )
        resp = await self._client.get_swap_margin_type(symbol=symbol)
        margin_mode_raw = resp.get("data", {}).get("marginType")
        if margin_mode_raw is None:
            raise ValueError("marginType not found in response")

        if margin_mode_raw == "CROSSED":
            margin_mode = UnifiedMarginMode.CROSS
        elif margin_mode_raw == "ISOLATED":
            margin_mode = UnifiedMarginMode.ISOLATED
        else:
            margin_mode = UnifiedMarginMode.OTHER

        return margin_mode

    async def update_margin_mode(
        self, symbol: str | None, mode: UnifiedMarginMode
    ) -> None:
        """
        Update user margin mode.

        For Bingx, must specify symbol (None will update for all if supported).
        """
        mode_bingx = mode.to_bingx()
        if not symbol:
            raise ValueError(
                "symbol must be specified when updating margin mode on BingX"
            )

        await self._client.change_swap_margin_type(
            symbol=symbol, margin_type=mode_bingx
        )

    async def get_hedge_mode(self, symbol: str | None) -> bool | None:
        """Query whether hedge mode is enabled on Bingx."""
        resp = await self._client.get_swap_position_mode()
        hedge_mode = resp.get("data", {}).get("dualSidePosition")
        if hedge_mode is not None:
            return hedge_mode == "true"  # type: ignore[no-any-return]
        return None

    async def set_hedge_mode(self, enabled: bool) -> None:
        """Enable or disable hedge mode on Bingx."""
        await self._client.set_swap_position_mode(dual_side_position=enabled)

    async def get_asset_mode(self) -> UnifiedAssetMode | None:
        """Query the current asset mode (e.g., 'USDT', 'multi-asset', etc)."""
        raise NotImplementedError(
            f"Don't use this method in {self.__class__.__name__} client"
        )

    async def set_asset_mode(self, mode: UnifiedAssetMode) -> None:
        """Set the asset mode (e.g., 'USDT', 'multi-asset', etc)."""
        raise NotImplementedError(
            f"Don't use this method in {self.__class__.__name__} client"
        )

    # Account/Balance methods
    async def get_usdt_available_balance(self) -> float | None:
        """Get wallet balance from Bingx."""
        usdt_balance: float | None = None
        try:
            resp = await self._client.get_swap_account_balance()
            for entry in resp.get("data", []):
                if entry["asset"] == "USDT" or entry["asset"] == "VST":
                    try:
                        usdt_balance = float(entry["availableMargin"])
                        break
                    except Exception as e:
                        logger.exception(
                            "Failed to parse availableMargin "
                            "for asset %s from Bingx: %s",
                            entry.get("asset"),
                            e,
                        )
                        usdt_balance = None
        except Exception as e:
            logger.error("Error getting Bingx swap account balance: %s", e)
            usdt_balance = None
        return usdt_balance

    async def get_spot_usdt_balance(self) -> float | None:
        """Get the spot USDT balance for the account."""
        usdt_balance: float | None = None
        resp = await self._client.get_spot_account_assets()
        balances = resp.get("data", {}).get("balances", [])
        if len(balances) == 0:
            return 0
        for entry in balances:
            if entry["asset"] == "USDT" or entry["asset"] == "VST":
                try:
                    usdt_balance = float(entry["free"])
                    break
                except Exception:
                    usdt_balance = None
        return usdt_balance

    # Position methods
    async def get_position_info(
        self, symbol: str | None = None
    ) -> list[UnifiedPositionInfo]:
        """Get position info from Bingx."""
        open_orders_response = await self._client.get_swap_open_orders(symbol)
        open_orders_list = open_orders_response.get("data", {}).get("orders", [])
        response = await self._client.get_swap_positions(symbol=symbol)
        return [
            unified_position_info_from_bingx(self._account_display, open_orders_list, x)
            for x in response.get("data", [])
        ]

    # Order methods
    async def close_position(
        self, position: UnifiedPositionInfo, order: UnifiedPlaceOrderRequest
    ) -> dict[str, Any]:
        """Place an order on Bingx."""
        return await self._client.place_swap_batch_orders(
            batch_orders=[
                PlaceSwapOrderParams(
                    symbol=position["symbol"],
                    order_type="MARKET",
                    side="BUY" if position["side"] == UnifiedSide.SHORT else "SELL",
                    position_side="BOTH",
                    reduce_only=True,
                    quantity=position["size"],
                )
            ]
        )

    async def place_spot_order(
        self, params: UnifiedPlaceSpotOrderRequest
    ) -> dict[str, Any]:
        """Place spot order on Bingx."""
        return await self._client.place_spot_order(
            params=convert_unified_place_spot_order_to_bingx(params)
        )

    async def get_spot_order_exec_qty(self, response: dict[str, Any]) -> float:
        """Get the executed quantity for a placed spot order."""
        try:
            return float(response.get("data", {}).get("executedQty"))
        except (TypeError, ValueError, AttributeError) as e:
            raise ValueError("Failed to get executed quantity from response") from e

    async def batch_place_order(
        self, has_existing_position: bool, requests: list[UnifiedPlaceOrderRequest]
    ) -> dict[str, Any]:
        """Batch place orders on Bingx."""
        return await self._client.place_swap_batch_orders(
            batch_orders=[
                convert_unified_place_order_to_bingx(order) for order in requests
            ]
        )

    async def batch_cancel_order(
        self, requests: list[UnifiedCancelOrderRequest]
    ) -> None:
        """Batch cancel orders on Bingx."""
        # Step 1: Map <symbol> -> list of requests
        symbol_to_requests: dict[str, list[UnifiedCancelOrderRequest]] = {}
        for order in requests:
            symbol = order["symbol"]
            symbol_to_requests.setdefault(symbol, []).append(order)

        # Step 2: For each symbol, collect order IDs/client order IDs
        for symbol, orders in symbol_to_requests.items():
            order_id_list: list[int] = []
            client_order_id_list: list[str] = []

            for order in orders:
                if order_id := order.get("order_id"):
                    order_id_list.append(int(order_id))
                if order_link_id := order.get("order_link_id"):
                    client_order_id_list.append(str(order_link_id))

            order_ids = order_id_list if order_id_list else None
            client_order_ids = client_order_id_list if client_order_id_list else None

            await self._client.cancel_swap_batch_orders(
                symbol=symbol,
                order_id_list=order_ids,
                client_order_id_list=client_order_ids,
            )

    async def get_pending_orders(self) -> list[UnifiedPendingOrder]:
        """Get pending orders from Bingx."""
        orders_response = await self._client.get_swap_open_orders()
        return [
            unified_pending_order_from_bingx(x)
            for x in orders_response.get("data", {}).get("orders", [])
        ]

    # Trading methods
    async def _cancel_trading_stop_orders(
        self,
        symbol: str,
        position: UnifiedPositionInfo | None,
        take_profit: float | None,
        stop_loss: float | None,
        active_price: float | None,
        trailing_delivation: float | None,
    ) -> None:
        """Cancel TP/SL/Trailing orders that need to be replaced."""
        if position is None:
            return
        if not (additional := position.get("additional")):
            logger.warning(
                "%s set_trading_stop: Provided position has no "
                "'additional' field for symbol=%s",
                self._account_display,
                symbol,
            )
            return

        cancel_orders: list[UnifiedCancelOrderRequest] = []

        if len(additional["matching_tp_orders"]) and (
            take_profit is not None
            or (trailing_delivation is not None and active_price is not None)
        ):
            cancel_orders.extend(
                [
                    UnifiedCancelOrderRequest(
                        symbol=order["symbol"], order_id=order["orderId"]
                    )
                    for order in additional["matching_tp_orders"]
                ]
            )

        if len(additional["matching_sl_orders"]) and stop_loss is not None:
            cancel_orders.extend(
                [
                    UnifiedCancelOrderRequest(
                        symbol=order["symbol"], order_id=order["orderId"]
                    )
                    for order in additional["matching_sl_orders"]
                ]
            )

        if len(additional["matching_trailing_orders"]) and (
            trailing_delivation is not None and active_price is not None
        ):
            cancel_orders.extend(
                [
                    UnifiedCancelOrderRequest(
                        symbol=order["symbol"], order_id=order["orderId"]
                    )
                    for order in additional["matching_trailing_orders"]
                ]
            )

        if cancel_orders:
            logger.info(
                "%s set_trading_stop: Cancelling %d TP/SL/Trailing orders "
                "for symbol=%s. Order IDs: %s",
                self._account_display,
                len(cancel_orders),
                symbol,
                [order.get("order_id") for order in cancel_orders],
            )
            try:
                await self.batch_cancel_order(cancel_orders)
                logger.info(
                    "%s set_trading_stop: Successfully cancelled orders for symbol=%s",
                    self._account_display,
                    symbol,
                )
            except Exception as exc:
                logger.warning(
                    "%s set_trading_stop: Failed to cancel orders for symbol=%s: %s",
                    self._account_display,
                    symbol,
                    exc,
                )

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
        """Set trading stop on Bingx."""
        await self._cancel_trading_stop_orders(
            symbol=symbol,
            position=position,
            take_profit=take_profit,
            stop_loss=stop_loss,
            active_price=active_price,
            trailing_delivation=trailing_delivation,
        )

        order_side: Literal["SELL", "BUY"]
        if position is not None:
            order_side = "SELL" if position["side"] == UnifiedSide.LONG else "BUY"
            order_qty = position["size"]
        elif side is not None and qty is not None:
            order_side = "SELL" if side == UnifiedSide.LONG else "BUY"
            order_qty = qty
        else:
            raise ValueError(
                "set_trading_stop: Either a valid 'position' or both 'side' "
                "and 'qty' must be provided for Bingx."
            )

        batch_orders: list[PlaceSwapOrderParams] = []

        if take_profit is not None:
            batch_orders.append(
                PlaceSwapOrderParams(
                    symbol=symbol,
                    quantity=order_qty,
                    position_side="BOTH",
                    side=order_side,
                    order_type="TAKE_PROFIT_MARKET",
                    working_type="CONTRACT_PRICE",
                    price=take_profit,
                    stop_price=take_profit,
                )
            )
        if stop_loss is not None:
            batch_orders.append(
                PlaceSwapOrderParams(
                    symbol=symbol,
                    quantity=order_qty,
                    position_side="BOTH",
                    side=order_side,
                    order_type="STOP_MARKET",
                    working_type="CONTRACT_PRICE",
                    price=stop_loss,
                    stop_price=stop_loss,
                )
            )
        if trailing_delivation is not None and active_price is not None:
            batch_orders.append(
                PlaceSwapOrderParams(
                    symbol=symbol,
                    quantity=order_qty,
                    position_side="BOTH",
                    side=order_side,
                    order_type="TRAILING_TP_SL",
                    working_type="CONTRACT_PRICE",
                    price_rate=trailing_delivation,
                    activation_price=active_price,
                )
            )

        errors: list[Exception] = []

        for i in range(0, len(batch_orders), 5):
            batch = batch_orders[i : i + 5]
            retries = 0
            while retries < SET_TRADING_STOP_MAX_RETRIES:
                try:
                    await self._client.place_swap_batch_orders(batch)
                    break  # Success, break out of retry loop
                except ClientResponseError as cre:
                    logger.warning(
                        "%s ClientResponseError while placing "
                        "plan order batch for %s (attempt %d/%d): %s",
                        self._account_display,
                        [order.get("symbol") for order in batch],
                        retries + 1,
                        SET_TRADING_STOP_MAX_RETRIES,
                        cre,
                    )
                    retries += 1
                    if retries >= SET_TRADING_STOP_MAX_RETRIES:
                        errors.append(cre)
                        break
                    await asyncio.sleep(SET_TRADING_STOP_RETRY_DELAY)
                except Exception as e:
                    logger.error(
                        "%s Failed to place plan order batch for %s: %s",
                        self._account_display,
                        [order.get("symbol") for order in batch],
                        e,
                    )
                    errors.append(e)
                    break  # For non-retryable errors, no retry
        if errors:
            raise errors[0]

    async def set_leverage(self, symbol: str, leverage: float) -> None:
        """Set leverage on Bingx."""
        await self._client.set_swap_leverage(
            symbol=symbol, side="BOTH", leverage=int(leverage)
        )
