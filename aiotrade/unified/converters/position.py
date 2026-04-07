"""Converter functions for position data structures."""

import logging
from typing import Any

from aiotrade.unified.types import UnifiedPositionInfo, UnifiedSide
from aiotrade.utils import parse_float

logger = logging.getLogger("aiotrade.unified")


def unified_position_info_from_bybit(
    open_orders: list[dict[str, Any]], data: dict[str, Any]
) -> "UnifiedPositionInfo":
    """Convert Bybit position dict."""
    trailing_order = next(
        (
            order
            for order in open_orders
            if order["createType"] == "CreateByTrailingProfit"
            and order["qty"] == data["size"]
            and order["symbol"] == data["symbol"]
        ),
        None,
    )
    position_side = UnifiedSide.from_exchange(data["side"])
    trailing_delivation = parse_float(data["trailingStop"])
    trailing_activate_price: float | None = None
    if trailing_order is not None and trailing_delivation is not None:
        trailing_order_trigger_price = parse_float(trailing_order.get("triggerPrice"))
        if trailing_order_trigger_price is not None:
            if position_side == UnifiedSide.LONG:
                trailing_activate_price = (
                    trailing_order_trigger_price + trailing_delivation
                )
            else:
                trailing_activate_price = (
                    trailing_order_trigger_price - trailing_delivation
                )

    return UnifiedPositionInfo(
        id=str(data["seq"]) + "_" + data["symbol"],
        symbol=data["symbol"],
        side=UnifiedSide.from_exchange(data["side"]),
        size=float(data["size"]),
        avgPrice=float(data["avgPrice"]),
        leverage=float(data["leverage"]),
        markPrice=float(data["markPrice"]),
        realizedPnl=float(data["curRealisedPnl"]),
        unrealisedPnl=float(data["unrealisedPnl"]),
        liqPrice=parse_float(data["liqPrice"]),
        stopLoss=parse_float(data["stopLoss"]),
        trailingDelivation=trailing_delivation,
        trailingActivatePrice=trailing_activate_price,
        takeProfit=parse_float(data["takeProfit"]),
        updatedTime=int(data["updatedTime"]),
        source="bybit",
    )


def unified_position_info_from_bingx(  # noqa: PLR0912
    account_display: str,
    open_orders: list[dict[str, Any]],
    data: dict[str, Any],
) -> "UnifiedPositionInfo":
    """Convert BingX position dict."""
    position_side = data["positionSide"]
    position_id = data["positionId"]

    # Try to find open stop loss or take profit orders matching this position
    matching_tp: list[dict[str, Any]] = []
    matching_sl: list[dict[str, Any]] = []
    matching_trailing: list[dict[str, Any]] = []
    for order in open_orders:
        order_position_id = order.get("positionID")
        order_type = order.get("type")
        order_position_side = order.get("positionSide")
        if (
            str(order_position_id) == str(position_id)
            and position_side == order_position_side
        ):
            if order_type == "TAKE_PROFIT_MARKET":
                matching_tp.append(order)
            if order_type == "STOP_MARKET":
                matching_sl.append(order)
            if order_type == "TRAILING_TP_SL":
                matching_trailing.append(order)

    size = float(data["positionAmt"])

    # STOP LOSS
    if (
        matching_sl
        and len(matching_sl) == 1
        and (
            float(matching_sl[0]["origQty"]) == size
            or data["positionAmt"] == matching_sl[0]["origQty"]
        )
    ):
        stop_loss = float(matching_sl[0]["stopPrice"])
    else:
        if matching_sl and len(matching_sl) == 1:
            logger.info(
                "%s Found SL order but origQty mismatch for "
                "position_id=%s symbol=%s: order['origQty']=%s, "
                "size=%s",
                account_display,
                position_id,
                data["symbol"],
                matching_sl[0]["origQty"],
                size,
            )
        stop_loss = None

    # TRAILING STOP
    if (
        matching_trailing
        and len(matching_trailing) == 1
        and (
            float(matching_trailing[0]["origQty"]) == size
            or data["positionAmt"] == matching_trailing[0]["origQty"]
        )
    ):
        if matching_trailing[0]["price"] not in [None, ""]:
            trailing_stop = float(matching_trailing[0]["price"])
        else:
            trailing_stop = float(matching_trailing[0]["priceRate"])
        trailing_activate_price = float(matching_trailing[0]["actPrice"])
    else:
        if matching_trailing and len(matching_trailing) == 1:
            logger.info(
                "%s Found trailing stop order but origQty mismatch for "
                "position_id=%s symbol=%s: order['origQty']=%s, "
                "size=%s",
                account_display,
                position_id,
                data["symbol"],
                matching_trailing[0]["origQty"],
                size,
            )
        trailing_stop = None
        trailing_activate_price = None

    # TAKE PROFIT
    if (
        matching_tp
        and len(matching_tp) == 1
        and (
            float(matching_tp[0]["origQty"]) == size
            or data["positionAmt"] == matching_tp[0]["origQty"]
        )
    ):
        take_profit = float(matching_tp[0]["stopPrice"])
    else:
        if matching_tp and len(matching_tp) == 1:
            logger.info(
                "%s Found TP order but origQty mismatch for "
                "position_id=%s symbol=%s: order['origQty']=%s, "
                "size=%s",
                account_display,
                position_id,
                data["symbol"],
                matching_tp[0]["origQty"],
                size,
            )
        take_profit = None

    return UnifiedPositionInfo(
        id=position_id,
        symbol=data["symbol"],
        side=UnifiedSide.from_exchange(position_side),
        size=size,
        avgPrice=float(data["avgPrice"]),
        leverage=float(data["leverage"]),
        markPrice=float(data["markPrice"]),
        realizedPnl=float(data["realisedProfit"]),
        unrealisedPnl=float(data["unrealizedProfit"]),
        liqPrice=parse_float(data["liquidationPrice"]),
        stopLoss=stop_loss,
        trailingDelivation=trailing_stop,
        trailingActivatePrice=trailing_activate_price,
        takeProfit=take_profit,
        updatedTime=int(data["updateTime"]),
        source="bingx",
        additional={
            "matching_sl_orders": matching_sl,
            "matching_tp_orders": matching_tp,
            "matching_trailing_orders": matching_trailing,
        },
    )


def unified_position_info_from_bitget(
    account_display: str,
    open_orders: list[dict[str, Any]],
    data: dict[str, Any],
) -> "UnifiedPositionInfo":
    """
    Convert Bitget position dict to UnifiedPositionInfo.

    open_orders: entrustedList from get_pending_trigger_orders
    data: single position dict from get_all_positions
    """
    symbol = data["symbol"]
    position_side = data["holdSide"]
    position_id = f"{symbol}:{position_side}:{data['marginMode']}:{data['cTime']}"
    size = float(data["total"])
    avg_price = float(data["openPriceAvg"])
    leverage = float(data["leverage"])
    mark_price = float(data["markPrice"])
    realized_pnl = float(data["achievedProfits"])
    unrealized_pnl = float(data["unrealizedPL"])
    liq_price = parse_float(data["liquidationPrice"])

    side = UnifiedSide.LONG if position_side == "long" else UnifiedSide.SHORT

    # Filter orders by symbol, plan status "live"
    matching_tp = [
        o
        for o in open_orders
        if o["symbol"] == symbol
        and o["planType"] in {"pos_profit", "profit_plan"}
        and o["planStatus"] == "live"
    ]
    matching_sl = [
        o
        for o in open_orders
        if o["symbol"] == symbol
        and o["planType"] in {"pos_loss", "loss_plan"}
        and o["planStatus"] == "live"
    ]
    matching_trailing = [
        o
        for o in open_orders
        if o["symbol"] == symbol
        and o["planType"] == "moving_plan"
        and o["planStatus"] == "live"
    ]

    if matching_sl and len(matching_sl) > 1:
        logger.warning(
            "%s Multiple stop loss orders found for symbol %s: %s",
            account_display,
            symbol,
            matching_sl,
        )
    stop_loss = (
        float(matching_sl[0]["stopLossTriggerPrice"])
        if matching_sl
        and len(matching_sl) == 1
        and matching_sl[0]["planType"] == "pos_loss"
        else None
    )

    if matching_tp and len(matching_tp) > 1:
        logger.warning(
            "%s Multiple take profit orders found for symbol %s: %s",
            account_display,
            symbol,
            matching_tp,
        )
    take_profit = (
        float(matching_tp[0]["stopSurplusTriggerPrice"])
        if matching_tp
        and len(matching_tp) == 1
        and matching_tp[0]["planType"] == "pos_profit"
        else None
    )

    if matching_trailing and len(matching_trailing) > 1:
        logger.warning(
            "%s Multiple trailing stop orders found for symbol %s: %s",
            account_display,
            symbol,
            matching_trailing,
        )
    trailing_stop = (
        float(matching_trailing[0]["callbackRatio"])
        if matching_trailing
        and len(matching_trailing) == 1
        and float(matching_trailing[0]["size"]) == size
        else None
    )
    trailing_activate_price = (
        float(matching_trailing[0]["triggerPrice"])
        if matching_trailing
        and len(matching_trailing) == 1
        and float(matching_trailing[0]["size"]) == size
        else None
    )

    return UnifiedPositionInfo(
        id=position_id,
        symbol=symbol,
        side=side,
        size=size,
        avgPrice=avg_price,
        leverage=leverage,
        markPrice=mark_price,
        realizedPnl=realized_pnl,
        unrealisedPnl=unrealized_pnl,
        liqPrice=liq_price,
        stopLoss=stop_loss,
        trailingDelivation=trailing_stop,
        trailingActivatePrice=trailing_activate_price,
        takeProfit=take_profit,
        updatedTime=int(data["uTime"]),
        source="bitget",
        additional={
            "matching_sl_orders": matching_sl,
            "matching_tp_orders": matching_tp,
            "matching_trailing_orders": matching_trailing,
        },
    )


def unified_position_info_from_binance(
    account_display: str,
    open_algo_orders: list[dict[str, Any]],
    data: dict[str, Any],
) -> "UnifiedPositionInfo":
    """
    Convert Binance position dict and open algo orders to UnifiedPositionInfo.

    open_algo_orders: list from client.get_open_algo_orders()
    data: single position dict from client.get_position_info()
    """
    symbol = data["symbol"]
    position_side = data["positionSide"]
    position_id = f"{symbol}:{position_side}"
    size = float(data["positionAmt"])
    avg_price = float(data["entryPrice"])
    leverage = float(data["leverage"])
    mark_price = float(data["markPrice"])
    # NOTE: determine realizedPnl (not present in Binance pos model example)
    realized_pnl = 0
    unrealized_pnl = float(data["unRealizedProfit"])
    liq_price = (
        parse_float(data["liquidationPrice"]) if "liquidationPrice" in data else None
    )

    # Determine side from position amount sign
    if size > 0:
        side = UnifiedSide.LONG
    elif size < 0:
        side = UnifiedSide.SHORT
    else:
        # Binance will return size==0 for closed pos
        side = UnifiedSide.LONG  # default fallback, could also use None

    size = abs(size)

    # Simple filter for open_algo_orders of correct symbol & position_side & status
    def _matching_orders(order_types: set[str]) -> list[dict[str, Any]]:
        return [
            o
            for o in open_algo_orders
            if o.get("symbol") == symbol
            and o.get("positionSide", "BOTH") == position_side
            and o.get("algoStatus", "").upper() in ("NEW", "TRIGGERED")
            and o.get("orderType") in order_types
        ]

    matching_tp = _matching_orders({"TAKE_PROFIT_MARKET", "TAKE_PROFIT"})
    matching_sl = _matching_orders({"STOP_MARKET", "STOP"})
    matching_trailing = _matching_orders({"TRAILING_STOP_MARKET"})

    if matching_sl and len(matching_sl) > 1:
        logger.warning(
            "%s Multiple stop loss orders found for symbol %s: %s",
            account_display,
            symbol,
            matching_sl,
        )
    stop_loss = (
        parse_float(matching_sl[0]["triggerPrice"])
        if matching_sl
        and len(matching_sl) == 1
        and (
            float(matching_sl[0]["quantity"]) == size or matching_sl[0]["closePosition"]
        )
        else None
    )

    if matching_tp and len(matching_tp) > 1:
        logger.warning(
            "%s Multiple take profit orders found for symbol %s: %s",
            account_display,
            symbol,
            matching_tp,
        )
    take_profit = (
        parse_float(matching_tp[0]["triggerPrice"])
        if matching_tp
        and len(matching_tp) == 1
        and (
            float(matching_tp[0]["quantity"]) == size or matching_tp[0]["closePosition"]
        )
        else None
    )

    if matching_trailing and len(matching_trailing) > 1:
        logger.warning(
            "%s Multiple trailing stop orders found for symbol %s: %s",
            account_display,
            symbol,
            matching_trailing,
        )
    trailing_stop = (
        parse_float(matching_trailing[0]["callbackRate"])
        if matching_trailing
        and len(matching_trailing) == 1
        and float(matching_trailing[0]["quantity"]) == size
        else None
    )
    trailing_activate_price = (
        parse_float(matching_trailing[0]["activatePrice"])
        if matching_trailing
        and len(matching_trailing) == 1
        and float(matching_trailing[0]["quantity"]) == size
        else None
    )

    return UnifiedPositionInfo(
        id=position_id,
        symbol=symbol,
        side=side,
        size=size,
        avgPrice=avg_price,
        leverage=leverage,
        markPrice=mark_price,
        realizedPnl=realized_pnl,  # TODO: determine realizedPnl
        unrealisedPnl=unrealized_pnl,
        liqPrice=liq_price,
        stopLoss=stop_loss,
        trailingDelivation=trailing_stop,
        trailingActivatePrice=trailing_activate_price,
        takeProfit=take_profit,
        updatedTime=int(data["updateTime"]) if "updateTime" in data else 0,
        source="binance",
        additional={
            "matching_sl_orders": matching_sl,
            "matching_tp_orders": matching_tp,
            "matching_trailing_orders": matching_trailing,
        },
    )


def unified_position_info_from_okx(
    account_display: str,
    open_algo_orders: list[dict[str, Any]],
    data: dict[str, Any],
) -> "UnifiedPositionInfo":
    """
    Convert OKX position dict and related algo orders to UnifiedPositionInfo.

    open_algo_orders: List from get_algo_orders_pending
    data: single position dict from get_positions
    """
    symbol = data["instId"]
    position_id = data["posId"] if data["posId"] else f"{symbol}:{data['posSide']}"
    inst_type = data["instType"].upper()
    ccy_side = data["posSide"]

    size = float(data["pos"])

    # Determine side/real_side based on OKX conventions as per the user example
    if inst_type in ("FUTURES", "SWAP", "OPTION"):
        if size > 0:
            side = UnifiedSide.LONG
        elif size < 0:
            side = UnifiedSide.SHORT
        else:
            raise NotImplementedError(
                f"{account_display} Can`t handle {size} of position "
                "to determine pos side"
            )
    elif inst_type == "MARGIN":
        pos_ccy = data["posCcy"]
        base_ccy = symbol.split("-")[0] if symbol else "?"
        side = UnifiedSide.LONG if pos_ccy == base_ccy else UnifiedSide.SHORT
    else:
        raise NotImplementedError(
            f"{account_display} Can`t handle {inst_type} for determine pos side"
        )

    avg_price = float(data["avgPx"])
    leverage = float(data["lever"])
    mark_price = float(data["markPx"])
    realized_pnl = float(data["realizedPnl"])
    unrealized_pnl = float(data["upl"])
    liq_price = parse_float(data["liqPx"])

    # Collect algo orders for this symbol & posSide
    def _matches(ord_: dict[str, Any], plan_type: set[str] | str | None) -> bool:
        # OKX trailing stop uses "move_order_stop", TP/SL both in "conditional"
        return (
            ord_["instId"] == symbol
            and ord_.get("state") == "live"
            and (
                plan_type is None
                or (isinstance(plan_type, set) and ord_.get("ordType") in plan_type)
                or (not isinstance(plan_type, set) and ord_.get("ordType") == plan_type)
            )
            and (ord_.get("posSide") == ccy_side or not ord_.get("posSide"))
        )

    matching_tp = [
        o
        for o in open_algo_orders
        if _matches(o, {"conditional", "oco"})
        and o.get("tpTriggerPx")
        and o["tpTriggerPx"] not in ("", "0")
    ]

    matching_sl = [
        o
        for o in open_algo_orders
        if _matches(o, {"conditional", "oco"})
        and o.get("slTriggerPx")
        and o["slTriggerPx"] not in ("", "0")
    ]

    matching_trailing = [
        o
        for o in open_algo_orders
        if _matches(o, "move_order_stop")
        and o.get("callbackRatio")
        and o["callbackRatio"] != ""
    ]

    if matching_sl and len(matching_sl) > 1:
        logger.warning(
            "%s Multiple stop loss orders found for symbol %s: %s",
            account_display,
            symbol,
            matching_sl,
        )
    stop_loss = (
        float(matching_sl[0]["slTriggerPx"])
        if matching_sl
        and len(matching_sl) == 1
        and matching_sl[0]["closeFraction"] == "1"
        else None
    )

    if matching_tp and len(matching_tp) > 1:
        logger.warning(
            "%s Multiple take profit orders found for symbol %s: %s",
            account_display,
            symbol,
            matching_tp,
        )
    take_profit = (
        float(matching_tp[0]["tpTriggerPx"])
        if matching_tp
        and len(matching_tp) == 1
        and matching_tp[0]["closeFraction"] == "1"
        else None
    )

    if matching_trailing and len(matching_trailing) > 1:
        logger.warning(
            "%s Multiple trailing stop orders found for symbol %s: %s",
            account_display,
            symbol,
            matching_trailing,
        )
    trailing_stop = (
        float(matching_trailing[0]["callbackRatio"])
        if matching_trailing
        and len(matching_trailing) == 1
        and abs(float(matching_trailing[0]["sz"])) == abs(size)
        else None
    )
    trailing_activate_price = (
        float(matching_trailing[0]["activePx"])
        if matching_trailing
        and len(matching_trailing) == 1
        and matching_trailing[0].get("activePx")
        and abs(float(matching_trailing[0]["sz"])) == abs(size)
        else None
    )

    return UnifiedPositionInfo(
        id=position_id,
        symbol=symbol,
        side=side,
        size=abs(size),
        avgPrice=avg_price,
        leverage=leverage,
        markPrice=mark_price,
        realizedPnl=realized_pnl,
        unrealisedPnl=unrealized_pnl,
        liqPrice=liq_price,
        stopLoss=stop_loss,
        trailingDelivation=trailing_stop,
        trailingActivatePrice=trailing_activate_price,
        takeProfit=take_profit,
        updatedTime=int(data["uTime"]),
        source="okx",
        additional={
            "raw_pos_side": ccy_side,
            "inst_type": inst_type,
            "margin_mode": data["mgnMode"],
            "matching_sl_orders": matching_sl,
            "matching_tp_orders": matching_tp,
            "matching_trailing_orders": matching_trailing,
        },
    )


def unified_position_info_from_kucoin(
    account_display: str,
    open_algo_orders: list[dict[str, Any]],
    data: dict[str, Any],
) -> "UnifiedPositionInfo":
    """
    Convert KuCoin position dict and open algo orders to UnifiedPositionInfo.

    Parses TP/SL/trailing from open_algo_orders like in okx.
    """
    symbol = data["symbol"]
    position_id = str(data["id"])

    size = float(data["currentQty"])
    side = UnifiedSide.SHORT if size < 0 else UnifiedSide.LONG
    size = abs(size)

    avg_price = float(data["avgEntryPrice"])
    leverage = float(data["leverage"])
    mark_price = float(data["markPrice"])
    realized_pnl = float(data["realisedPnl"])
    unrealized_pnl = float(data["unrealisedPnl"])
    liq_price = (
        float(data["liquidationPrice"])
        if data["liquidationPrice"] is not None
        else None
    )
    updated_time = int(data["openingTimestamp"])

    # Collect algo orders (open_algo_orders is Kucoin TP/SL/trailing records)
    # Для Kucoin:
    #   Для SHORT позиции: SL если o['stop']=='up', TP если o['stop']=='down'
    #   Для LONG позиции: SL если o['stop']=='down', TP если o['stop']=='up'
    #   Трейлинг: stopPrice None and price not None

    def _is_valid_order(o: dict[str, Any]) -> bool:
        return (
            o.get("symbol") == symbol
            and o.get("isActive", False)
            and o.get("stopPriceType") == "TP"
            and o.get("stopPrice") is not None
            and o.get("stopPrice") not in ("", "0")
        )

    # Detect trailing orders for KuCoin (stopPrice is None and price is not None)
    def _is_trailing_order(o: dict[str, Any]) -> bool:
        return (
            o.get("symbol") == symbol
            and o.get("isActive", False)
            and o.get("stopPriceType") == "TP"
            and (
                (
                    o.get("stopPrice") in (None, "", "0")
                    and o.get("price") not in (None, "", "0")
                )
                or (
                    o.get("stopPrice") in (None, "", "0")
                    and o.get("price") in (None, "", "0")
                )
            )
        )

    if side == UnifiedSide.SHORT:
        matching_sl = [
            o for o in open_algo_orders if _is_valid_order(o) and o.get("stop") == "up"
        ]
        matching_tp = [
            o
            for o in open_algo_orders
            if _is_valid_order(o) and o.get("stop") == "down"
        ]
        matching_trailing = [
            o
            for o in open_algo_orders
            if _is_trailing_order(o) and o.get("stop") == "up"
        ]
    else:  # LONG
        matching_sl = [
            o
            for o in open_algo_orders
            if _is_valid_order(o) and o.get("stop") == "down"
        ]
        matching_tp = [
            o for o in open_algo_orders if _is_valid_order(o) and o.get("stop") == "up"
        ]

        matching_trailing = [
            o
            for o in open_algo_orders
            if _is_trailing_order(o) and o.get("stop") == "down"
        ]

    if matching_sl and len(matching_sl) > 1:
        logger.warning(
            "%s Multiple stop loss orders found for symbol %s: %s",
            account_display,
            symbol,
            matching_sl,
        )
    stop_loss = (
        float(matching_sl[0]["stopPrice"])
        if matching_sl
        and len(matching_sl) == 1
        and (
            matching_sl[0]["closeOrder"]
            or (matching_sl[0]["reduceOnly"] and matching_sl[0]["size"] == size)
        )
        else None
    )

    if matching_tp and len(matching_tp) > 1:
        logger.warning(
            "%s Multiple take profit orders found for symbol %s: %s",
            account_display,
            symbol,
            matching_tp,
        )
    take_profit = (
        float(matching_tp[0]["stopPrice"])
        if matching_tp
        and len(matching_tp) == 1
        and (
            matching_tp[0]["closeOrder"]
            or (matching_tp[0]["reduceOnly"] and matching_tp[0]["size"] == size)
        )
        else None
    )

    if matching_trailing and len(matching_trailing) > 1:
        logger.warning(
            "%s Multiple trailing stop orders found for symbol %s: %s",
            account_display,
            symbol,
            matching_trailing,
        )

    trailing_delivation = None
    trailing_activate_price = (
        float(matching_trailing[0]["price"])
        if matching_trailing
        and len(matching_trailing) == 1
        and matching_trailing[0]["reduceOnly"]
        and float(matching_trailing[0]["price"]) != 0
        and abs(matching_trailing[0]["size"]) == size
        else None
    )

    return UnifiedPositionInfo(
        id=position_id,
        symbol=symbol,
        side=side,
        size=size,
        avgPrice=avg_price,
        leverage=leverage,
        markPrice=mark_price,
        realizedPnl=realized_pnl,
        unrealisedPnl=unrealized_pnl,
        liqPrice=liq_price,
        stopLoss=stop_loss,
        trailingDelivation=trailing_delivation,
        trailingActivatePrice=trailing_activate_price,
        takeProfit=take_profit,
        updatedTime=updated_time,
        source="kucoin",
        additional={
            "matching_sl_orders": matching_sl,
            "matching_tp_orders": matching_tp,
            "matching_trailing_orders": matching_trailing,
        },
    )
