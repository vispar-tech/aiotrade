import logging
import math
from decimal import Decimal
from enum import StrEnum
from typing import Any, Literal, NotRequired, TypedDict, cast

from aiotrade import ExchangeLiteral as ExchangeKey
from aiotrade.types.binance import AlgorithmOrderParams as PlaceBinanceAlgoOrderParams
from aiotrade.types.binance import AlgorithmOrderType as BinanceAlgorithmOrderType
from aiotrade.types.binance import CreateOrderParams as PlaceBinanceOrderParams
from aiotrade.types.binance import MarginType as BinanceMarginMode
from aiotrade.types.binance import (
    StopTakeProfitAlgorithmOrderParams as PlaceBinanceTpSlOrderParams,
)
from aiotrade.types.bingx import MarginMode as BingxMarginMode
from aiotrade.types.bingx import PlaceSpotOrderParams as PlaceBingxSpotOrderParams
from aiotrade.types.bingx import PlaceSwapOrderParams as PlaceBingxSwapOrderParams
from aiotrade.types.bingx import TpSlStruct
from aiotrade.types.bitget import (
    BatchPlaceOrderItemParams as BatchPlaceBitgetOrderItemParams,
)
from aiotrade.types.bitget import MarginMode as BitgetMarginMode
from aiotrade.types.bybit import MarginMode as BybitMarginMode
from aiotrade.types.bybit import PlaceOrderParams as PlaceBybitOrderParams
from aiotrade.types.kucoin import MarginMode as KuCoinMarginMode
from aiotrade.types.kucoin import PlaceOrderParams as KuCoinPlaceOrderParams
from aiotrade.types.kucoin import (
    TakeProfitStopLossOrderParams as KuCoinTakeProfitStopLossOrderParams,
)
from aiotrade.types.okx import AttachAlgorithmOrderParams
from aiotrade.types.okx import PlaceOrderParams as PlaceOkxOrderParams

from .helpers import parse_decimal, parse_float

logger = logging.getLogger(__name__)

type ExchangeInstuments = tuple[
    float,  # symbol price
    "UnifiedInstrumentInfo",  # main instrument
    "UnifiedInstrumentInfo | None",  # demo instrument for bingx, okx, bitget
    "list[BybitRiskLimitInfo] | None",  # risk limits for bybit
]


class UnifiedMarginMode(StrEnum):
    """Unified margin mode enum for various exchanges."""

    CROSS = "CROSS"
    ISOLATED = "ISOLATED"
    OTHER = "OTHER"

    @property
    def _exchange_map(self) -> dict[str, dict["UnifiedMarginMode", str]]:
        return {
            "bybit": {
                UnifiedMarginMode.CROSS: "REGULAR_MARGIN",
                UnifiedMarginMode.ISOLATED: "ISOLATED_MARGIN",
            },
            "bingx": {
                UnifiedMarginMode.CROSS: "CROSSED",
                UnifiedMarginMode.ISOLATED: "ISOLATED",
            },
            "bitget": {
                UnifiedMarginMode.CROSS: "crossed",
                UnifiedMarginMode.ISOLATED: "isolated",
            },
            "binance": {
                UnifiedMarginMode.CROSS: "CROSSED",
                UnifiedMarginMode.ISOLATED: "ISOLATED",
            },
            "kucoin": {
                UnifiedMarginMode.CROSS: "CROSS",
                UnifiedMarginMode.ISOLATED: "ISOLATED",
            },
        }

    def to_exchange(self, exchange: str) -> str:
        """
        Return exchange-specific string value for this margin mode.
        `exchange` should be one of: 'bybit', 'bingx', 'bitget', 'binance', 'kucoin'
        """
        exchange = exchange.lower()
        try:
            return self._exchange_map[exchange][self]
        except KeyError as err:
            raise ValueError(
                f"Unsupported margin mode or exchange: {self} for {exchange}"
            ) from err

    # For backward compatibility with previous method names:
    def to_bybit(self) -> BybitMarginMode:
        return cast(BybitMarginMode, self.to_exchange("bybit"))

    def to_bingx(self) -> BingxMarginMode:
        return cast(BingxMarginMode, self.to_exchange("bingx"))

    def to_bitget(self) -> BitgetMarginMode:
        return cast(BitgetMarginMode, self.to_exchange("bitget"))

    def to_binance(self) -> BinanceMarginMode:
        return cast(BinanceMarginMode, self.to_exchange("binance"))

    def to_kucoin(self) -> KuCoinMarginMode:
        return cast(KuCoinMarginMode, self.to_exchange("kucoin"))


class UnifiedSide(StrEnum):
    """Unified representation of trade side (long/short)."""

    LONG = "LONG"
    SHORT = "SHORT"

    @staticmethod
    def from_exchange(side: str) -> "UnifiedSide":
        """
        Convert an exchange-specific side string to UnifiedSide.

        Handles all known exchange conventions (case-insensitive).
        """
        side_lower = side.lower()
        if side_lower in ("long", "buy"):
            return UnifiedSide.LONG
        if side_lower in ("short", "sell"):
            return UnifiedSide.SHORT
        raise ValueError(f"Unsupported exchange side: {side}")


class UnifiedPositionInfo(TypedDict):
    """Unified info for position data across exchanges."""

    id: str
    symbol: str
    side: UnifiedSide
    size: float
    avgPrice: float
    leverage: float
    markPrice: float
    realizedPnl: float
    unrealisedPnl: float
    liqPrice: float | None
    stopLoss: float | None
    trailingDelivation: float | None
    trailingActivatePrice: float | None
    takeProfit: float | None
    updatedTime: int
    source: ExchangeKey
    additional: NotRequired[dict[str, Any]]


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

    # size_str = str(data["positionAmt"])
    # decimals_count = len(size_str.split(".", 1)[1]) if "." in size_str else 0  # noqa: E501

    # position_value = float(data["positionValue"])
    # mark_price = float(data["markPrice"])
    # calculated_size: float = position_value / mark_price if mark_price else 0  # noqa: E501

    # size: float = (
    #     float(f"{round(calculated_size, decimals_count):.{decimals_count}f}")  # noqa: E501
    #     if mark_price and decimals_count > 0
    #     else calculated_size)
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
            trailing_stop = float(matching_trailing[0]["priceRate"])  # type: ignore
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
    updated_time = (
        int(data["currentTimestamp"]) if data.get("currentTimestamp") is not None else 0
    )

    # Collect algo orders (open_algo_orders is Kucoin TP/SL/trailing records)
    # Для Kucoin:
    #   Для SHORT позиции: SL если o['stop']=='up', TP если o['stop']=='down'
    #   Для LONG позиции: SL если o['stop']=='down', TP если o['stop']=='up'
    #   Трейлинг: stopPrice is None and price is not None

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
            or (matching_tp[0]["reduceOnly"] and matching_sl[0]["size"] == size)
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


class UnifiedOrderStatus(StrEnum):
    """Unified representation of order status across exchanges."""

    NEW = "NEW"
    FILLED = "FILLED"
    OTHER = "OTHER"

    @classmethod
    def from_exchange(cls, status: str) -> "UnifiedOrderStatus":
        """
        Convert exchange order status to UnifiedOrderStatus.

        Accepts status (str) as found in Bybit, BingX, Bitget, Okx, or Binance.
        """
        new_statuses = {"New", "Untriggered", "PENDING", "live", "NEW", "open"}
        filled_statuses = {"Filled", "FILLED", "filled", "done"}

        if status in new_statuses:
            return cls.NEW
        if status in filled_statuses:
            return cls.FILLED
        return cls.OTHER


class UnifiedOrderType(StrEnum):
    """Unified representation of order types across exchanges."""

    LIMIT = "LIMIT"
    MARKET = "MARKET"
    CONDITIONAL = "CONDITIONAL"
    OTHER = "OTHER"

    @classmethod
    def from_exchange(cls, status: str) -> "UnifiedOrderType":
        """
        Convert exchange order type to UnifiedOrderType.

        Accepts status (str) as found in Bybit, BingX, Bitget, Okx, or Binance.
        """
        market_types = {"Market", "MARKET", "market"}
        limit_types = {"Limit", "LIMIT", "limit"}
        conditional_types = {"CONDITIONAL"}

        if status in limit_types:
            return cls.LIMIT
        if status in market_types:
            return cls.MARKET
        if status in conditional_types:
            return cls.CONDITIONAL
        return cls.OTHER


class UnifiedPendingOrder(TypedDict):
    """Unified history order info across exchanges."""

    updatedTime: int
    createdTime: int
    orderStatus: UnifiedOrderStatus
    orderType: UnifiedOrderType
    orderId: int | str
    orderLinkId: str
    symbol: str
    side: UnifiedSide
    avgPrice: float | None
    qty: float
    source: ExchangeKey


def unified_history_order_from_bingx(order: dict[str, Any]) -> "UnifiedPendingOrder":
    """Create UnifiedPendingOrder from a BingX order dict."""
    return UnifiedPendingOrder(
        createdTime=int(order["time"]),
        updatedTime=int(order["updateTime"]),
        orderStatus=UnifiedOrderStatus.from_exchange(order["status"]),
        orderType=UnifiedOrderType.from_exchange(order["type"]),
        orderId=order["orderId"],
        orderLinkId=str(order["clientOrderId"]),
        symbol=str(order["symbol"]),
        side=UnifiedSide.from_exchange(order["side"]),
        avgPrice=parse_float(order["avgPrice"]),
        qty=float(order["executedQty"]),
        source="bingx",
    )


def unified_history_order_from_bybit(order: dict[str, Any]) -> "UnifiedPendingOrder":
    """Create UnifiedPendingOrder from a Bybit order dict."""
    return UnifiedPendingOrder(
        createdTime=int(order["createdTime"]),
        updatedTime=int(order["updatedTime"]),
        orderStatus=UnifiedOrderStatus.from_exchange(order["orderStatus"]),
        orderType=UnifiedOrderType.from_exchange(order["orderType"]),
        orderId=order["orderId"],
        orderLinkId=str(order["orderLinkId"]),
        symbol=str(order["symbol"]),
        side=UnifiedSide.from_exchange(order["side"]),
        avgPrice=parse_float(order["avgPrice"]),
        qty=float(order["cumExecQty"]),
        source="bybit",
    )


def unified_history_order_from_bitget(order: dict[str, Any]) -> "UnifiedPendingOrder":
    """Create UnifiedPendingOrder from a Bitget order dict."""
    return UnifiedPendingOrder(
        createdTime=int(order["cTime"]),
        updatedTime=int(order["uTime"]),
        orderStatus=UnifiedOrderStatus.from_exchange(order["status"]),
        orderType=UnifiedOrderType.from_exchange(order["orderType"]),
        orderId=order["orderId"],
        orderLinkId=str(order.get("clientOid", "")),
        symbol=str(order["symbol"]),
        side=UnifiedSide.from_exchange(order["side"]),
        avgPrice=parse_float(order.get("priceAvg") or order.get("price") or None),
        qty=float(order["size"]),
        source="bitget",
    )


def unified_history_order_from_okx(order: dict[str, Any]) -> "UnifiedPendingOrder":
    """Create UnifiedPendingOrder from an OKX order dict."""
    return UnifiedPendingOrder(
        createdTime=int(order["cTime"]),
        updatedTime=int(order["uTime"]),
        orderStatus=UnifiedOrderStatus.from_exchange(order["state"]),
        orderType=UnifiedOrderType.from_exchange(order["ordType"]),
        orderId=order["ordId"],
        orderLinkId=str(order.get("clOrdId", "")),
        symbol=str(order["instId"]),
        side=UnifiedSide.from_exchange(order["side"]),
        avgPrice=parse_float(order.get("avgPx") or order.get("px") or None),
        qty=float(order["sz"]),
        source="okx",
    )


def unified_history_order_from_binance(order: dict[str, Any]) -> "UnifiedPendingOrder":
    """Create UnifiedPendingOrder from a Binance order dict, checking required keys."""

    def get_first_existing(
        order: dict[str, Any],
        keys: list[str],
        required: bool = True,
        err_msg: str | None = None,
    ) -> Any:
        for k in keys:
            if k in order:
                return order[k]
        if required:
            raise ValueError(
                err_msg or f"None of required keys {keys} found in order: {order}"
            )
        return None

    created_time = get_first_existing(
        order,
        ["time", "createTime"],
        err_msg="Neither 'time' nor 'createTime' found in Binance order.",
    )
    updated_time = get_first_existing(
        order, ["updateTime"], err_msg="'updateTime' not found in Binance order."
    )
    order_status = get_first_existing(
        order,
        ["status", "algoStatus"],
        err_msg="Neither 'status' nor 'algoStatus' found in Binance order.",
    )
    order_type = get_first_existing(
        order,
        ["type", "algoType"],
        err_msg="Neither 'type' nor 'algoType' found in Binance order.",
    )
    order_id = get_first_existing(
        order,
        ["orderId", "algoId"],
        err_msg="Neither 'orderId' nor 'algoId' found in Binance order.",
    )
    order_link_id = get_first_existing(
        order,
        ["clientOrderId", "clientAlgoId"],
        err_msg="Neither 'clientOrderId' nor 'clientAlgoId' found in Binance order.",
    )
    symbol = get_first_existing(
        order, ["symbol"], err_msg="'symbol' not found in Binance order."
    )
    side = get_first_existing(
        order, ["side"], err_msg="'side' not found in Binance order."
    )

    # avgPrice logic: try price, then avgPrice, then activatePrice, then triggerPrice
    avg_price = None
    if "price" in order and order["price"] is not None:
        avg_price = parse_float(order["price"])
    for pkey in ["avgPrice", "activatePrice", "triggerPrice"]:
        if avg_price is None and pkey in order and order[pkey] is not None:
            avg_price = parse_float(order[pkey])

    # qty logic: try quantity, then executedQty, then origQty, else 0
    qty = None
    for qkey in ["quantity", "executedQty", "origQty"]:
        if qkey in order and order[qkey] is not None:
            q = parse_float(order[qkey])
            if q is not None:
                qty = q
                break
    if qty is None:
        qty = 0

    return UnifiedPendingOrder(
        createdTime=int(created_time),
        updatedTime=int(updated_time),
        orderStatus=UnifiedOrderStatus.from_exchange(order_status),
        orderType=UnifiedOrderType.from_exchange(order_type),
        orderId=order_id,
        orderLinkId=str(order_link_id),
        symbol=str(symbol),
        side=UnifiedSide.from_exchange(side),
        avgPrice=avg_price,
        qty=qty,
        source="binance",
    )


def unified_history_order_from_kucoin(order: dict[str, Any]) -> "UnifiedPendingOrder":
    """Create UnifiedPendingOrder from a KuCoin order dict."""

    # KuCoin orderId = `id`
    order_id = order["id"]
    # clientOid is optional
    order_link_id = str(order["clientOid"])

    # Symbol
    symbol = str(order["symbol"])

    # Side ('buy'/'sell')
    side = UnifiedSide.from_exchange(order["side"])

    # Status ("open" = active, "done" = completed/canceled)
    order_status = UnifiedOrderStatus.from_exchange(order["status"])

    # Order type ('limit', 'market', etc.)
    order_type = UnifiedOrderType.from_exchange(order["type"])

    # Created and updated
    created_time = int(order["createdAt"])
    updated_time = int(order["updatedAt"])

    # Average price: just use price
    avg_price = parse_float(order.get("price"))

    # Quantity: just use size
    size = parse_float(order.get("size"))
    if not size:
        raise ValueError(f"Missing or invalid order size in KuCoin order: {order}")

    return UnifiedPendingOrder(
        createdTime=created_time,
        updatedTime=updated_time,
        orderStatus=order_status,
        orderType=order_type,
        orderId=order_id,
        orderLinkId=order_link_id,
        symbol=symbol,
        side=side,
        avgPrice=avg_price,
        qty=size,
        source="kucoin",
    )


class UnifiedInstrumentInfo(TypedDict):
    """Unified instrument info."""

    symbol: str
    decimal_places: int
    price_precision: int
    tick_size: float
    qty_step: Decimal
    min_order_qty: Decimal
    max_order_qty: Decimal
    max_mkt_qty: Decimal
    max_notional: Decimal
    max_mkt_notional: Decimal
    max_absolute_margin: Decimal
    min_notional: Decimal
    min_leverage: float
    max_leverage: float
    additional: dict[str, Any]
    source: ExchangeKey


def unified_instrument_info_from_bingx(
    instrument: dict[str, Any],
) -> "UnifiedInstrumentInfo":
    """Create UnifiedInstrumentInfo from a BingX closed position."""
    qty_step_str = (
        "{:.20f}".format(10 ** -instrument["quantityPrecision"]).rstrip("0").rstrip(".")
    )
    decimal_places = len(qty_step_str.split(".")[1]) if "." in qty_step_str else 0
    return UnifiedInstrumentInfo(
        symbol=instrument["symbol"],
        decimal_places=decimal_places,
        price_precision=instrument["pricePrecision"],
        tick_size=10 ** -instrument["pricePrecision"],
        qty_step=parse_decimal(10 ** -instrument["quantityPrecision"]),
        min_order_qty=parse_decimal(instrument["tradeMinQuantity"]),
        max_order_qty=Decimal("inf"),
        max_mkt_qty=Decimal("inf"),
        max_notional=Decimal("inf"),
        max_mkt_notional=Decimal("inf"),
        max_absolute_margin=Decimal("inf"),
        min_notional=parse_decimal(instrument["tradeMinUSDT"]),
        min_leverage=1,
        max_leverage=float("inf"),
        additional={},
        source="bingx",
    )


def unified_instrument_info_from_bitget(
    instrument: dict[str, Any],
) -> "UnifiedInstrumentInfo":
    """Create UnifiedInstrumentInfo from a Bitget futures instrument."""
    return UnifiedInstrumentInfo(
        symbol=instrument["symbol"],
        decimal_places=int(instrument["volumePlace"]),
        price_precision=int(instrument["pricePlace"]),
        tick_size=10 ** -int(instrument["pricePlace"]),
        qty_step=parse_decimal(instrument["sizeMultiplier"]),
        min_order_qty=parse_decimal(instrument["minTradeNum"]),
        max_order_qty=(
            Decimal("inf")
            if instrument["maxOrderQty"] == ""
            else parse_decimal(instrument["maxOrderQty"])
        ),
        max_mkt_qty=(
            Decimal("inf")
            if instrument["maxMarketOrderQty"] == ""
            else parse_decimal(instrument["maxMarketOrderQty"])
        ),
        max_notional=Decimal("inf"),
        max_mkt_notional=Decimal("inf"),
        max_absolute_margin=Decimal("inf"),
        min_notional=parse_decimal(instrument["minTradeUSDT"]),
        min_leverage=float(instrument["minLever"]),
        max_leverage=float(instrument["maxLever"]),
        additional={},
        source="bitget",
    )


def unified_instrument_info_from_binance(
    instrument: dict[str, Any],
) -> "UnifiedInstrumentInfo":
    """Create UnifiedInstrumentInfo from a binance futures instrument."""

    # Helper to extract filter
    def get_filter(filter_type: str) -> dict[str, Any]:
        default: dict[str, Any] = {}
        for f in instrument.get("filters", []):
            if f.get("filterType") == filter_type:
                return f
        return default

    price_filter = get_filter("PRICE_FILTER")
    lot_size_filter = get_filter("LOT_SIZE")
    market_lot_size_filter = get_filter("MARKET_LOT_SIZE")
    min_notional_filter = get_filter("MIN_NOTIONAL")
    tick_sz = price_filter.get("tickSize", "1")
    price_precision = 0
    if "." in tick_sz:
        price_precision = len(tick_sz.rstrip("0").split(".")[1])

    return UnifiedInstrumentInfo(
        symbol=instrument["symbol"],
        decimal_places=int(instrument["quantityPrecision"]),
        price_precision=price_precision,
        tick_size=float(price_filter.get("tickSize", "1")),
        qty_step=parse_decimal(lot_size_filter.get("stepSize", "1")),
        min_order_qty=parse_decimal(lot_size_filter.get("minQty", "0")),
        max_order_qty=parse_decimal(lot_size_filter.get("maxQty", "0")),
        max_mkt_qty=parse_decimal(market_lot_size_filter.get("maxQty", "0")),
        max_notional=Decimal("inf"),
        max_mkt_notional=Decimal("inf"),
        max_absolute_margin=Decimal("inf"),
        min_notional=parse_decimal(min_notional_filter.get("notional", "0")),
        min_leverage=1,
        max_leverage=float("inf"),
        additional={},
        source="binance",
    )


def unified_instrument_info_from_okx(
    instrument: dict[str, Any],
) -> "UnifiedInstrumentInfo":
    """Create UnifiedInstrumentInfo from a native OKX swap instrument response."""
    # For OKX: main fields directly at the top level
    tick_sz = instrument.get("tickSz") or "1"
    lot_sz = instrument.get("lotSz") or "1"
    min_sz = instrument.get("minSz") or "0"
    max_lmt_sz = instrument.get("maxLmtSz") or "0"
    max_mkt_sz = instrument.get("maxMktSz") or "0"
    price_precision = 0
    # price_precision (decimal places of tickSz)
    if "." in tick_sz:
        price_precision = len(tick_sz.rstrip("0").split(".")[1])
    symbol = instrument.get("instId", "")
    # Determine decimal_places for qty_step (lotSz)
    decimal_places = 0
    if "." in lot_sz:
        decimal_places = len(lot_sz.rstrip("0").split(".")[1])
    return UnifiedInstrumentInfo(
        symbol=symbol,
        decimal_places=decimal_places,
        price_precision=price_precision,
        tick_size=float(tick_sz),
        qty_step=parse_decimal(lot_sz),
        min_order_qty=parse_decimal(min_sz),
        max_order_qty=parse_decimal(max_lmt_sz),
        max_mkt_qty=parse_decimal(max_mkt_sz) if max_mkt_sz else Decimal("inf"),
        min_notional=Decimal("0"),
        max_notional=Decimal("inf"),
        max_mkt_notional=Decimal("inf"),
        max_absolute_margin=Decimal("inf"),
        min_leverage=1.0,  # OKX API doesn't specify min leverage, defaulting to 1.0
        max_leverage=float(instrument.get("lever", "100")),  # Max leverage as "lever"
        additional={
            "ct_val": parse_decimal(instrument["ctVal"]),
            "ct_mult": parse_decimal(instrument["ctMult"]),
        },
        source="okx",
    )


def unified_instrument_info_from_bybit(
    instrument: dict[str, Any],
) -> "UnifiedInstrumentInfo":
    """Create UnifiedInstrumentInfo from a Bybit closed position."""
    qty_step_str = (
        "{:.20f}".format(float(instrument["priceFilter"]["tickSize"]))
        .rstrip("0")
        .rstrip(".")
    )
    decimal_places = len(qty_step_str.split(".")[1]) if "." in qty_step_str else 0
    return UnifiedInstrumentInfo(
        symbol=instrument["symbol"],
        decimal_places=decimal_places,
        price_precision=int(instrument["priceScale"]),
        tick_size=float(instrument["priceFilter"]["tickSize"]),
        qty_step=parse_decimal(instrument["lotSizeFilter"]["qtyStep"]),
        min_order_qty=parse_decimal(instrument["lotSizeFilter"]["minOrderQty"]),
        max_order_qty=parse_decimal(instrument["lotSizeFilter"]["maxOrderQty"]),
        max_mkt_qty=parse_decimal(instrument["lotSizeFilter"]["maxMktOrderQty"]),
        min_notional=parse_decimal(instrument["lotSizeFilter"]["minNotionalValue"]),
        max_notional=Decimal("inf"),
        max_mkt_notional=Decimal("inf"),
        max_absolute_margin=Decimal("inf"),
        min_leverage=float(instrument["leverageFilter"]["minLeverage"]),
        max_leverage=float(instrument["leverageFilter"]["maxLeverage"]),
        additional={},
        source="bybit",
    )


class UnifiedSpotInstrumentInfo(TypedDict):
    """Unified spot instrument info."""

    symbol: str
    decimal_places: int
    price_precision: int
    tick_size: float
    qty_step: Decimal
    min_order_qty: Decimal
    max_order_qty: Decimal
    max_mkt_qty: Decimal | None
    min_notional: Decimal
    max_notional: Decimal
    max_mkt_notional: Decimal
    max_absolute_margin: Decimal
    additional: dict[str, Any]
    source: ExchangeKey


def unified_spot_instrument_info_from_bingx(
    instrument: dict[str, Any],
) -> "UnifiedSpotInstrumentInfo":
    """Create UnifiedSpotInstrumentInfo from a BingX spot instrument."""
    # Correctly determine decimal places even for scientific notation (e.g., 1e-06)
    qty_step_str = (
        "{:.20f}".format(float(instrument["stepSize"])).rstrip("0").rstrip(".")
    )
    decimal_places = len(qty_step_str.split(".")[1]) if "." in qty_step_str else 0

    return UnifiedSpotInstrumentInfo(
        symbol=instrument["symbol"],
        decimal_places=decimal_places,
        price_precision=abs(round(math.log10(instrument["tickSize"]))),
        tick_size=instrument["tickSize"],
        qty_step=parse_decimal(instrument["stepSize"]),
        min_order_qty=parse_decimal(instrument["minQty"]),
        max_order_qty=parse_decimal(instrument["maxQty"]),
        max_mkt_qty=Decimal("inf"),
        min_notional=parse_decimal(instrument["minNotional"]),
        max_notional=parse_decimal(instrument["maxNotional"]),
        max_mkt_notional=parse_decimal(instrument["maxMarketNotional"]),
        max_absolute_margin=Decimal("inf"),
        additional={},
        source="bingx",
    )


def unified_spot_instrument_info_from_bybit(
    instrument: dict[str, Any],
) -> "UnifiedSpotInstrumentInfo":
    """Create UnifiedSpotInstrumentInfo from a Bybit spot instrument."""
    qty_step_str = (
        "{:.20f}".format(float(instrument["priceFilter"]["tickSize"]))
        .rstrip("0")
        .rstrip(".")
    )
    decimal_places = len(qty_step_str.split(".")[1]) if "." in qty_step_str else 0
    return UnifiedSpotInstrumentInfo(
        symbol=instrument["symbol"],
        decimal_places=decimal_places,
        price_precision=round(math.log10(float(instrument["priceFilter"]["tickSize"]))),
        tick_size=float(instrument["priceFilter"]["tickSize"]),
        qty_step=parse_decimal(instrument["lotSizeFilter"]["basePrecision"]),
        min_order_qty=parse_decimal(instrument["lotSizeFilter"]["minOrderQty"]),
        max_order_qty=parse_decimal(instrument["lotSizeFilter"]["maxLimitOrderQty"]),
        max_mkt_qty=parse_decimal(instrument["lotSizeFilter"]["maxMarketOrderQty"]),
        min_notional=parse_decimal(instrument["lotSizeFilter"]["minOrderAmt"]),
        max_notional=Decimal("inf"),
        max_mkt_notional=Decimal("inf"),
        max_absolute_margin=Decimal("inf"),
        additional={},
        source="bybit",
    )


class UnifiedCancelOrderRequest(TypedDict):
    """Unified model for cancel order request."""

    symbol: str
    order_link_id: NotRequired[str]
    order_id: NotRequired[str | int]
    order_type: NotRequired[UnifiedOrderType]


class UnifiedPlaceOrderRequest(TypedDict):
    """Unified model for placing an order, compatible across supported exchanges."""

    symbol: str
    side: UnifiedSide
    price: NotRequired[float]
    qty: float
    leverage: NotRequired[int]
    order_link_id: NotRequired[str]
    order_type: Literal["Market", "Limit"]
    take_profit: NotRequired[float]
    stop_loss: NotRequired[float]
    active_price: NotRequired[float]
    trailing_stop: NotRequired[float]
    reduce_only: NotRequired[bool]


def convert_unified_to_bingx(
    order: UnifiedPlaceOrderRequest,
) -> PlaceBingxSwapOrderParams:
    """Convert unified place order request to bingx format."""
    params = PlaceBingxSwapOrderParams(
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


def convert_unified_to_bybit(order: UnifiedPlaceOrderRequest) -> PlaceBybitOrderParams:
    """Convert unified place order request to bybit format."""
    params = PlaceBybitOrderParams(
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


def convert_unified_to_bitget(
    order: UnifiedPlaceOrderRequest,
) -> BatchPlaceBitgetOrderItemParams:
    """Convert unified place spot order request to bybit format."""
    params = BatchPlaceBitgetOrderItemParams(
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


def convert_unified_to_okx(
    order: UnifiedPlaceOrderRequest, broker_tag: str | None
) -> PlaceOkxOrderParams:
    """Convert unified place order request to okx format."""
    params = PlaceOkxOrderParams(
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
        attached_tp_sl = AttachAlgorithmOrderParams()
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


def prepend_binance_broker_id(
    broker_id: str | None, order_link_id: str, max_length: int = 36
) -> str:
    """Add binance broker id to order link id."""
    if broker_id is not None:
        return ("x-" + broker_id + "-" + order_link_id)[:max_length]
    return order_link_id


def convert_unified_to_binance(
    broker_id: str | None,
    order: UnifiedPlaceOrderRequest,
) -> tuple[list[PlaceBinanceOrderParams], list[PlaceBinanceAlgoOrderParams]]:
    """
    Convert unified place order request to Binance format.

    Returns a tuple of:
        (main simple orders, algo/conditional orders like TP/SL)
    """
    main_orders: list[PlaceBinanceOrderParams] = []
    algo_orders: list[PlaceBinanceAlgoOrderParams] = []

    # Main order (MARKET/LIMIT)
    main_params = PlaceBinanceOrderParams(
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
        main_params["newClientOrderId"] = prepend_binance_broker_id(
            broker_id, order_link_id
        )
    if (reduce_only := order.get("reduce_only")) is not None:
        main_params["reduceOnly"] = "true" if reduce_only else "false"

    main_orders.append(main_params)

    # Take Profit as a separate ALGO order if set
    if (tp := order.get("take_profit")) is not None:
        tp_algo = PlaceBinanceTpSlOrderParams(
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
            tp_algo["clientAlgoId"] = (
                f"{prepend_binance_broker_id(broker_id, order_link_id, 33)}_tp"
            )
        algo_orders.append(tp_algo)

    # Stop Loss as a separate ALGO order if set
    if (sl := order.get("stop_loss")) is not None:
        sl_algo = PlaceBinanceTpSlOrderParams(
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
            sl_algo["clientAlgoId"] = (
                f"{prepend_binance_broker_id(broker_id, order_link_id, 33)}_sl"
            )
        algo_orders.append(sl_algo)

    return main_orders, algo_orders


def convert_unified_to_kucoin(
    order: UnifiedPlaceOrderRequest,
) -> tuple[
    "KuCoinPlaceOrderParams | None", "KuCoinTakeProfitStopLossOrderParams | None"
]:
    """
    Convert a unified order to KuCoin's order model.
    """
    side = "buy" if order["side"] == UnifiedSide.LONG else "sell"
    order_type = "market" if order["order_type"] == "Market" else "limit"

    leverage = order.get("leverage")
    if leverage is None:
        raise ValueError(
            "KuCoin requires a 'leverage' parameter in "
            "UnifiedPlaceOrderRequest for futures orders."
        )

    tp = order.get("take_profit")
    sl = order.get("stop_loss")

    if order_type == "market":
        tp_sl_params = KuCoinTakeProfitStopLossOrderParams(
            symbol=order["symbol"],
            side=side,
            type="market",
            leverage=leverage,
            qty=order["qty"],
            stopPriceType="TP",
        )
        if (order_link_id := order.get("order_link_id")) is not None:
            tp_sl_params["clientOid"] = order_link_id

        # For long: tp -> up, sl -> down. For short: tp -> down, sl -> up.
        if order["side"] == UnifiedSide.LONG:
            if tp is not None:
                tp_sl_params["triggerStopUpPrice"] = tp
            if sl is not None:
                tp_sl_params["triggerStopDownPrice"] = sl
        else:
            if tp is not None:
                tp_sl_params["triggerStopDownPrice"] = tp
            if sl is not None:
                tp_sl_params["triggerStopUpPrice"] = sl
        if (reduce_only := order.get("reduce_only")) is not None:
            tp_sl_params["reduceOnly"] = reduce_only
        return None, tp_sl_params

    if order_type == "limit":
        main_params = KuCoinPlaceOrderParams(
            symbol=order["symbol"],
            side=side,
            type=order_type,
            qty=order["qty"],
            positionSide="BOTH",
            leverage=leverage,
        )

        if (order_link_id := order.get("order_link_id")) is not None:
            main_params["clientOid"] = order_link_id
        if (price := order.get("price")) is not None:
            main_params["price"] = price
        if (reduce_only := order.get("reduce_only")) is not None:
            main_params["reduceOnly"] = reduce_only

        # TP/SL orders are not created for limit orders via this converter.
        return main_params, None

    raise ValueError(f"Unsupported order_type: {order_type}")


class UnifiedPlaceSpotOrderRequest(TypedDict):
    """Unified model for placing a spot order."""

    symbol: str
    side: UnifiedSide
    price: NotRequired[float]
    qty: float
    order_link_id: NotRequired[str]
    order_type: Literal["Market", "TakeProfit"]


def convert_unified_spot_to_bingx(
    order: UnifiedPlaceSpotOrderRequest,
) -> PlaceBingxSpotOrderParams:
    """Convert unified place spot order request to bingx format."""
    params = PlaceBingxSpotOrderParams(
        symbol=order["symbol"],
        side="BUY" if order["side"] == UnifiedSide.LONG else "SELL",
        order_type="MARKET" if order["order_type"] == "Market" else "TAKE_STOP_MARKET",
        quantity=order["qty"],
    )

    if (order_link_id := order.get("order_link_id")) is not None:
        params["new_client_order_id"] = order_link_id
    if (price := order.get("price")) is not None:
        if order["order_type"] == "Market":
            params["price"] = price
        else:
            params["stop_price"] = price
    return params


def convert_unified_spot_to_bybit(
    order: UnifiedPlaceSpotOrderRequest,
) -> PlaceBybitOrderParams:
    """Convert unified place spot order request to bybit format."""
    params = PlaceBybitOrderParams(
        symbol=order["symbol"],
        side="Buy" if order["side"] == UnifiedSide.LONG else "Sell",
        order_type="Market",
        qty=order["qty"],
        market_unit="baseCoin",
        is_leverage=0,
    )

    if order["order_type"] == "TakeProfit":
        params["tp_order_type"] = "Market"
        if (price := order.get("price")) is not None:
            params["trigger_price"] = price
        params["order_filter"] = "tpslOrder"

    if (price := order.get("price")) is not None:
        params["price"] = price
    if (order_link_id := order.get("order_link_id")) is not None:
        params["order_link_id"] = order_link_id

    return params


class BybitRiskLimitInfo(TypedDict):
    """Bybit risk limit info."""

    id: int
    initialMargin: str
    isLowestRisk: int
    maintenanceMargin: str
    maxLeverage: Decimal
    mmDeduction: str
    riskLimitValue: Decimal
    symbol: str
