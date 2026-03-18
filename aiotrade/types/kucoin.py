"""Type definitions for kucoin client."""

from typing import Literal, NotRequired, TypedDict

# Extracted literal types
MarginMode = Literal["ISOLATED", "CROSS"]
Side = Literal["buy", "sell"]
OrderType = Literal["limit", "market"]
StopType = Literal["down", "up"]
StopPriceType = Literal["TP", "MP", "IP"]
STPType = Literal["CN", "CO", "CB"]
TimeInForce = Literal["GTC", "IOC"]
PositionSide = Literal["BOTH", "LONG", "SHORT"]


# TypedDict for Place Order parameters
class PlaceOrderParams(TypedDict, total=False):
    """Params for placing a futures order."""

    clientOid: str
    symbol: str
    side: Side
    leverage: int
    type: OrderType
    remark: str
    stop: StopType
    stopPriceType: StopPriceType
    stopPrice: float  # need to str
    reduceOnly: bool
    closeOrder: bool
    forceHold: bool
    stp: STPType
    marginMode: MarginMode
    price: float  # need to str
    size: int
    qty: float  # need to str
    valueQty: float  # need to str
    timeInForce: TimeInForce
    postOnly: bool
    hidden: bool
    iceberg: bool
    visibleSize: float  # need to str
    positionSide: PositionSide


# TypedDict for Take Profit and Stop Loss Order parameters
class TakeProfitStopLossOrderParams(TypedDict, total=False):
    """Params for setting take profit or stop loss orders."""

    clientOid: str
    symbol: str
    side: Side
    leverage: int
    type: OrderType
    remark: str
    stopPriceType: StopPriceType
    reduceOnly: bool
    closeOrder: bool
    forceHold: bool
    stp: STPType
    marginMode: MarginMode
    price: float  # need to str
    size: int
    qty: float  # need to str
    valueQty: float  # need to str
    timeInForce: TimeInForce
    postOnly: bool
    hidden: bool
    iceberg: bool
    visibleSize: float  # need to str
    positionSide: PositionSide
    triggerStopUpPrice: float  # need to str
    triggerStopDownPrice: float  # need to str


class BatchCancelOrdersClientOid(TypedDict):
    """A single client id + symbol for batch cancellation."""

    symbol: str
    clientOid: str


class BatchCancelOrdersPayload(TypedDict, total=False):
    """Payload for batch cancelling orders."""

    orderIdsList: NotRequired[list[str]]
    clientOidsList: NotRequired[list[BatchCancelOrdersClientOid]]
