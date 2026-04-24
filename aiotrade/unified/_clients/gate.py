import asyncio
import logging
from collections.abc import Coroutine
from typing import Any

from aiotrade import ExchangeResponseError, GateClient
from aiotrade.types.gate import (
    FuturesPlaceOrder,
    FuturesPlaceTrailingOrder,
    FuturesPriceTriggeredOrder,
    UnifiedMode,
    UnifiedModeSet,
)
from aiotrade.unified.converters.pending_order import unified_pending_order_from_gate
from aiotrade.unified.converters.place.futures import (
    convert_unified_place_order_to_gate,
)
from aiotrade.unified.converters.position import unified_position_info_from_gate
from aiotrade.unified.types import (
    UnifiedAssetMode,
    UnifiedCancelOrderRequest,
    UnifiedMarginMode,
    UnifiedOrderType,
    UnifiedPendingOrder,
    UnifiedPlaceOrderRequest,
    UnifiedPlaceSpotOrderRequest,
    UnifiedPositionInfo,
    UnifiedSide,
)

logger = logging.getLogger("aiotrade.unified")


class UnifiedGateClient:
    """Gate client implementing ExchangeClient."""

    def __init__(
        self,
        account_display: str,
        api_key: str | None = None,
        api_secret: str | None = None,
        demo: bool = False,
        broker_tag: str | None = None,
    ) -> None:
        """Initialize Gate client wrapper."""
        self._account_display = account_display
        self._client = GateClient(
            api_key=api_key,
            api_secret=api_secret,
            demo=demo,
            broker_tag=broker_tag,
        )

    # Account/Balance methods
    async def _get_position(
        self,
        symbol: str | None,
        return_empty_pos: bool = True,
    ) -> dict[str, Any]:
        """
        Fetch and unwrap position for a symbol from Gate, handling hedge/non-hedge.

        - If hedge_mode == False: returns result dict itself (not from ['list']!)
        - If hedge_mode == True: returns the 'dual_long' position
            dict from ['result']['list'], or raises if not present.

        Args:
            symbol: Symbol to fetch.
            return_empty_pos: If False, only return position if size != 0.
        """
        if not symbol:
            raise ValueError("symbol is required")
        response = await self._client.get_position("usdt", symbol)
        result = response.get("result", {})

        if "list" in result:
            pos_list: list[dict[str, Any]] = result["list"]
            if not pos_list:
                raise ValueError(f"No positions returned for symbol: {symbol}")
            # In hedge mode: find 'dual_long'
            dual_long_pos = next(
                (p for p in pos_list if p.get("mode") == "dual_long"), None
            )
            if dual_long_pos is not None:
                if not return_empty_pos and dual_long_pos.get("size", 0) == 0:
                    raise ValueError(
                        "Position size is zero and return_empty_pos is False"
                    )
                return dual_long_pos
            raise ValueError(
                "No 'dual_long' position found in hedge mode positions list"
            )

        if not return_empty_pos and result.get("size", 0) == 0:
            raise ValueError("Position size is zero and return_empty_pos is False")
        return result  # type: ignore[no-any-return]

    async def get_margin_mode(self, symbol: str | None) -> UnifiedMarginMode:
        """Get margin mode for a symbol."""
        position = await self._get_position(symbol)
        mode = position.get("pos_margin_mode")
        if not mode:
            raise ValueError("pos_margin_mode not found in position response")

        match mode:
            case "cross":
                return UnifiedMarginMode.CROSS
            case "isolated":
                return UnifiedMarginMode.ISOLATED
            case _:
                raise ValueError(f"Unknown Gate pos_margin_mode: {mode}")

    async def update_margin_mode(
        self, symbol: str | None, mode: UnifiedMarginMode
    ) -> None:
        """Set margin mode."""
        if symbol is None:
            raise ValueError("symbol is required to update margin mode")
        if mode not in ("crossed", "isolated"):
            raise ValueError(f"Unsupported margin mode: {mode}")
        await self._client.update_position_cross_mode(
            "usdt", contract=symbol, mode=mode.to_gate()
        )

    async def get_hedge_mode(self, symbol: str | None) -> bool | None:
        """Query whether hedge mode is enabled for the specified symbol."""
        response = await self._client.get_futures_account("usdt")
        in_dual_mode = response.get("result", {}).get("in_dual_mode")
        if in_dual_mode is None:
            return None
        return in_dual_mode  # type: ignore[no-any-return]

    async def set_hedge_mode(self, enabled: bool) -> None:
        """Enable or disable hedge mode for USDT futures."""
        # if not changed will be error like this
        # message NO_CHANGE
        # code 400
        # response {"result":{},"retCode":400,"retMsg":"NO_CHANGE"}
        await self._client.set_dual_mode("usdt", enabled)

    async def get_asset_mode(self) -> UnifiedAssetMode | None:
        """Query the current asset mode (e.g., 'USDT', 'multi-asset', etc)."""
        resp = await self._client.get_futures_account("usdt")
        mode_int = resp.get("result", {}).get("margin_mode")
        if mode_int is None:
            return None
        return "single" if mode_int == 3 else "union"

    async def set_asset_mode(self, mode: UnifiedAssetMode) -> None:
        """
        Set the asset mode for the unified account.

        Args:
            mode (UnifiedAssetMode): The desired asset mode ("single" or "union").
        """
        # if not changed will be error like this
        # message NO_CHANGE
        # code 400
        # response {"result":{},"retCode":400,"retMsg":"NO_CHANGE"}

        # Mode map aligns aiotrade unified asset mode to Gate "mode" strings.
        mode_map: dict[UnifiedAssetMode, UnifiedMode] = {
            "single": "single_currency",
            "union": "multi_currency",
        }
        unified_mode = mode_map.get(mode)
        if unified_mode is None:
            raise ValueError(f"Unsupported asset mode: {mode}")

        await self._client.set_unified_mode(UnifiedModeSet(mode=unified_mode))

    async def get_usdt_available_balance(self) -> float | None:
        """Get wallet available balance from Gate (futures/USDT margin wallet)."""
        resp = await self._client.get_futures_account("usdt")
        # response is like: {'result': {'available': 24.34830824, ....}, ...}
        available = resp.get("result", {}).get("available")
        if available is None:
            return None
        return float(available)

    async def get_spot_usdt_balance(self) -> float | None:
        """Get the spot USDT balance for the account."""
        raise NotImplementedError(
            "Spot trading balance is not yet implemented for Gate."
        )

    # Position methods
    async def get_position_info(
        self, symbol: str | None = None
    ) -> list[UnifiedPositionInfo]:
        """Get position info from Gate, including open price orders."""
        price_trigger_orders_response = await self._client.list_price_triggered_orders(
            settle="usdt", contract=symbol, status="open"
        )
        price_trigger_orders = price_trigger_orders_response.get("result", {}).get(
            "list", []
        )

        trailing_orders_response = await self._client.list_trailing_orders(
            settle="usdt", contract=symbol, is_finished=False, hide_cancel=True
        )
        trailing_orders = (
            trailing_orders_response.get("result", {}).get("data", {}).get("orders", [])
        )
        positions_response = await self._client.list_positions("usdt", holding=True)

        return [
            unified_position_info_from_gate(
                self._account_display, price_trigger_orders, trailing_orders, x
            )
            for x in positions_response.get("result", {}).get("list", [])
        ]

    # Order methods
    async def close_position(
        self, position: UnifiedPositionInfo, order: UnifiedPlaceOrderRequest
    ) -> dict[str, Any]:
        """Close position."""
        # when no position
        # message POSITION_EMPTY
        # code 400
        # response {"result":{},"retCode":400,"retMsg":"POSITION_EMPTY"}

        # when expire
        # message the current time has exceeded the order expiration time.
        # code 400
        # response {"result":{},"retCode":400,"retMsg":"the current time has exceeded the order expiration time."}  # noqa: E501

        # invalid side when try close order
        # message invalid size with close-order
        # code 400
        # response {"result":{},"retCode":400,"retMsg":"invalid size with close-order"}

        # max order limit
        # message limit 100000
        # code 400
        # response {"result":{},"retCode":400,"retMsg":"limit 100000"}

        # not enough balance
        # message margin 26043.178774977 while available 957.25348
        # code 400
        # response {"result":{},"retCode":400,"retMsg":"margin 26043.178774977 while available 957.25348"}  # noqa: E501

        # success
        # response
        # {'result': {'amend_text' = '-',
        #     'bbo' = '-',
        #     'biz_info' = '-',
        #     'contract' = 'ADA_USDT',
        #     'create_time' = 1776417854.418,
        #     'fill_price' = '0.2573',
        #     'finish_as' = 'filled',
        #     'finish_time' = 1776417854.418,
        #     'iceberg' = 0,
        #     'id' = 21955048462469777,
        #     'is_close' = True,
        #     'is_liq' = False,
        #     'is_reduce_only' = False,
        #     'left' = 0,
        #     'market_order_slip_ratio' = '0.05',
        #     'mkfr' = '0.0002',
        #     'pnl' = '-0.4',
        #     'pnl_margin' = '25.9019425',
        #     'price' = '0',
        #     'refr' = '0',
        #     'refu' = 0,
        #     'size' = 100,
        #     'status' = 'finished',
        #     'stp_act' = '-',
        #     'stp_id' = 0,
        #     'text' = 'api',
        #     'tif' = 'ioc',
        #     'tkfr' = '0.0005',
        #     'update_id' = 1,
        #     'update_time' = 1776417854.418,
        #     'user' = 51876058 }}
        return await self._client.create_futures_order(
            settle="usdt",
            order=FuturesPlaceOrder(
                contract=position["symbol"],
                size=0,
                close=True,
                price=0,
                tif="ioc",
            ),
        )

    async def place_spot_order(
        self, params: UnifiedPlaceSpotOrderRequest
    ) -> dict[str, Any]:
        """Place spot order on Gate."""
        raise NotImplementedError(
            "Spot trading balance is not yet implemented for Gate."
        )

    async def get_spot_order_exec_qty(self, response: dict[str, Any]) -> float:
        """Get the executed quantity for a placed spot order (Gate).

        Extracts the orderId from the Gate response and get the executed qty.
        """
        raise NotImplementedError(
            "Spot trading balance is not yet implemented for Gate."
        )

    async def batch_place_order(
        self, has_existing_position: bool, requests: list[UnifiedPlaceOrderRequest]
    ) -> dict[str, Any]:
        """
        Batch place orders on Gate.

        For Gate, we have three types of orders:
            - main (market/limit)
            - trigger (conditional, e.g. stop/TP)
            - trail (trailing stop)

        Our converter returns a tuple: (main_orders, trigger_orders, trailing_orders).
        We need to collect all of them, and send each batch.
        If has_existing_position is True, do NOT send trigger/trailing orders.

        Returns a dictionary with results for each order type.
        """
        all_main_orders: list[FuturesPlaceOrder] = []
        all_trigger_orders: list[FuturesPriceTriggeredOrder] = []
        all_trailing_orders: list[FuturesPlaceTrailingOrder] = []

        for order in requests:
            main_order, trigger_orders, trailing_orders = (
                convert_unified_place_order_to_gate(order)
            )
            if main_order:
                all_main_orders.append(main_order)
            # Only add triggers/trailing if not has_existing_position (mimic binance.py)
            if not has_existing_position:
                all_trigger_orders.extend(trigger_orders)
                all_trailing_orders.extend(trailing_orders)
            elif trigger_orders or trailing_orders:
                logger.info(
                    "%s has_existing_position=True, skipping "
                    "trigger and trailing orders for symbol(s): %s",
                    self._account_display,
                    order["symbol"],
                )

        results: dict[str, Any] = {
            "main_orders_result": None,
            "trigger_orders_result": [],
            "trailing_orders_result": [],
        }
        main_error = None

        # Batch place main orders
        try:
            if all_main_orders:
                # Gate usually accepts single main order at a time, so place in parallel
                main_results = await asyncio.gather(
                    *(
                        self._client.create_futures_order(settle="usdt", order=order)
                        for order in all_main_orders
                    ),
                    return_exceptions=True,
                )
                results["main_orders_result"] = main_results
        except ExchangeResponseError as e:
            main_error = e

        # Place triggers one by one, collecting responses/errors
        for trigger_order in all_trigger_orders:
            try:
                resp = await self._client.create_price_triggered_order(
                    settle="usdt", order=trigger_order
                )
                results["trigger_orders_result"].append({"result": resp})
            except ExchangeResponseError as e:
                results["trigger_orders_result"].append({"error": e.resp})

        # Place trailing orders one by one, collecting responses/errors
        for trail_order in all_trailing_orders:
            try:
                resp = await self._client.create_trailing_order(
                    settle="usdt", order=trail_order
                )
                results["trailing_orders_result"].append({"result": resp})
            except ExchangeResponseError as e:
                results["trailing_orders_result"].append({"error": e.resp})

        # Logic: if batch main and all triggers/trails failed,
        # throw exception like in binance
        all_trigger_failed = len(all_trigger_orders) > 0 and all(
            "error" in x for x in results["trigger_orders_result"]
        )
        all_trailing_failed = len(all_trailing_orders) > 0 and all(
            "error" in x for x in results["trailing_orders_result"]
        )
        main_failed = main_error is not None or (
            results["main_orders_result"] is not None
            and all(isinstance(x, Exception) for x in results["main_orders_result"])
        )

        if main_failed and (
            (not all_trigger_orders and not all_trailing_orders)
            or (all_trigger_failed and all_trailing_failed)
        ):
            raise Exception(
                "Batch main orders failed: "
                + (repr(main_error) if main_error else "Unknown error")
                + f", Trigger orders results: {results['trigger_orders_result']}"
                + f", Trailing orders results: {results['trailing_orders_result']}"
            )

        return results

    async def batch_cancel_order(
        self, requests: list[UnifiedCancelOrderRequest]
    ) -> None:
        """Batch cancel orders on Gate."""
        # Separate requests by order type
        futures_order: list[UnifiedCancelOrderRequest] = []
        skipped_orders: list[UnifiedCancelOrderRequest] = []

        for order in requests:
            if order.get("order_type") in (
                UnifiedOrderType.MARKET,
                UnifiedOrderType.LIMIT,
            ):
                futures_order.append(order)
            else:
                skipped_orders.append(order)

        # Batch cancel limit orders using batch_cancel_futures_orders
        if futures_order:
            # Collect all IDs to a flat list
            ids_list = [
                str(order.get("order_id"))
                for order in futures_order
                if order.get("order_id") is not None
            ]

            # Send in batches of 10
            for i in range(0, len(ids_list), 10):
                batch_ids = ids_list[i : i + 10]
                if batch_ids:
                    await self._client.cancel_batch_future_orders(
                        "usdt", order_ids=batch_ids
                    )

        # For conditional (trigger) orders, just log a warning (don't cancel)
        for order in skipped_orders:
            order_id = order.get("order_id")
            logger.warning(
                f"{self._account_display} Skipping cancel for {order.get('order_type')}"
                f"this order type (id={order_id}). "
                "This order type cancel is not supported here."
            )

    async def get_pending_orders(self) -> list[UnifiedPendingOrder]:
        """Get pending orders from Gate."""
        price_trigger_orders_response = await self._client.list_price_triggered_orders(
            settle="usdt", contract=None, status="open"
        )
        futures_orders_response = await self._client.list_futures_orders(
            "usdt",
            status="open",
        )

        all_orders = futures_orders_response.get("result", {}).get(
            "list", []
        ) + price_trigger_orders_response.get("result", {}).get("list", [])
        return [unified_pending_order_from_gate(x) for x in all_orders]

    async def _terminate_trail_order(self, order_id: int) -> dict[str, Any]:
        """Terminate a trailing order via the Gate API."""
        response = await self._client.terminate_trail_order("usdt", id=order_id)
        if response.get("result", {}).get("code") != 0:
            raise Exception(f"Cancel trailing stop order failed: {response}")
        return response

    # Trading methods
    async def _cancel_trading_stop_orders(  # noqa: C901, PLR0912
        self,
        symbol: str,
        position: UnifiedPositionInfo | None,
        take_profit: float | None,
        stop_loss: float | None,
        active_price: float | None,
        trailing_delivation: float | None,
    ) -> None:
        """Cancel active algo orders (TP/SL/Trailing) that need to be replaced."""
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

        cancel_tasks: list[Coroutine[Any, Any, dict[str, Any]]] = []

        if len(additional.get("matching_tp_orders", [])) and (
            take_profit is not None
            or (trailing_delivation is not None and active_price is not None)
        ):
            for order in additional["matching_tp_orders"]:
                order_id = order["id"]
                if order_id:
                    logger.info(
                        "%s set_trading_stop: Cancelling TP trigger order for "
                        "symbol=%s: order_id=%s",
                        self._account_display,
                        symbol,
                        order_id,
                    )
                    cancel_tasks.append(
                        self._client.cancel_price_triggered_order(
                            "usdt", order_id=order_id
                        )
                    )

        if len(additional.get("matching_sl_orders", [])) and stop_loss is not None:
            for order in additional["matching_sl_orders"]:
                order_id = order["id"]
                if order_id:
                    logger.info(
                        "%s set_trading_stop: Cancelling SL trigger order for "
                        "symbol=%s: order_id=%s",
                        self._account_display,
                        symbol,
                        order_id,
                    )
                    cancel_tasks.append(
                        self._client.cancel_price_triggered_order(
                            "usdt", order_id=order_id
                        )
                    )

        if len(additional.get("matching_trailing_orders", [])) and (
            trailing_delivation is not None and active_price is not None
        ):
            for order in additional["matching_trailing_orders"]:
                order_id = order.get("id")
                if order_id:
                    logger.info(
                        "%s set_trading_stop: Cancelling Trailing order for "
                        "symbol=%s: order_id=%s",
                        self._account_display,
                        symbol,
                        order_id,
                    )
                    cancel_tasks.append(
                        self._terminate_trail_order(order_id=int(order_id))
                    )

        if cancel_tasks:
            results = await asyncio.gather(*cancel_tasks, return_exceptions=True)
            for r in results:
                if isinstance(r, Exception):
                    logger.warning(
                        "%s set_trading_stop: Failed to cancel algo order "
                        "for symbol=%s: %s",
                        self._account_display,
                        symbol,
                        r,
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
        """Set trading stop-loss/take-profit."""
        await self._cancel_trading_stop_orders(
            symbol=symbol,
            position=position,
            take_profit=take_profit,
            stop_loss=stop_loss,
            active_price=active_price,
            trailing_delivation=trailing_delivation,
        )

        if position is not None:
            pos_side = position["side"]
            qty_val = position["size"]
        elif side is not None and qty is not None:
            pos_side = side
            qty_val = qty
        else:
            raise ValueError(
                "set_trading_stop: Either 'position' or both 'side' "
                "and 'qty' must be provided."
            )

        # Construct price trigger orders for tp/sl
        trigger_orders: list[FuturesPriceTriggeredOrder] = []

        # Take profit
        if take_profit is not None:
            tp_order: FuturesPriceTriggeredOrder = {
                "initial": {
                    "contract": symbol,
                    "price": "0",
                    "reduce_only": True,
                    "tif": "ioc",
                    "auto_size": "close",
                },
                "trigger": {
                    "price": str(take_profit),
                    "rule": 1 if pos_side == UnifiedSide.LONG else 2,
                },
                "order_type": (
                    "close-long-position"
                    if pos_side == UnifiedSide.LONG
                    else "close-short-position"
                ),
            }
            trigger_orders.append(tp_order)

        # Stop loss
        if stop_loss is not None:
            sl_order: FuturesPriceTriggeredOrder = {
                "initial": {
                    "contract": symbol,
                    "price": "0",
                    "reduce_only": True,
                    "tif": "ioc",
                    "auto_size": "close",
                },
                "trigger": {
                    "price": str(stop_loss),
                    "rule": 2 if pos_side == UnifiedSide.LONG else 1,
                },
                "order_type": (
                    "close-long-position"
                    if pos_side == UnifiedSide.LONG
                    else "close-short-position"
                ),
            }
            trigger_orders.append(sl_order)

        # Now place orders via client, collecting responses/errors.
        errors: list[Exception] = []

        # Trailing stop (only one possible)
        if trailing_delivation is not None and active_price is not None:
            trailing_order: FuturesPlaceTrailingOrder = {
                "contract": symbol,
                "amount": -qty_val if pos_side == UnifiedSide.LONG else qty_val,
                "activation_price": str(active_price),
                "price_type": 1,
                "price_offset": f"{trailing_delivation}%",
                "position_related": True,
                "reduce_only": True,
                "is_gte": pos_side == UnifiedSide.LONG,
            }
            try:
                response = await self._client.create_trailing_order(
                    settle="usdt", order=trailing_order
                )
                if response.get("result", {}).get("code") != 0:
                    raise Exception(f"Trailing stop order failed: {response}")

            except Exception as e:
                logger.error(
                    "%s set_trading_stop: Failed to place trailing "
                    "stop order for %s: %s",
                    self._account_display,
                    symbol,
                    e,
                )
                errors.append(e)

        # Create price-triggered orders one by one (tp/sl)
        for trig_order in trigger_orders:
            try:
                await self._client.create_price_triggered_order(
                    settle="usdt", order=trig_order
                )
            except Exception as e:
                logger.error(
                    "%s set_trading_stop: Failed to place trigger order for %s: %s",
                    self._account_display,
                    symbol,
                    e,
                )
                errors.append(e)

        if errors:
            # mimic raising the first error if any fail
            raise errors[0]

    async def set_leverage(self, symbol: str, leverage: float) -> None:
        """Set leverage on Gate."""
        await self._client.update_position_leverage(
            "usdt", contract=symbol, leverage=leverage
        )
