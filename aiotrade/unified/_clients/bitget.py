import asyncio
import logging
from typing import Any, Literal

from aiolimiter import AsyncLimiter

from aiotrade import BitgetClient
from aiotrade.types.bitget import (
    GetPendingTriggerOrdersParams,
    PlaceOrderParams,
    PlaceTpslPlanOrderParams,
    ProductType,
)
from aiotrade.unified.converters.pending_order import unified_pending_order_from_bitget
from aiotrade.unified.converters.place.futures import (
    convert_unified_place_order_to_bitget,
)
from aiotrade.unified.converters.position import unified_position_info_from_bitget
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

TriggerPlanType = Literal[
    "normal_plan", "profit_plan", "loss_plan", "pos_profit", "pos_loss", "moving_plan"
]


class UnifiedBitgetClient:
    """Bitget client implementing ExchangeClient."""

    def __init__(
        self,
        account_display: str,
        api_key: str | None = None,
        api_secret: str | None = None,
        passphrase: str | None = None,
        demo: bool = False,
        channel_api_code: str | None = None,
        recv_window: int = 5000,
    ) -> None:
        """Initialize Bitget client wrapper."""
        self._account_display = account_display
        self._client = BitgetClient(
            api_key=api_key,
            api_secret=api_secret,
            passphrase=passphrase,
            demo=demo,
            recv_window=recv_window,
            channel_api_code=channel_api_code,
        )
        self._place_plan_order_limiter = AsyncLimiter(10, 1)  # 10 requests per 1 second

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
        resp = await self._client.get_single_account(
            symbol=symbol, margin_coin="USDT", product_type="USDT-FUTURES"
        )
        data = resp.get("data", {})
        margin_mode_raw = data.get("marginMode")
        if margin_mode_raw is None:
            return UnifiedMarginMode.OTHER

        # Bitget returns: "isolated", "crossed", possibly others
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
        mode_bitget = mode.to_bitget()
        if not symbol:
            raise ValueError(
                "symbol must be specified when updating margin mode on BingX"
            )

        await self._client.set_margin_mode(
            symbol=symbol,
            product_type="USDT-FUTURES",
            margin_coin="USDT",
            margin_mode=mode_bitget,
        )

    async def get_hedge_mode(self, symbol: str | None) -> bool | None:
        """Query whether hedge mode is enabled."""
        # NOTE: Need specify symbol to query global hedge mode
        resp = await self._client.get_single_account(
            symbol="BTCUSDT", product_type="USDT-FUTURES", margin_coin="USDT"
        )
        hedge_mode = resp.get("data", {}).get("posMode")
        if hedge_mode is not None:
            return hedge_mode == "hedge_mode"  # type: ignore[no-any-return]
        return None

    async def set_hedge_mode(self, enabled: bool) -> None:
        """Enable or disable hedge mode."""
        await self._client.set_position_mode(
            product_type="USDT-FUTURES",
            pos_mode="hedge_mode" if enabled else "one_way_mode",
        )

    async def get_asset_mode(self) -> UnifiedAssetMode | None:
        """Query the current asset mode (e.g., 'USDT', 'multi-asset', etc)."""
        # Query account list and look for USDT marginCoin
        resp = await self._client.get_account_list(product_type="USDT-FUTURES")
        data = resp.get("data", [])
        for entry in data:
            if entry.get("marginCoin") == "USDT":
                return entry.get("assetMode")  # type: ignore[no-any-return]
        return None

    async def set_asset_mode(self, mode: UnifiedAssetMode) -> None:
        """Set the asset mode (e.g., 'USDT', 'multi-asset', etc)."""
        await self._client.set_asset_mode(
            product_type="USDT-FUTURES",
            asset_mode=mode,
        )

    async def get_usdt_available_balance(self) -> float | None:
        """Get the available USDT balance for the account."""
        result = await self._client.get_account_list("USDT-FUTURES")

        usdt_balance = self._client.helpers.extract_wallet_balance(result, asset="USDT")

        if usdt_balance is None:
            logger.error(
                "%s No USDT asset found at bitget account.", self._account_display
            )
            return None

        return usdt_balance

    async def get_spot_usdt_balance(self) -> float | None:
        """Get the spot USDT balance for the account."""
        raise NotImplementedError(
            "Spot trading balance is not yet implemented for Bitget."
        )

    # Position methods
    async def get_position_info(
        self, symbol: str | None = None
    ) -> list[UnifiedPositionInfo]:
        """Get current position information."""
        # Get all open positions for USDT-FUTURES
        pos_resp = await self._client.get_all_positions(
            product_type="USDT-FUTURES",
            margin_coin="USDT",
        )
        positions_data: list[dict[str, Any]] = pos_resp.get("data") or []

        # Get all open trigger (stop/profit/trailing) orders for USDT-FUTURES
        tr_orders_resp = await self._client.get_pending_trigger_orders(
            params=GetPendingTriggerOrdersParams(
                productType="USDT-FUTURES",
                planType="profit_loss",
            )
        )
        open_orders_data: list[dict[str, Any]] = (
            tr_orders_resp.get("data", {}).get("entrustedList") or []
        )

        # Optionally filter by symbol
        if symbol is not None:
            positions_data = [x for x in positions_data if x.get("symbol") == symbol]
            open_orders_data = [
                o for o in open_orders_data if o.get("symbol") == symbol
            ]

        return [
            unified_position_info_from_bitget(
                self._account_display, open_orders_data, pos
            )
            for pos in positions_data
        ]

    async def close_position(
        self, position: UnifiedPositionInfo, order: UnifiedPlaceOrderRequest
    ) -> dict[str, Any]:
        """Cancel position."""
        return await self._client.place_futures_order(
            params=PlaceOrderParams(
                productType="USDT-FUTURES",
                symbol=position["symbol"],
                marginMode="isolated",
                marginCoin="USDT",
                size=position["size"],
                orderType="market",
                side="sell" if position["side"] == UnifiedSide.LONG else "buy",
                reduceOnly="YES",
            )
        )

    async def place_spot_order(
        self, params: UnifiedPlaceSpotOrderRequest
    ) -> dict[str, Any]:
        """Place spot order."""
        raise NotImplementedError("Spot trading is not yet implemented for Bitget.")

    async def get_spot_order_exec_qty(self, response: dict[str, Any]) -> float:
        """Get the executed quantity for a placed spot order.

        Accepts the response as returned from place_spot_order.
        """
        raise NotImplementedError("Spot trading is not yet implemented for Bitget.")

    async def batch_place_order(
        self, has_existing_position: bool, requests: list[UnifiedPlaceOrderRequest]
    ) -> dict[str, Any]:
        """Place multiple orders at once."""
        if not requests:
            return {}

        symbols = {order["symbol"] for order in requests}
        if len(symbols) > 1:
            raise ValueError(
                "batch_place_order for Bitget supports "
                "only orders with the same symbol; "
                f"got multiple symbols: {list(symbols)}"
            )
        symbol = next(iter(symbols))

        product_type: ProductType = "USDT-FUTURES"
        # todo: determine needed margin mode
        margin_mode: Literal["isolated", "crossed"] = "isolated"
        margin_coin = "USDT"

        order_list = [
            convert_unified_place_order_to_bitget(order) for order in requests
        ]
        logger.info(
            "Bitget batch_place_futures_orders: "
            "symbol=%s, product_type=%s, margin_mode=%s, margin_coin=%s, order_list=%s",
            symbol,
            product_type,
            margin_mode,
            margin_coin,
            order_list,
        )
        return await self._client.batch_place_futures_orders(
            symbol=symbol,
            product_type=product_type,
            margin_mode=margin_mode,
            margin_coin=margin_coin,
            order_list=order_list,
        )

    async def batch_cancel_order(
        self, requests: list[UnifiedCancelOrderRequest]
    ) -> None:
        """Batch cancel orders.

        Gathers all symbols present in the requests
        and sends batch cancel requests for each symbol.
        """
        if not requests:
            return

        product_type: ProductType = "USDT-FUTURES"
        margin_coin = "USDT"

        # Group orders by symbol
        symbol_to_order_id_list: dict[str, list[dict[str, str]]] = {}

        for order in requests:
            symbol = order["symbol"]
            if not symbol:
                continue
            order_dict = None
            if order_id := order.get("order_id"):
                order_dict = {"orderId": str(order_id)}
            elif order_link_id := order.get("order_link_id"):
                order_dict = {"clientOid": order_link_id}
            if order_dict:
                if symbol not in symbol_to_order_id_list:
                    symbol_to_order_id_list[symbol] = []
                symbol_to_order_id_list[symbol].append(order_dict)

        # Execute batch cancel for each symbol
        for symbol, order_id_list in symbol_to_order_id_list.items():
            if not order_id_list:
                continue
            await self._client.batch_cancel_futures_orders(
                product_type=product_type,
                order_id_list=order_id_list,
                symbol=symbol,
                margin_coin=margin_coin,
            )

    async def get_pending_orders(self) -> list[UnifiedPendingOrder]:
        """Retrieve pending orders."""
        orders_response = await self._client.get_pending_orders(
            product_type="USDT-FUTURES"
        )
        orders_list: list[dict[str, Any]] = (
            orders_response.get("data", {}).get("entrustedList") or []
        )
        return [unified_pending_order_from_bitget(x) for x in orders_list]

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
        """Cancel trigger orders (TP/SL/Trailing) that need to be replaced."""
        if position is None or not (additional := position.get("additional")):
            return

        trigger_cancel_map: dict[
            Literal[
                "normal_plan",
                "profit_plan",
                "loss_plan",
                "pos_profit",
                "pos_loss",
                "moving_plan",
            ],
            list[str],
        ] = {
            "pos_profit": [],
            "profit_plan": [],
            "pos_loss": [],
            "loss_plan": [],
            "moving_plan": [],
        }

        if additional.get("matching_tp_orders") and (
            take_profit is not None
            or (trailing_delivation is not None and active_price is not None)
        ):
            for order in additional["matching_tp_orders"]:
                trigger_cancel_map[order["planType"]].append(str(order["orderId"]))

        if additional.get("matching_sl_orders") and stop_loss is not None:
            for order in additional["matching_sl_orders"]:
                trigger_cancel_map[order["planType"]].append(str(order["orderId"]))

        if additional.get("matching_trailing_orders") and (
            trailing_delivation is not None and active_price is not None
        ):
            for order in additional["matching_trailing_orders"]:
                trigger_cancel_map["moving_plan"].append(str(order["orderId"]))

        product_type: ProductType = "USDT-FUTURES"
        margin_coin = "USDT"

        async def cancel_plan_type(
            pt: TriggerPlanType,
            order_id_list: list[str],
        ) -> None:
            if not order_id_list:
                return

            logger.info(
                "%s set_trading_stop: Cancelling trigger orders for symbol=%s, "
                "plan_type=%s, order_ids=%s",
                self._account_display,
                symbol,
                pt,
                order_id_list,
            )
            await self._client.cancel_trigger_orders(
                product_type=product_type,
                symbol=symbol,
                margin_coin=margin_coin,
                plan_type=pt,
                order_id_list=[{"orderId": oid} for oid in order_id_list],
            )

        tasks = [
            cancel_plan_type(plan_type, order_id_list)
            for plan_type, order_id_list in trigger_cancel_map.items()
            if order_id_list
        ]
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in results:
                if isinstance(r, Exception):
                    logger.warning(
                        "%s set_trading_stop: Failed to cancel trigger orders "
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
        """Set trading stop on bitget."""
        await self._cancel_trading_stop_orders(
            symbol=symbol,
            position=position,
            take_profit=take_profit,
            stop_loss=stop_loss,
            active_price=active_price,
            trailing_delivation=trailing_delivation,
        )

        order_side: Literal["sell", "buy"]
        if position is not None:
            order_side = "buy" if position["side"] == UnifiedSide.LONG else "sell"
            order_qty = position["size"]
        elif side is not None and qty is not None:
            order_side = "buy" if side == UnifiedSide.LONG else "sell"
            order_qty = qty
        else:
            raise ValueError(
                "set_trading_stop: Either a valid 'position' or both 'side' "
                "and 'qty' must be provided for Bingx."
            )

        plan_orders: list[PlaceTpslPlanOrderParams] = []

        if take_profit is not None:
            plan_orders.append(
                PlaceTpslPlanOrderParams(
                    productType="USDT-FUTURES",
                    symbol=symbol,
                    planType="pos_profit",
                    triggerPrice=take_profit,
                    triggerType="fill_price",
                    holdSide=order_side,
                    marginCoin="USDT",
                    stpMode="cancel_both",
                ),
            )
        if stop_loss is not None:
            plan_orders.append(
                PlaceTpslPlanOrderParams(
                    productType="USDT-FUTURES",
                    symbol=symbol,
                    planType="pos_loss",
                    triggerPrice=stop_loss,
                    triggerType="fill_price",
                    holdSide=order_side,
                    marginCoin="USDT",
                    stpMode="cancel_both",
                ),
            )
        if trailing_delivation is not None and active_price is not None:
            plan_orders.append(
                PlaceTpslPlanOrderParams(
                    productType="USDT-FUTURES",
                    symbol=symbol,
                    planType="moving_plan",
                    triggerPrice=active_price,
                    triggerType="fill_price",
                    holdSide=order_side,
                    size=order_qty,
                    marginCoin="USDT",
                    rangeRate=trailing_delivation,
                    stpMode="cancel_both",
                ),
            )

        async def place_plan_order_with_rate_limit(
            order_params: PlaceTpslPlanOrderParams,
        ) -> None:
            try:
                async with self._place_plan_order_limiter:
                    await self._client.place_tpsl_plan_order(order_params)
            except Exception as e:
                logger.error(
                    "%s Failed to place plan order for %s [%s]: %s",
                    self._account_display,
                    order_params.get("symbol"),
                    order_params.get("planType"),
                    e,
                )
                raise

        tasks = [
            place_plan_order_with_rate_limit(order_params)
            for order_params in plan_orders
        ]
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            exceptions = [r for r in results if isinstance(r, Exception)]
            if exceptions:
                raise exceptions[0]

    async def set_leverage(self, symbol: str, leverage: float) -> None:
        """Set leverage for a symbol or account."""
        await self._client.set_leverage(
            symbol=symbol,
            product_type="USDT-FUTURES",
            margin_coin="USDT",
            leverage=str(int(leverage)),
        )
