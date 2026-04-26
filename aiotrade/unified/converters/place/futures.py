"""Converters for unified futures order placement parameters."""

from typing import Literal

from aiotrade import BinanceClient
from aiotrade.types.binance import AlgorithmOrderParams as BinanceAlgoOrderParams
from aiotrade.types.binance import AlgorithmOrderType as BinanceAlgorithmOrderType
from aiotrade.types.binance import CreateOrderParams as BinanceOrderParams
from aiotrade.types.binance import (
    StopTakeProfitAlgorithmOrderParams as BinanceTpSlOrderParams,
)
from aiotrade.types.bingx import PlaceSwapOrderParams as BingxSwapOrderParams
from aiotrade.types.bingx import TpSlStruct
from aiotrade.types.bitget import (
    BatchPlaceOrderItemParams as BitgetBatchOrderItemParams,
)
from aiotrade.types.bybit import PlaceOrderParams as BybitOrderParams
from aiotrade.types.gate import (
    FuturesPlaceOrder as GateOrderParams,
)
from aiotrade.types.gate import (
    FuturesPlaceTrailingOrder as GateTrailingOrderParams,
)
from aiotrade.types.gate import (
    FuturesPriceTriggeredOrder as GatePriceTriggeredOrderParams,
)
from aiotrade.types.kucoin import PlaceOrderParams as KuCoinOrderParams
from aiotrade.types.kucoin import (
    TakeProfitStopLossOrderParams as KuCoinTakeProfitStopLossOrderParams,
)
from aiotrade.types.okx import AttachAlgorithmOrderParams as OkxAlgorithmOrderParams
from aiotrade.types.okx import PlaceOrderParams as OkxOrderParams
from aiotrade.unified.types import (
    UnifiedPlaceOrderRequest,
    UnifiedSide,
)
from aiotrade.utils.formatters import float_to_str


def convert_unified_place_order_to_bingx(
    order: UnifiedPlaceOrderRequest,
) -> BingxSwapOrderParams:
    """Convert unified place order request to bingx format."""
    params = BingxSwapOrderParams(
        symbol=order["symbol"],
        side="BUY" if order["side"] == UnifiedSide.LONG else "SELL",
        order_type="MARKET" if order["order_type"] == "Market" else "LIMIT",
        quantity=order["qty"],
        position_side="BOTH",
    )
    if order["order_type"] == "Limit":
        params["time_in_force"] = "GTC"
    if (order_link_id := order.get("order_link_id")) is not None:
        params["client_order_id"] = order_link_id
    if (price := order.get("price")) is not None:
        params["price"] = price
    if (tp := order.get("take_profit")) is not None:
        params["take_profit"] = TpSlStruct(
            order_type="TAKE_PROFIT_MARKET",
            price=tp,
            stop_price=tp,
            working_type="CONTRACT_PRICE",
        )
    if (sl := order.get("stop_loss")) is not None:
        params["stop_loss"] = TpSlStruct(
            order_type="STOP_MARKET",
            price=sl,
            stop_price=sl,
            working_type="CONTRACT_PRICE",
        )
    if (reduce_only := order.get("reduce_only")) is not None:
        params["reduce_only"] = reduce_only
    return params


def convert_unified_place_order_to_bybit(
    order: UnifiedPlaceOrderRequest,
) -> BybitOrderParams:
    """Convert unified place order request to bybit format."""
    params = BybitOrderParams(
        symbol=order["symbol"],
        side="Buy" if order["side"] == UnifiedSide.LONG else "Sell",
        order_type=order["order_type"],
        qty=order["qty"],
        is_leverage=1,
        tpsl_mode="Full",
    )

    if order["order_type"] == "Limit":
        params["time_in_force"] = "GTC"
    if (price := order.get("price")) is not None:
        params["price"] = price
    if (order_link_id := order.get("order_link_id")) is not None:
        params["order_link_id"] = order_link_id
    if (tp := order.get("take_profit")) is not None:
        params["take_profit"] = tp
    if (sl := order.get("stop_loss")) is not None:
        params["stop_loss"] = sl
    if (reduce_only := order.get("reduce_only")) is not None:
        params["reduce_only"] = reduce_only
    return params


def convert_unified_place_order_to_bitget(
    order: UnifiedPlaceOrderRequest,
) -> BitgetBatchOrderItemParams:
    """Convert unified place spot order request to bybit format."""
    params = BitgetBatchOrderItemParams(
        size=order["qty"],
        side="buy" if order["side"] == UnifiedSide.LONG else "sell",
        orderType="market" if order["order_type"] == "Market" else "limit",
    )
    if order["order_type"] == "Limit":
        params["force"] = "gtc"
    if (price := order.get("price")) is not None:
        params["price"] = price
    if (order_link_id := order.get("order_link_id")) is not None:
        params["clientOid"] = order_link_id

    if (tp := order.get("take_profit")) is not None:
        params["presetStopSurplusPrice"] = tp
    if (sl := order.get("stop_loss")) is not None:
        params["presetStopLossPrice"] = sl
    if (reduce_only := order.get("reduce_only")) is not None:
        params["reduceOnly"] = "YES" if reduce_only else "NO"

    return params


def convert_unified_place_order_to_okx(
    order: UnifiedPlaceOrderRequest, broker_tag: str | None
) -> OkxOrderParams:
    """Convert unified place order request to okx format."""
    params = OkxOrderParams(
        instId=order["symbol"],
        tdMode="isolated",
        side="buy" if order["side"] == UnifiedSide.LONG else "sell",
        ordType="market" if order["order_type"] == "Market" else "limit",
        sz=order["qty"],
    )

    if broker_tag:
        params["tag"] = broker_tag

    if (price := order.get("price")) is not None:
        params["px"] = price
    if (order_link_id := order.get("order_link_id")) is not None:
        params["clOrdId"] = order_link_id.replace("_", "0")

    tp = order.get("take_profit")
    sl = order.get("stop_loss")
    if tp is not None or sl is not None:
        attached_tp_sl = OkxAlgorithmOrderParams()
        if tp is not None:
            attached_tp_sl["tpOrdKind"] = "condition"
            attached_tp_sl["tpOrdPx"] = -1
            attached_tp_sl["tpTriggerPx"] = tp
            attached_tp_sl["tpTriggerPxType"] = "last"
        if sl is not None:
            attached_tp_sl["slTriggerPx"] = sl
            attached_tp_sl["slOrdPx"] = -1
            attached_tp_sl["slTriggerPxType"] = "last"
        params["attachAlgoOrds"] = [attached_tp_sl]

    if (reduce_only := order.get("reduce_only")) is not None:
        params["reduceOnly"] = reduce_only
    return params


def convert_unified_place_order_to_binance(
    broker_id: str | None,
    order: UnifiedPlaceOrderRequest,
) -> tuple[list[BinanceOrderParams], list[BinanceAlgoOrderParams]]:
    """
    Convert unified place order request to Binance format.

    Returns a tuple of:
        (main simple orders, algo/conditional orders like TP/SL)
    """
    main_orders: list[BinanceOrderParams] = []
    algo_orders: list[BinanceAlgoOrderParams] = []

    # Main order (MARKET/LIMIT)
    main_params = BinanceOrderParams(
        symbol=order["symbol"],
        side="BUY" if order["side"] == UnifiedSide.LONG else "SELL",
        type="MARKET" if order["order_type"] == "Market" else "LIMIT",
        quantity=order["qty"],
    )
    tp_type: BinanceAlgorithmOrderType = (
        "TAKE_PROFIT_MARKET" if order["order_type"] == "Market" else "TAKE_PROFIT"
    )
    sl_type: BinanceAlgorithmOrderType = (
        "STOP_MARKET" if order["order_type"] == "Market" else "STOP"
    )
    if order["order_type"] == "Limit":
        main_params["timeInForce"] = "GTC"
        if (price := order.get("price")) is not None:
            main_params["price"] = price
    if (order_link_id := order.get("order_link_id")) is not None:
        main_params["newClientOrderId"] = BinanceClient.helpers.prepend_broker_id(
            broker_id, order_link_id
        )
    if (reduce_only := order.get("reduce_only")) is not None:
        main_params["reduceOnly"] = "true" if reduce_only else "false"

    main_orders.append(main_params)

    # Take Profit as a separate ALGO order if set
    if (tp := order.get("take_profit")) is not None:
        tp_algo = BinanceTpSlOrderParams(
            algoType="CONDITIONAL",
            symbol=order["symbol"],
            side="SELL" if order["side"] == UnifiedSide.LONG else "BUY",
            type=tp_type,
            positionSide="BOTH",
            workingType="CONTRACT_PRICE",
            triggerPrice=tp,
        )
        if tp_type == "TAKE_PROFIT":
            tp_algo["quantity"] = order["qty"]
            tp_algo["price"] = tp
            tp_algo["reduceOnly"] = "true"
        elif tp_type == "TAKE_PROFIT_MARKET":
            tp_algo["closePosition"] = "true"
        if (order_link_id := order.get("order_link_id")) is not None:
            base_order_id = BinanceClient.helpers.prepend_broker_id(
                broker_id, order_link_id, 33
            )
            algo_order_id = f"{base_order_id}_tp"
            tp_algo["clientAlgoId"] = algo_order_id
        algo_orders.append(tp_algo)

    # Stop Loss as a separate ALGO order if set
    if (sl := order.get("stop_loss")) is not None:
        sl_algo = BinanceTpSlOrderParams(
            algoType="CONDITIONAL",
            symbol=order["symbol"],
            side="SELL" if order["side"] == UnifiedSide.LONG else "BUY",
            type=sl_type,
            positionSide="BOTH",
            workingType="CONTRACT_PRICE",
            triggerPrice=sl,
        )
        if sl_type == "STOP":
            sl_algo["quantity"] = order["qty"]
            sl_algo["price"] = sl
            sl_algo["reduceOnly"] = "true"
        elif sl_type == "STOP_MARKET":
            sl_algo["closePosition"] = "true"
        if (order_link_id := order.get("order_link_id")) is not None:
            base_order_id = BinanceClient.helpers.prepend_broker_id(
                broker_id, order_link_id, 33
            )
            algo_order_id = f"{base_order_id}_sl"
            sl_algo["clientAlgoId"] = algo_order_id
        algo_orders.append(sl_algo)

    return main_orders, algo_orders


def convert_unified_place_order_to_kucoin(  # noqa: C901, PLR0912
    order: UnifiedPlaceOrderRequest,
) -> tuple[KuCoinOrderParams | None, KuCoinTakeProfitStopLossOrderParams | None]:
    """Convert a unified order to KuCoin's order model.

    If the order contains a trailing stop, should set standard TP.
    """
    side: Literal["buy", "sell"] = (
        "buy" if order["side"] == UnifiedSide.LONG else "sell"
    )
    order_type: Literal["market", "limit"] = (
        "market" if order["order_type"] == "Market" else "limit"
    )
    leverage = order["leverage"]
    tp = order.get("take_profit")
    sl = order.get("stop_loss")
    trailing_activate = order.get("active_price")

    has_tp_sl = tp is not None or sl is not None or trailing_activate is not None

    if has_tp_sl:
        tp_sl_params = KuCoinTakeProfitStopLossOrderParams(
            symbol=order["symbol"],
            side=side,
            type=order_type,
            leverage=int(leverage),
            marginMode="ISOLATED",
            size=int(order["qty"]),
            stopPriceType="TP",
        )
        if (order_link_id := order.get("order_link_id")) is not None:
            tp_sl_params["clientOid"] = order_link_id

        if order_type == "limit" and (price := order.get("price")) is not None:
            tp_sl_params["price"] = price

        # For long: tp -> up, sl -> down. For short: tp -> down, sl -> up.
        if order["side"] == UnifiedSide.LONG:
            # If trailing is set, always set triggerStopUpPrice as tp (standard TP)
            if tp is not None or trailing_activate is not None:
                if tp is not None:
                    tp_sl_params["triggerStopUpPrice"] = tp
                elif trailing_activate is not None:
                    tp_sl_params["triggerStopUpPrice"] = trailing_activate
            if sl is not None:
                tp_sl_params["triggerStopDownPrice"] = sl
        else:
            # SHORT
            # If trailing is set, always set triggerStopDownPrice as tp (standard TP)
            if tp is not None or trailing_activate is not None:
                if tp is not None:
                    tp_sl_params["triggerStopDownPrice"] = tp
                elif trailing_activate is not None:
                    tp_sl_params["triggerStopUpPrice"] = trailing_activate
            if sl is not None:
                tp_sl_params["triggerStopUpPrice"] = sl
        if (reduce_only := order.get("reduce_only")) is not None:
            tp_sl_params["reduceOnly"] = reduce_only

        return None, tp_sl_params

    # Если нет TP/SL - строим обычный KuCoinOrderParams для любого типа
    main_params = KuCoinOrderParams(
        symbol=order["symbol"],
        side=side,
        type=order_type,
        marginMode="ISOLATED",
        size=int(order["qty"]),
        positionSide="BOTH",
        leverage=int(leverage),
    )
    if (order_link_id := order.get("order_link_id")) is not None:
        main_params["clientOid"] = order_link_id
    if (price := order.get("price")) is not None:
        main_params["price"] = price
    if (reduce_only := order.get("reduce_only")) is not None:
        main_params["reduceOnly"] = reduce_only

    return main_params, None


def convert_unified_place_order_to_gate(  # noqa: C901, PLR0912
    order: UnifiedPlaceOrderRequest,
) -> tuple[
    GateOrderParams | None,
    list[GatePriceTriggeredOrderParams],
    list[GateTrailingOrderParams],
]:
    """
    Convert unified place order request to Gate.io format.

    Returns a tuple of:
        (main order for market, price trigger orders for limit/tp/sl, trailing orders)
    """
    main_order: GateOrderParams | None = None
    price_trigger_orders: list[GatePriceTriggeredOrderParams] = []
    trailing_orders: list[GateTrailingOrderParams] = []

    symbol = order["symbol"]
    qty = order["qty"]
    order_price = order.get("price")
    order_type = order["order_type"]
    side = order["side"]
    reduce_only = order.get("reduce_only", False)
    order_link_id = order.get("order_link_id", None)
    order_qty = qty if side == UnifiedSide.LONG else -qty
    # fix for bad gate parsing size field
    if order_qty.is_integer():
        order_qty = int(order_qty)

    # Market order (fills main_order, only for "Market" type)
    if order_type == "Market":
        main_order = GateOrderParams(
            contract=symbol,
            size=order_qty,
            price=0,
            tif="ioc",
        )
        if reduce_only:
            main_order["reduce_only"] = reduce_only
        if order_link_id is not None:
            main_order["text"] = "t-" + order_link_id

    # Limit order (fills price_trigger_orders)
    elif order_type == "Limit":
        if not order_price:
            raise ValueError("Limit order requires a price.")

        limit_order: GatePriceTriggeredOrderParams = {
            "initial": {
                "contract": symbol,
                "amount": float_to_str(order_qty),
                "price": float_to_str(order_price),
            },
            "trigger": {
                "price": float_to_str(order_price),
                "price_type": 0,
                "rule": 1 if side == UnifiedSide.LONG else 2,
            },
        }
        if reduce_only:
            limit_order["initial"]["reduce_only"] = reduce_only
        if order_link_id is not None:
            limit_order["initial"]["text"] = "t-" + order_link_id
        price_trigger_orders.append(limit_order)

    # Take Profit / Stop Loss triggers (always as price_trigger)
    # Take profit (tp)
    take_profit = order.get("take_profit")
    if take_profit is not None:
        tp_order: GatePriceTriggeredOrderParams = {
            "initial": {
                "contract": symbol,
                "price": "0",  # market order close as string
                "reduce_only": True,
                "tif": "ioc",
                "auto_size": "close",
            },
            "trigger": {
                "price": float_to_str(take_profit),
                "rule": 1 if side == UnifiedSide.LONG else 2,
            },
            "order_type": (
                "close-long-position"
                if side == UnifiedSide.LONG
                else "close-short-position"
            ),
        }
        if order_link_id is not None:
            tp_order["initial"]["text"] = f"{order_link_id}_tp"
        price_trigger_orders.append(tp_order)

    # Stop loss (sl)
    stop_loss = order.get("stop_loss")
    if stop_loss is not None:
        sl_order: GatePriceTriggeredOrderParams = {
            "initial": {
                "contract": symbol,
                "price": "0",  # market order close as string
                "reduce_only": True,
                "tif": "ioc",
                "auto_size": "close",
            },
            "trigger": {
                "price": float_to_str(stop_loss),
                "rule": 2 if side == UnifiedSide.LONG else 1,
            },
            "order_type": (
                "close-long-position"
                if side == UnifiedSide.LONG
                else "close-short-position"
            ),
        }
        if order_link_id is not None:
            sl_order["initial"]["text"] = f"{order_link_id}_sl"
        price_trigger_orders.append(sl_order)

    # Trailing stop (trail)
    trailing_activate = order.get("trailing_stop_activation", None)
    trailing_callback = order.get("trailing_stop_callback", None)
    if trailing_activate is not None and trailing_callback is not None:
        trail_order = GateTrailingOrderParams(
            contract=symbol,
            amount=qty if side == UnifiedSide.LONG else -qty,
            activation_price=str(trailing_activate),
            is_gte=side == UnifiedSide.LONG,
            price_offset=str(trailing_callback) + "%",
            reduce_only=True,
            position_related=True,
        )
        if order_link_id is not None:
            trail_order["text"] = f"{order_link_id}_trail"
        trailing_orders.append(trail_order)

    return main_order, price_trigger_orders, trailing_orders
