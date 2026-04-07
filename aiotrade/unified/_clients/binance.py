import asyncio
import logging
import uuid
from collections.abc import Coroutine
from typing import Any, Literal

from aiotrade import BinanceClient
from aiotrade.types.binance import (
    AlgorithmOrderParams,
    CreateOrderParams,
    StopTakeProfitAlgorithmOrderParams,
    TrailingStopMarketAlgorithmOrderParams,
)
from aiotrade.unified.converters.pending_order import (
    unified_pending_order_from_binance,
)
from aiotrade.unified.converters.place.futures import (
    convert_unified_place_order_to_binance,
)
from aiotrade.unified.converters.position import unified_position_info_from_binance
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


class UnifiedBinanceClient:
    """Binance client implementing ExchangeClient."""

    def __init__(
        self,
        account_display: str,
        api_key: str | None = None,
        api_secret: str | None = None,
        demo: bool = False,
        broker_id: str | None = None,
        recv_window: int = 5000,
    ) -> None:
        """Initialize Binance client wrapper."""
        self._account_display = account_display
        self._client = BinanceClient(
            api_key=api_key,
            api_secret=api_secret,
            demo=demo,
            recv_window=recv_window,
            broker_id=broker_id,
        )

    # Account/Balance methods
    async def get_margin_mode(self, symbol: str | None) -> UnifiedMarginMode:
        """
        Query user margin mode.

        For Bitget, margin mode is returned as a string in "marginMode" field.
        """
        if not symbol:
            raise ValueError(
                "symbol must be specified when querying margin mode on Bitget"
            )
        resp = await self._client.get_symbol_config(symbol=symbol)
        # Find the entry for the correct symbol and check marginType
        data = resp.get("result", {}).get("list", [])
        entry = None
        for item in data:
            if item.get("symbol") == symbol:
                entry = item
                break

        if not entry:
            return UnifiedMarginMode.OTHER

        margin_mode_raw = entry.get("marginType")
        if margin_mode_raw is None:
            return UnifiedMarginMode.OTHER

        margin_mode_raw = str(margin_mode_raw).lower()
        if margin_mode_raw == "isolated":
            return UnifiedMarginMode.ISOLATED
        if margin_mode_raw == "crossed":
            return UnifiedMarginMode.CROSS
        return UnifiedMarginMode.OTHER

    async def update_margin_mode(
        self, symbol: str | None, mode: UnifiedMarginMode
    ) -> None:
        """Update user margin mode."""
        mode_bitget = mode.to_binance()
        if not symbol:
            raise ValueError(
                "symbol must be specified when updating margin mode on Binance"
            )

        await self._client.change_margin_type(
            symbol=symbol,
            margin_type=mode_bitget,
        )

    async def get_hedge_mode(self, symbol: str | None) -> bool | None:
        """Query whether hedge mode is enabled."""
        resp = await self._client.get_position_mode()
        # Find the entry for the correct symbol and check marginType
        data = resp.get("result")

        if not data:
            return None

        hedge_mode = data.get("dualSidePosition")
        if hedge_mode is not None:
            return hedge_mode  # type: ignore[no-any-return]
        return None

    async def set_hedge_mode(self, enabled: bool) -> None:
        """Enable or disable hedge mode."""
        await self._client.change_position_mode(dual_side_position=enabled)

    async def get_asset_mode(self) -> UnifiedAssetMode | None:
        """Query the current asset mode (e.g., 'USDT', 'multi-asset', etc)."""
        resp = await self._client.get_multi_assets_mode()
        # Find the entry for the correct symbol and check marginType
        data = resp.get("result")

        if not data:
            return None

        asset_mode = data.get("multiAssetsMargin")
        if asset_mode is not None:
            return "union" if asset_mode else "single"
        return None

    async def set_asset_mode(self, mode: UnifiedAssetMode) -> None:
        """Set the asset mode (e.g., 'USDT', 'multi-asset', etc)."""
        await self._client.change_multi_assets_mode(multi_assets_margin=mode == "union")

    async def get_usdt_available_balance(self) -> float | None:
        """Get the available USDT balance for the account."""
        result = await self._client.get_account_balance()
        usdt_entry = None
        for entry in result.get("result", {}).get("list", []):
            if (
                entry.get("asset") == "USDT"
                and float(entry.get("availableBalance", 0)) != 0
            ):
                usdt_entry = entry
                break
        if not usdt_entry:
            logger.warning(
                "%s No USDT futures asset found in binance account.",
                self._account_display,
            )
            return None

        return float(usdt_entry["availableBalance"])

    async def get_spot_usdt_balance(self) -> float | None:
        """Get the spot USDT balance for the account."""
        raise NotImplementedError("Spot trading is not yet implemented for Binance.")

    # Position methods
    async def get_position_info(
        self, symbol: str | None = None
    ) -> list[UnifiedPositionInfo]:
        """Get current position information."""
        # Fetch position info from Binance
        positions_resp = await self._client.get_position_info()
        positions = positions_resp.get("result", {}).get("list", [])

        # Filter by symbol if needed
        if symbol:
            positions = [p for p in positions if p.get("symbol") == symbol]

        # Collect all unique symbols with open positions
        symbols_set: set[str] = {
            p["symbol"] for p in positions if float(p.get("positionAmt", 0)) != 0
        }
        if symbol:
            symbols_set = {symbol} if symbols_set else set()

        open_algo_orders_map: dict[str, list[dict[str, Any]]]
        if symbols_set:
            open_algo_orders_results = await asyncio.gather(
                *[self._client.get_open_algo_orders(symbol=s) for s in symbols_set]
            )
            # Map symbol -> open_algo_orders for convenience
            open_algo_orders_map = {}
            for s, resp in zip(symbols_set, open_algo_orders_results, strict=False):
                open_algo_orders = resp.get("result", {}).get("list", [])
                open_algo_orders_map[s] = open_algo_orders
        else:
            open_algo_orders_map = {}

        unified_positions: list[UnifiedPositionInfo] = []
        for pos in positions:
            if float(pos["positionAmt"]) == 0:
                continue
            sym = pos["symbol"]
            algo_orders = open_algo_orders_map.get(sym, [])
            unified_positions.append(
                unified_position_info_from_binance(
                    self._account_display, algo_orders, pos
                )
            )
        return unified_positions

    async def close_position(
        self, position: UnifiedPositionInfo, order: UnifiedPlaceOrderRequest
    ) -> dict[str, Any]:
        """Cancel position."""
        order_uuid = uuid.uuid4().hex[:12]

        return await self._client.create_order(
            params=CreateOrderParams(
                symbol=position["symbol"],
                side="BUY" if position["side"] == UnifiedSide.SHORT else "SELL",
                type="MARKET",
                quantity=position["size"],
                reduceOnly="true",
                newClientOrderId=(
                    BinanceClient.helpers.prepend_broker_id(
                        self._client.broker_id, order_uuid, 33
                    )
                    + "_cl"
                ),
            )
        )

    async def place_spot_order(
        self, params: UnifiedPlaceSpotOrderRequest
    ) -> dict[str, Any]:
        """Place spot order."""
        raise NotImplementedError("Spot trading is not yet implemented for Binance.")

    async def get_spot_order_exec_qty(self, response: dict[str, Any]) -> float:
        """Get the executed quantity for a placed spot order.

        Accepts the response as returned from place_spot_order.
        """
        raise NotImplementedError("Spot trading is not yet implemented for Binance.")

    async def batch_place_order(
        self, has_existing_position: bool, requests: list[UnifiedPlaceOrderRequest]
    ) -> dict[str, Any]:
        """Place multiple orders at once."""
        all_orders: list[CreateOrderParams] = []
        algo_orders: list[AlgorithmOrderParams] = []

        for order in requests:
            main_orders, conditional_orders = convert_unified_place_order_to_binance(
                self._client.broker_id, order
            )
            all_orders.extend(main_orders)
            # If has_existing_position, we do not add algo orders
            if not has_existing_position:
                algo_orders.extend(conditional_orders)
            elif conditional_orders:
                logger.info(
                    "%s has_existing_position=True, skipping "
                    "algo orders for symbol(s): %s",
                    self._account_display,
                    ", ".join(
                        [o.get("symbol", "<unknown>") for o in conditional_orders]
                    ),
                )

        # Wrap batch_orders sending in try-except
        batch_error = None
        batch_result = None
        try:
            batch_result = await self._client.create_batch_orders(
                params=all_orders,
            )
        except Exception as e:
            batch_error = e

        # For each algo-order, use a separate try-except and
        # collect resp/error in a separate list
        algo_results: list[dict[str, Any]] = []
        algo_errors: list[Exception] = []
        for algo_order in algo_orders:
            try:
                resp = await self._client.create_algo_order(params=algo_order)
                algo_results.append({"result": resp})
            except Exception as e:
                algo_results.append({"error": repr(e)})
                algo_errors.append(e)

        # Check: if batch and *all* algo_orders failed -
        # throw Exception with all responses
        all_algo_failed = len(algo_orders) > 0 and len(algo_errors) == len(algo_orders)
        batch_failed = batch_error is not None

        if batch_failed and (not algo_orders or all_algo_failed):
            # Collect responses for debugging
            raise Exception(
                "Batch orders failed: "
                + (repr(batch_error) if batch_error else "Unknown error")
                + f", Algo orders results: {algo_results}"
            )

        return {"batch_orders_result": batch_result, "algo_orders_result": algo_results}

    async def batch_cancel_order(
        self, requests: list[UnifiedCancelOrderRequest]
    ) -> None:
        """Cancel multiple orders at once."""
        # Step 1: Separate conditional (algo) orders and regular orders
        regular_orders: list[UnifiedCancelOrderRequest] = []
        conditional_orders: list[UnifiedCancelOrderRequest] = []

        for order in requests:
            if order.get("order_type") == UnifiedOrderType.CONDITIONAL:
                conditional_orders.append(order)
            else:
                regular_orders.append(order)

        # Step 2: Batch cancel regular orders (old logic)
        symbol_to_requests: dict[str, list[UnifiedCancelOrderRequest]] = {}
        for order in regular_orders:
            symbol = order["symbol"]
            symbol_to_requests.setdefault(symbol, []).append(order)

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

            # Batch cancel via regular endpoint
            await self._client.cancel_batch_orders(
                symbol=symbol,
                order_id_list=order_ids,
                orig_client_order_id_list=client_order_ids,
            )

        # Step 3: Cancel each conditional order (algo) individually
        for order in conditional_orders:
            if algo_id := order.get("order_id"):
                await self._client.cancel_algo_order(algo_id=int(algo_id))
            elif client_algo_id := order.get("order_link_id"):
                await self._client.cancel_algo_order(client_algo_id=str(client_algo_id))

    async def get_pending_orders(self) -> list[UnifiedPendingOrder]:
        """Retrieve all pending orders (regular and algo) as a single list."""
        orders_response = await self._client.get_open_orders()
        algo_orders_response = await self._client.get_open_algo_orders(
            algo_type="CONDITIONAL"
        )

        orders = [
            unified_pending_order_from_binance(x)
            for x in orders_response.get("result", {}).get("list", [])
        ]
        algo_orders = [
            unified_pending_order_from_binance(x)
            for x in algo_orders_response.get("result", {}).get("list", [])
        ]
        return orders + algo_orders

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
                client_algo_id = order.get("clientAlgoId")
                if client_algo_id:
                    logger.info(
                        "%s set_trading_stop: Cancelling TP algo order for "
                        "symbol=%s: clientAlgoId=%s",
                        self._account_display,
                        symbol,
                        client_algo_id,
                    )
                    cancel_tasks.append(
                        self._client.cancel_algo_order(client_algo_id=client_algo_id)
                    )

        if len(additional.get("matching_sl_orders", [])) and stop_loss is not None:
            for order in additional["matching_sl_orders"]:
                client_algo_id = order.get("clientAlgoId")
                if client_algo_id:
                    logger.info(
                        "%s set_trading_stop: Cancelling SL algo order for "
                        "symbol=%s: clientAlgoId=%s",
                        self._account_display,
                        symbol,
                        client_algo_id,
                    )
                    cancel_tasks.append(
                        self._client.cancel_algo_order(client_algo_id=client_algo_id)
                    )

        if len(additional.get("matching_trailing_orders", [])) and (
            trailing_delivation is not None and active_price is not None
        ):
            for order in additional["matching_trailing_orders"]:
                client_algo_id = order.get("clientAlgoId")
                if client_algo_id:
                    logger.info(
                        "%s set_trading_stop: Cancelling Trailing algo order for "
                        "symbol=%s: clientAlgoId=%s",
                        self._account_display,
                        symbol,
                        client_algo_id,
                    )
                    cancel_tasks.append(
                        self._client.cancel_algo_order(client_algo_id=client_algo_id)
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

        plan_orders: list[AlgorithmOrderParams] = []

        order_uuid = uuid.uuid4().hex[:12]

        if take_profit is not None:
            plan_orders.append(
                StopTakeProfitAlgorithmOrderParams(
                    algoType="CONDITIONAL",
                    symbol=symbol,
                    side=order_side,
                    type="TAKE_PROFIT_MARKET",
                    positionSide="BOTH",
                    workingType="CONTRACT_PRICE",
                    triggerPrice=take_profit,
                    closePosition="true",
                    clientAlgoId=BinanceClient.helpers.prepend_broker_id(
                        self._client.broker_id, order_uuid, 33
                    )
                    + "_tp",
                )
            )
        if stop_loss is not None:
            plan_orders.append(
                StopTakeProfitAlgorithmOrderParams(
                    algoType="CONDITIONAL",
                    symbol=symbol,
                    side=order_side,
                    type="STOP_MARKET",
                    positionSide="BOTH",
                    workingType="CONTRACT_PRICE",
                    triggerPrice=stop_loss,
                    closePosition="true",
                    clientAlgoId=BinanceClient.helpers.prepend_broker_id(
                        self._client.broker_id, order_uuid, 33
                    )
                    + "_sl",
                )
            )
        if trailing_delivation is not None and active_price is not None:
            plan_orders.append(
                TrailingStopMarketAlgorithmOrderParams(
                    algoType="CONDITIONAL",
                    symbol=symbol,
                    side=order_side,
                    type="TRAILING_STOP_MARKET",
                    positionSide="BOTH",
                    workingType="CONTRACT_PRICE",
                    activatePrice=active_price,
                    callbackRate=trailing_delivation,
                    quantity=order_qty,
                    reduceOnly="true",
                    clientAlgoId=BinanceClient.helpers.prepend_broker_id(
                        self._client.broker_id, order_uuid, 33
                    )
                    + "_tr",
                )
            )

        async def place_plan_order(
            order_params: AlgorithmOrderParams,
        ) -> None:
            order_type = order_params["type"]
            try:
                await self._client.create_algo_order(order_params)
            except Exception as e:
                logger.error(
                    "%s Failed to place plan order for %s [%s]: %s",
                    self._account_display,
                    order_params["symbol"],
                    order_type,
                    e,
                )
                raise

        tasks = [place_plan_order(order_params) for order_params in plan_orders]
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            exceptions = [r for r in results if isinstance(r, Exception)]
            if exceptions:
                raise exceptions[0]

    async def set_leverage(self, symbol: str, leverage: float) -> None:
        """Set leverage for a symbol or account."""
        await self._client.change_leverage(symbol=symbol, leverage=int(leverage))
