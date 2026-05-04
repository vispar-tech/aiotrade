import asyncio
import logging
from typing import Any, Literal

from aiolimiter import AsyncLimiter

from aiotrade import OkxClient
from aiotrade.types.okx import (
    AlgoOrderType,
    AlgorithmOrderParams,
    CancelAlgorithmOrderParams,
    CancelOrderParams,
    ConditionalAlgorithmOrderParams,
    TrailingStopAlgorithmOrderParams,
)
from aiotrade.unified.converters.pending_order import (
    unified_pending_order_from_okx,
)
from aiotrade.unified.converters.place.futures import (
    convert_unified_place_order_to_okx,
)
from aiotrade.unified.converters.position import unified_position_info_from_okx
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
from aiotrade.utils.numbers import parse_float

logger = logging.getLogger("aiotrade.unified")


class UnifiedOkxClient:
    """Okx client implementing ExchangeClient."""

    def __init__(
        self,
        account_display: str,
        api_key: str | None = None,
        api_secret: str | None = None,
        passphrase: str | None = None,
        demo: bool = False,
        broker_tag: str | None = None,
        recv_window: int = 5000,
    ) -> None:
        """Initialize Okx client wrapper."""
        self._account_display = account_display
        self._client = OkxClient(
            api_key=api_key,
            api_secret=api_secret,
            passphrase=passphrase,
            demo=demo,
            recv_window=recv_window,
            broker_tag=broker_tag,
        )
        self._place_plan_order_limiter = AsyncLimiter(20, 2)  # 10 requests per 1 second

    # Account/Balance methods
    async def get_margin_mode(self, symbol: str | None) -> UnifiedMarginMode:
        """OKX: margin mode is determined per-order using `tdMode`."""
        raise NotImplementedError(
            "OKX does not have a global margin mode; specify 'tdMode' in each "
            "order request."
        )

    async def update_margin_mode(
        self, symbol: str | None, mode: UnifiedMarginMode
    ) -> None:
        """OKX: margin mode is determined per-order using `tdMode`."""
        raise NotImplementedError(
            "OKX does not have a global margin mode; specify 'tdMode' in each "
            "order request."
        )

    async def get_hedge_mode(self, symbol: str | None) -> bool | None:
        """Query whether hedge mode is enabled.

        For OKX: Use account config's 'posMode'.
        'long_short_mode' means hedge mode enabled.
        """
        resp = await self._client.get_account_config()
        data = resp.get("data")
        if not data:
            logger.error(
                "%s No data found in OKX account config response.",
                self._account_display,
            )
            return None

        # In OKX API, hedge mode = posMode == "long_short_mode"
        pos_mode = data[0].get("posMode") if data else None
        if pos_mode is None:
            logger.warning(
                "%s No posMode found in OKX account config data.", self._account_display
            )
            return None
        return pos_mode == "long_short_mode"  # type: ignore[no-any-return]

    async def set_hedge_mode(self, enabled: bool) -> None:
        """Enable or disable hedge mode."""
        await self._client.set_position_mode(
            pos_mode="long_short_mode" if enabled else "net_mode"
        )

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

    async def get_usdt_available_balance(self) -> float | None:
        """Get the available USDT balance for the account."""
        result = await self._client.get_balance()
        usdt_detail = None
        for account in result.get("data", []):
            for detail in account.get("details", []):
                if detail.get("ccy") == "USDT":
                    usdt_detail = detail
                    break
            if usdt_detail:
                break
        if not usdt_detail:
            return 0.0

        return float(usdt_detail["availBal"])

    async def get_spot_usdt_balance(self) -> float | None:
        """Get the spot USDT balance for the account."""
        raise NotImplementedError("Spot trading is not yet implemented for Okx.")

    # Position methods
    async def get_position_info(
        self, symbol: str | None = None
    ) -> list[UnifiedPositionInfo]:
        """Get current position information incl. open conditional/tp/sl orders."""
        # 1. Get open positions from OKX
        pos_response = await self._client.get_positions(
            inst_type="SWAP", inst_id=symbol if symbol else None
        )
        open_positions = pos_response.get("data", [])

        if not open_positions:
            return []

        # 2. Get all pending algo orders (tp/sl, conditional, trailing, etc)
        #   for those positions
        algo_orders: list[dict[str, Any]] = []
        # Get all possible types, for this moment,
        #   at least 'conditional' and 'move_order_stop'
        ord_types: set[AlgoOrderType] = {"conditional", "move_order_stop", "oco"}
        for ord_type in ord_types:
            algo_resp = await self._client.get_algo_orders_pending(
                ord_type=ord_type, inst_type="SWAP", inst_id=symbol if symbol else None
            )
            data = algo_resp.get("data", [])
            algo_orders.extend(data)

        return [
            unified_position_info_from_okx(self._account_display, algo_orders, pos)
            for pos in open_positions
            if parse_float(pos.get("size", 0)) not in [0, None]
        ]

    async def close_position(
        self, position: UnifiedPositionInfo, order: UnifiedPlaceOrderRequest
    ) -> dict[str, Any]:
        """Cancel position."""
        if "margin_mode" not in position.get("additional", {}):
            raise ValueError(
                "OKX Position should contain margin mode field in additional data"
            )
        return await self._client.close_position(
            inst_id=position["symbol"],
            mgn_mode=position.get("additional", {}).get("margin_mode", "isolated"),
            auto_cxl=True,
        )

    async def place_spot_order(
        self, params: UnifiedPlaceSpotOrderRequest
    ) -> dict[str, Any]:
        """Place spot order."""
        raise NotImplementedError("Spot trading is not yet implemented for Okx.")

    async def get_spot_order_exec_qty(self, response: dict[str, Any]) -> float:
        """Get the executed quantity for a placed spot order.

        Accepts the response as returned from place_spot_order.
        """
        raise NotImplementedError("Spot trading is not yet implemented for Okx.")

    async def batch_place_order(
        self, has_existing_position: bool, requests: list[UnifiedPlaceOrderRequest]
    ) -> dict[str, Any]:
        """Place multiple orders at once."""
        return await self._client.batch_place_order(
            orders=[
                convert_unified_place_order_to_okx(order, self._client.broker_tag)
                for order in requests
            ],
        )

    async def batch_cancel_order(
        self, requests: list[UnifiedCancelOrderRequest]
    ) -> None:
        """Cancel multiple orders at once."""
        """Batch cancel orders on Bybit."""
        converted_arrays: list[CancelOrderParams] = []
        for order in requests:
            obj = CancelOrderParams(instId=order["symbol"])
            if order_id := order.get("order_id"):
                obj["ordId"] = str(order_id)
            if order_link_id := order.get("order_link_id"):
                obj["clOrdId"] = order_link_id
            converted_arrays.append(obj)

        await self._client.cancel_batch_orders(orders=converted_arrays)

    async def get_pending_orders(self) -> list[UnifiedPendingOrder]:
        """Retrieve all pending (regular + algo) orders for SWAP."""
        # Regular pending orders
        orders_response = await self._client.get_orders_pending(inst_type="SWAP")
        regular_orders = [
            unified_pending_order_from_okx(x) for x in orders_response.get("data", [])
        ]

        # Also fetch algo orders pending
        algo_resp = await self._client.get_algo_orders_pending(
            ord_type="move_order_stop", inst_type="SWAP"
        )
        algo_orders = [
            unified_pending_order_from_okx(x) for x in algo_resp.get("data", [])
        ]

        return regular_orders + algo_orders

    # Trading methods
    async def _cancel_trading_stop_orders(  # noqa: C901, PLR0912
        self,
        symbol: str,
        position: UnifiedPositionInfo | None,
        take_profit: float | None,
        stop_loss: float | None,
        active_price: float | None,
        trailing_delivation: float | None,
    ) -> tuple[float | None, float | None] | None:
        """Cancel algo orders (TP/SL/Trailing) that need to be replaced."""
        if position is None:
            return None
        if not (additional := position.get("additional")):
            logger.warning(
                "%s set_trading_stop: Provided position has no "
                "'additional' field for symbol=%s",
                self._account_display,
                symbol,
            )
            return None

        cancel_orders: list[UnifiedCancelOrderRequest] = []

        # If either take_profit or stop_loss is provided
        # cancel all matching TP and SL orders
        if take_profit is not None or stop_loss is not None:
            cancel_tp_orders = bool(len(additional["matching_tp_orders"]))
            cancel_sl_orders = bool(len(additional["matching_sl_orders"]))
            if cancel_tp_orders:
                cancel_orders.extend(
                    [
                        UnifiedCancelOrderRequest(
                            symbol=order["instId"], order_id=order["algoId"]
                        )
                        for order in additional["matching_tp_orders"]
                    ]
                )

            if cancel_sl_orders:
                cancel_orders.extend(
                    [
                        UnifiedCancelOrderRequest(
                            symbol=order["instId"], order_id=order["algoId"]
                        )
                        for order in additional["matching_sl_orders"]
                    ]
                )

            if cancel_sl_orders and stop_loss is None:
                stop_loss = additional["matching_sl_orders"][0]["slTriggerPx"]

            if cancel_tp_orders and take_profit is None:
                take_profit = additional["matching_tp_orders"][0]["tpTriggerPx"]

        # Cancel trailing algo orders if:
        # - there is at least one existing trailing order AND
        # - we pass both trailing_delivation and active_price
        if (
            trailing_delivation is not None
            and active_price is not None
            and len(additional["matching_trailing_orders"])
        ):
            cancel_orders.extend(
                [
                    UnifiedCancelOrderRequest(
                        symbol=order["instId"], order_id=order["algoId"]
                    )
                    for order in additional["matching_trailing_orders"]
                ]
            )

        if cancel_orders:
            unique_cancel_orders: dict[str | int, UnifiedCancelOrderRequest] = {}
            for order in cancel_orders:
                algo_id = order.get("order_id")
                if algo_id is None:
                    raise Exception(
                        "Unexpected: missing algoId, but this should never happen. "
                        "Each algo order must have an algoId."
                    )
                if algo_id not in unique_cancel_orders:
                    unique_cancel_orders[algo_id] = order
            cancel_orders = list(unique_cancel_orders.values())

            # LOG: Show which orders about to be cancelled
            logger.info(
                "%s set_trading_stop: Cancelling %d algo order(s) for symbol=%s: %s",
                self._account_display,
                len(cancel_orders),
                symbol,
                [
                    {
                        "symbol": cancel_order["symbol"],
                        "order_id": cancel_order.get("order_id"),
                    }
                    for cancel_order in cancel_orders
                ],
            )

            try:
                await self._client.cancel_algo_orders(
                    orders=[
                        CancelAlgorithmOrderParams(
                            instId=cancel_order["symbol"],
                            algoId=str(cancel_order.get("order_id")),
                        )
                        for cancel_order in cancel_orders
                    ]
                )
                logger.info(
                    "%s set_trading_stop: Successfully sent "
                    "cancel_algo_orders for symbol=%s.",
                    self._account_display,
                    symbol,
                )
            except Exception as exc:
                logger.warning(
                    "%s set_trading_stop: Failed to cancel algo orders "
                    "for symbol=%s: %s",
                    self._account_display,
                    symbol,
                    exc,
                )
        return take_profit, stop_loss

    async def set_trading_stop(  # noqa: C901, PLR0912
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
        canceled_tp_sl = await self._cancel_trading_stop_orders(
            symbol=symbol,
            position=position,
            take_profit=take_profit,
            stop_loss=stop_loss,
            active_price=active_price,
            trailing_delivation=trailing_delivation,
        )
        if canceled_tp_sl is not None:
            take_profit, stop_loss = canceled_tp_sl

        order_side: Literal["sell", "buy"]
        if position is not None:
            order_side = "sell" if position["side"] == UnifiedSide.LONG else "buy"
            order_qty = position["size"]
        elif side is not None and qty is not None:
            order_side = "sell" if side == UnifiedSide.LONG else "buy"
            order_qty = qty
        else:
            raise ValueError(
                "set_trading_stop: Either a valid 'position' or both 'side' "
                "and 'qty' must be provided for Bingx."
            )

        plan_orders: list[AlgorithmOrderParams] = []

        if take_profit is not None or stop_loss is not None:
            algo_params = ConditionalAlgorithmOrderParams(
                instId=symbol,
                side=order_side,
                ordType="conditional",
                cxlOnClosePos=True,
                closeFraction=1,
                reduceOnly=True,
                tdMode="isolated",
            )
            if take_profit is not None:
                algo_params["tpTriggerPx"] = take_profit
                algo_params["tpTriggerPxType"] = "last"
                algo_params["tpOrdPx"] = -1
            if stop_loss is not None:
                algo_params["slTriggerPx"] = stop_loss
                algo_params["slTriggerPxType"] = "last"
                algo_params["slOrdPx"] = -1

            # NOTE: if set both, should be oco type
            if stop_loss is not None and take_profit is not None:
                algo_params["ordType"] = "oco"

            if self._client.broker_tag is not None:
                algo_params["tag"] = self._client.broker_tag
            plan_orders.append(algo_params)
        if trailing_delivation is not None and active_price is not None:
            trailing_algo_params = TrailingStopAlgorithmOrderParams(
                instId=symbol,
                tdMode="isolated",
                ordType="move_order_stop",
                side=order_side,
                callbackRatio=trailing_delivation,
                sz=order_qty,
                activePx=active_price,
                cxlOnClosePos=True,
                reduceOnly=True,
            )
            if self._client.broker_tag is not None:
                trailing_algo_params["tag"] = self._client.broker_tag
            plan_orders.append(trailing_algo_params)

        async def place_plan_order_with_rate_limit(
            order_params: AlgorithmOrderParams,
        ) -> None:
            try:
                async with self._place_plan_order_limiter:
                    await self._client.place_algo_order(order_params)
            except Exception as e:
                logger.error(
                    "%s Failed to place plan order for %s [%s]: %s",
                    self._account_display,
                    order_params.get("instId"),
                    order_params.get("ordType"),
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
            leverage=int(leverage),
            mgn_mode="isolated",
            inst_id=symbol,
        )
