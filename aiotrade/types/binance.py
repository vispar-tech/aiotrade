"""Type definitions for binance client."""

from typing import Literal, NotRequired, TypedDict

type SymbolPermissions = Literal["SPOT", "MARGIN", "LEVERAGED"]
type AlgorithmOrderType = Literal[
    "STOP_MARKET",
    "TAKE_PROFIT_MARKET",
    "STOP",
    "TAKE_PROFIT",
    "TRAILING_STOP_MARKET",
]
type MarginType = Literal["ISOLATED", "CROSSED"]
type OrderSide = Literal["BUY", "SELL"]
type AlgorithmAlgoType = Literal["CONDITIONAL"]
type PositionSide = Literal["BOTH", "LONG", "SHORT"]
type TimeInForce = Literal["IOC", "GTC", "FOK", "GTX", "GTD"]
type AlgorithmWorkingType = Literal["MARK_PRICE", "CONTRACT_PRICE"]
type PriceMatch = Literal[
    "OPPONENT",
    "OPPONENT_5",
    "OPPONENT_10",
    "OPPONENT_20",
    "QUEUE",
    "QUEUE_5",
    "QUEUE_10",
    "QUEUE_20",
]
type NewOrderRespType = Literal["ACK", "RESULT"]
type AlgorithmSTPMode = Literal["EXPIRE_TAKER", "EXPIRE_MAKER", "EXPIRE_BOTH", "NONE"]
type BoolStr = Literal["true", "false"]
type BoolUpperStr = Literal["TRUE", "FALSE"]

type OrderType = Literal[
    "LIMIT",
    "MARKET",
    "STOP",
    "TAKE_PROFIT",
    "STOP_MARKET",
    "TAKE_PROFIT_MARKET",
    "LIMIT_MAKER",
]

type SelfTradePreventionMode = Literal["EXPIRE_TAKER", "EXPIRE_MAKER", "EXPIRE_BOTH"]
# The parameters for conditional orders, grouped by underlying algo order type
type AlgorithmOrderParams = (
    "TrailingStopMarketAlgorithmOrderParams | StopTakeProfitAlgorithmOrderParams"
)

# Order types (spot)
type SpotOrderType = Literal[
    "LIMIT",
    "MARKET",
    "STOP_LOSS",
    "STOP_LOSS_LIMIT",
    "TAKE_PROFIT",
    "TAKE_PROFIT_LIMIT",
    "LIMIT_MAKER",
]


# Order response type
type SpotOrderRespType = Literal["ACK", "RESULT", "FULL"]

# Self trade prevention mode
type SpotSelfTradePreventionMode = Literal[
    "NONE", "EXPIRE_MAKER", "EXPIRE_TAKER", "EXPIRE_BOTH"
]

# Peg price type
type PegPriceType = Literal["PRIMARY_PEG", "MARKET_PEG"]

# Peg offset type
type PegOffsetType = Literal["PRICE_LEVEL"]


class CreateOrderParams(TypedDict, total=False):
    """Params to create order on binance."""

    symbol: str
    side: OrderSide
    type: OrderType
    positionSide: NotRequired[PositionSide]
    timeInForce: NotRequired[TimeInForce]
    quantity: NotRequired[float]
    reduceOnly: NotRequired[BoolStr]
    price: NotRequired[float]
    newClientOrderId: NotRequired[str]
    newOrderRespType: NotRequired[NewOrderRespType]
    priceMatch: NotRequired[PriceMatch]
    selfTradePreventionMode: NotRequired[SelfTradePreventionMode]
    goodTillDate: NotRequired[int]
    recvWindow: NotRequired[int]


class BaseAlgorithmOrderParams(TypedDict):
    """Base parameters for a  conditional (algo) order."""

    algoType: AlgorithmAlgoType
    symbol: str
    side: OrderSide
    type: AlgorithmOrderType
    positionSide: NotRequired[PositionSide]
    timeInForce: NotRequired[TimeInForce]
    workingType: NotRequired[AlgorithmWorkingType]
    priceMatch: NotRequired[PriceMatch]
    clientAlgoId: NotRequired[str]
    newOrderRespType: NotRequired[NewOrderRespType]
    selfTradePreventionMode: NotRequired[AlgorithmSTPMode]
    goodTillDate: NotRequired[int]  # ms timestamp, for timeInForce="GTD"
    recvWindow: NotRequired[int]


class TrailingStopMarketAlgorithmOrderParams(BaseAlgorithmOrderParams):
    """Parameters for a  TRAILING_STOP_MARKET conditional (algo) order."""

    activatePrice: float
    callbackRate: float
    quantity: NotRequired[float]
    reduceOnly: NotRequired[BoolStr]
    price: NotRequired[float]


class StopTakeProfitAlgorithmOrderParams(BaseAlgorithmOrderParams):
    """Parameters for a  STOP/TAKE_PROFIT(MARKET) conditional (algo) order."""

    quantity: NotRequired[float]
    price: NotRequired[float]
    triggerPrice: NotRequired[float]
    closePosition: NotRequired[BoolStr]
    priceProtect: NotRequired[BoolUpperStr]
    reduceOnly: NotRequired[BoolStr]


class SpotOrderParams(TypedDict):
    """Parameters for placing a new spot order."""

    symbol: str
    side: OrderSide
    type: SpotOrderType
    timestamp: int

    # Optional fields
    timeInForce: NotRequired[TimeInForce]
    quantity: NotRequired[float]
    quoteOrderQty: NotRequired[float]
    price: NotRequired[float]
    newClientOrderId: NotRequired[str]
    strategyId: NotRequired[int]
    strategyType: NotRequired[int]
    stopPrice: NotRequired[float]
    trailingDelta: NotRequired[int]
    icebergQty: NotRequired[float]
    newOrderRespType: NotRequired[SpotOrderRespType]
    selfTradePreventionMode: NotRequired[SpotSelfTradePreventionMode]
    pegPriceType: NotRequired[PegPriceType]
    pegOffsetValue: NotRequired[int]
    pegOffsetType: NotRequired[PegOffsetType]
    recvWindow: NotRequired[float]
