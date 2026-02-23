"""Type definitions for bitget client."""

from typing import Literal, NotRequired, TypedDict

ProductType = Literal[
    "USDT-FUTURES",
    "COIN-FUTURES",
    "USDC-FUTURES",
]

MarginMode = Literal["isolated", "crossed"]
Side = Literal["buy", "sell"]
OrderType = Literal["limit", "market"]
TradeSide = Literal["open", "close"]
TimeInForce = Literal["ioc", "fok", "gtc", "post_only"]
ReduceOnly = Literal["YES", "NO"]
StpMode = Literal["none", "cancel_taker", "cancel_maker", "cancel_both"]


class PlaceOrderParams(TypedDict, total=False):
    """Parameters for placing a futures order.

    Ignore tradeSide when in one-way position mode. In hedge-mode,
    tradeSide is required.
    """

    symbol: str
    productType: ProductType
    marginMode: MarginMode
    marginCoin: str
    size: float
    side: Side
    orderType: OrderType

    price: NotRequired[float]
    tradeSide: NotRequired[TradeSide]
    force: NotRequired[TimeInForce]
    clientOid: NotRequired[str]
    reduceOnly: NotRequired[ReduceOnly]
    presetStopSurplusPrice: NotRequired[float]
    presetStopLossPrice: NotRequired[float]
    presetStopSurplusExecutePrice: NotRequired[float]
    presetStopLossExecutePrice: NotRequired[float]
    stpMode: NotRequired[StpMode]


class BatchPlaceOrderItemParams(TypedDict, total=False):
    """Parameters for a single order in batch place order. Used in orderList."""

    size: float
    side: Side
    orderType: OrderType

    price: NotRequired[float]
    tradeSide: NotRequired[TradeSide]
    force: NotRequired[TimeInForce]
    clientOid: NotRequired[str]
    reduceOnly: NotRequired[ReduceOnly]
    presetStopSurplusPrice: NotRequired[float]
    presetStopLossPrice: NotRequired[float]
    stpMode: NotRequired[StpMode]


class CancelOrderParams(TypedDict, total=False):
    """Parameters for canceling an order. Either orderId or clientOid required."""

    symbol: str
    productType: ProductType

    orderId: NotRequired[str]
    clientOid: NotRequired[str]
    marginCoin: NotRequired[str]


class GetPendingTriggerOrdersParams(TypedDict, total=False):
    """Params for querying pending trigger/plan orders."""

    productType: ProductType
    planType: Literal[
        "normal_plan",
        "track_plan",
        "profit_loss",
        "profit_plan",
        "loss_plan",
        "moving_plan",
        "pos_profit",
        "pos_loss",
    ]
    orderId: str
    clientOid: str
    symbol: str
    idLessThan: str
    startTime: int
    endTime: int
    limit: int


class CancelTriggerOrderItem(TypedDict, total=False):
    """Order ID/client OID item for canceling trigger orders."""

    orderId: str
    clientOid: str


class PlaceTriggerOrderParams(TypedDict, total=False):
    """Params for placing a trigger/plan order."""

    planType: Literal["normal_plan", "track_plan"]
    symbol: str
    productType: ProductType
    marginMode: Literal["isolated", "crossed"]
    marginCoin: str
    size: float
    price: NotRequired[float]
    callbackRatio: NotRequired[float]
    triggerPrice: float
    triggerType: Literal["mark_price", "fill_price"]
    side: Literal["buy", "sell"]
    tradeSide: NotRequired[Literal["open", "close"]]
    orderType: Literal["limit", "market"]
    clientOid: NotRequired[str]
    reduceOnly: NotRequired[Literal["yes", "no"]]
    stopSurplusTriggerPrice: NotRequired[float]
    stopSurplusExecutePrice: NotRequired[float]
    stopSurplusTriggerType: NotRequired[Literal["fill_price", "mark_price"]]
    stopLossTriggerPrice: NotRequired[float]
    stopLossExecutePrice: NotRequired[float]
    stopLossTriggerType: NotRequired[Literal["fill_price", "mark_price"]]
    stpMode: NotRequired[Literal["none", "cancel_taker", "cancel_maker", "cancel_both"]]


class PlaceTpslPlanOrderParams(TypedDict, total=False):
    """Params for placing a TP/SL plan order."""

    marginCoin: str
    productType: ProductType
    symbol: str
    planType: Literal[
        "profit_plan",
        "loss_plan",
        "moving_plan",
        "pos_profit",
        "pos_loss",
    ]
    triggerPrice: float
    triggerType: Literal["fill_price", "mark_price"]
    executePrice: float
    holdSide: Literal["long", "short", "buy", "sell"]
    size: float
    rangeRate: float
    clientOid: str
    stpMode: Literal["none", "cancel_taker", "cancel_maker", "cancel_both"]


class PlaceSpotOrderParams(TypedDict, total=False):
    """Params for placing a spot order."""

    symbol: str
    side: Literal["buy", "sell"]
    orderType: Literal["limit", "market"]
    force: NotRequired[Literal["gtc", "post_only", "fok", "ioc"]]
    price: NotRequired[float]
    size: float
    clientOid: NotRequired[str]
    triggerPrice: NotRequired[float]
    tpslType: NotRequired[Literal["normal", "tpsl"]]
    requestTime: NotRequired[int]
    receiveWindow: NotRequired[int]
    stpMode: NotRequired[Literal["none", "cancel_taker", "cancel_maker", "cancel_both"]]
    presetTakeProfitPrice: NotRequired[float]
    executeTakeProfitPrice: NotRequired[float]
    presetStopLossPrice: NotRequired[float]
    executeStopLossPrice: NotRequired[float]


class BatchSpotOrderItemParams(TypedDict, total=False):
    """Params for a single spot order in a batch."""

    symbol: NotRequired[str]
    side: Literal["buy", "sell"]
    orderType: Literal["limit", "market"]
    force: NotRequired[Literal["gtc", "post_only", "fok", "ioc"]]
    price: NotRequired[float]
    size: float
    clientOid: NotRequired[str]
    stpMode: NotRequired[Literal["none", "cancel_taker", "cancel_maker", "cancel_both"]]
    presetTakeProfitPrice: NotRequired[float]
    executeTakeProfitPrice: NotRequired[float]
    presetStopLossPrice: NotRequired[float]
    executeStopLossPrice: NotRequired[float]


class BatchPlaceSpotOrderParams(TypedDict, total=False):
    """Params for placing batch spot orders."""

    symbol: NotRequired[str]
    batchMode: NotRequired[Literal["single", "multiple"]]
    orderList: list[BatchSpotOrderItemParams]


class BatchCancelSpotOrderItemParams(TypedDict, total=False):
    """Params for a single spot order to cancel in a batch."""

    symbol: NotRequired[str]
    orderId: NotRequired[str]
    clientOid: NotRequired[str]


class BatchCancelSpotOrderParams(TypedDict, total=False):
    """Params for batch cancellation of spot orders."""

    symbol: NotRequired[str]
    batchMode: NotRequired[Literal["single", "multiple"]]
    orderList: list[BatchCancelSpotOrderItemParams]


class CancelSymbolOrderParams(TypedDict):
    """Params to cancel all orders by symbol."""

    symbol: str


class SpotOrdersQueryParams(TypedDict, total=False):
    """Params for querying spot orders."""

    symbol: NotRequired[str]
    startTime: NotRequired[str]
    endTime: NotRequired[str]
    idLessThan: NotRequired[str]
    limit: NotRequired[str]
    orderId: NotRequired[str]
    tpslType: NotRequired[str]
    requestTime: NotRequired[str]
    receiveWindow: NotRequired[str]
