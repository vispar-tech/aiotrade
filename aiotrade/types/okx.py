"""Type definitions for OKX client."""

from typing import Literal, NotRequired, TypedDict

type TradeMode = Literal["cross", "isolated", "cash", "spot_isolated"]
type OrderSide = Literal["buy", "sell"]
type PositionSide = Literal["long", "short", "net"]
type OrderType = Literal[
    "market",
    "limit",
    "post_only",
    "fok",
    "ioc",
    "optimal_limit_ioc",
    "mmp",
    "mmp_and_post_only",
    "elp",
]
type TargetCurrency = Literal["base_ccy", "quote_ccy"]
type PriceAmendmentType = Literal["0", "1"]
type SelfTradePreventionMode = Literal["cancel_maker", "cancel_taker", "cancel_both"]
type TakeProfitStopLossTriggerPriceType = Literal["last", "index", "mark"]
type TakeProfitOrderKind = Literal["condition", "limit"]
type AmendPriceOnTriggerType = Literal["0", "1"]
type AlgoOrderType = Literal[
    "conditional",
    "oco",
    "chase",
    "trigger",
    "move_order_stop",
    "iceberg",
    "twap",
]
type AlgoOrderHistoryState = Literal["effective", "canceled", "order_failed"]


class AttachAlgorithmOrderParams(TypedDict, total=False):
    """Attach TP/SL info to order."""

    # Client Algo ID (max 32 characters)
    attachAlgoClOrdId: NotRequired[str]
    # Take-profit trigger price (float, will be converted to str in request)
    tpTriggerPx: NotRequired[float]
    # Take-profit trigger ratio, e.g. 0.3 for 30%
    tpTriggerRatio: NotRequired[float]
    # Take-profit order price, -1 for market
    tpOrdPx: NotRequired[float]
    # Take-profit order kind: condition or limit
    tpOrdKind: NotRequired[TakeProfitOrderKind]
    # Stop-loss trigger price
    slTriggerPx: NotRequired[float]
    # Stop-loss trigger ratio
    slTriggerRatio: NotRequired[float]
    # Stop-loss order price, -1 for market
    slOrdPx: NotRequired[float]
    # TP trigger price type: last, index, mark
    tpTriggerPxType: NotRequired[TakeProfitStopLossTriggerPriceType]
    # SL trigger price type: last, index, mark
    slTriggerPxType: NotRequired[TakeProfitStopLossTriggerPriceType]
    # TP order size (float; for split TP)
    sz: NotRequired[float]
    # Use cost-price for SL in split TPs; "0" = disable, "1" = enable
    amendPxOnTriggerType: NotRequired[AmendPriceOnTriggerType]


class PlaceOrderParams(TypedDict, total=False):
    """Single order parameters for placing to OKX."""

    # Instrument ID, e.g. "BTC-USDT"
    instId: str
    # Trade mode: cross/isolated/cash/spot_isolated
    tdMode: TradeMode
    # Margin currency
    ccy: NotRequired[str]
    # Client Order ID (up to 32 chars)
    clOrdId: NotRequired[str]
    # Order tag (up to 16 chars)
    tag: NotRequired[str]
    # Order side (buy/sell)
    side: OrderSide
    # Position side: long, short, net
    posSide: NotRequired[PositionSide]
    # Order type (market, limit, etc)
    ordType: OrderType
    # Quantity (float, will be converted to str in request)
    sz: float
    # Order price (float, will be converted to str in request)
    px: NotRequired[float]
    # USD order price (float, for options)
    pxUsd: NotRequired[float]
    # Implied volatility price (float, for options)
    pxVol: NotRequired[float]
    # Reduce position only
    reduceOnly: NotRequired[bool]
    # Quantity unit ("base_ccy", "quote_ccy")
    tgtCcy: NotRequired[TargetCurrency]
    # Disallow auto order size amend in spot
    banAmend: NotRequired[bool]
    # Price amendment type ("0", "1")
    pxAmendType: NotRequired[PriceAmendmentType]
    # Quote currency for trading
    tradeQuoteCcy: NotRequired[str]
    # Self-trade prevention mode
    stpMode: NotRequired[SelfTradePreventionMode]
    # ELP taker access (IOC only)
    isElpTakerAccess: NotRequired[bool]
    # Attached TP/SL info (list of AttachAlgorithmOrderParams)
    attachAlgoOrds: NotRequired[list[AttachAlgorithmOrderParams]]


class CancelOrderParams(TypedDict, total=False):
    """Params for canceling a single order.

    instId required; ordId or clOrdId required.
    """

    instId: str
    ordId: str
    clOrdId: str


class AttachAlgorithmOrderNested(TypedDict, total=False):
    """Attach nested TP/SL order (used in attachAlgoOrds)."""

    # Client-supplied Algo ID (max 32 chars)
    attachAlgoClOrdId: NotRequired[str]
    # Take-profit trigger price (float->str)
    tpTriggerPx: NotRequired[float]
    # Take-profit trigger ratio (float->str)
    tpTriggerRatio: NotRequired[float]
    # Take-profit trigger px type: last/index/mark
    tpTriggerPxType: NotRequired[str]
    # Take-profit order price (float->str)
    tpOrdPx: NotRequired[float]
    # Stop-loss trigger price (float->str)
    slTriggerPx: NotRequired[float]
    # Stop-loss trigger ratio (float->str)
    slTriggerRatio: NotRequired[float]
    # Stop-loss trigger px type: last/index/mark
    slTriggerPxType: NotRequired[str]
    # Stop-loss order price (float->str)
    slOrdPx: NotRequired[float]


class BaseAlgorithmOrderParams(TypedDict):
    """Base fields for all algo orders."""

    # Instrument ID
    instId: str
    # Trade mode: cross/isolated/cash/spot_isolated
    tdMode: str
    # Order side: buy/sell
    side: str
    # Algo order type
    ordType: str


class ConditionalAlgorithmOrderParams(BaseAlgorithmOrderParams, total=False):
    """Algo order: take-profit/stop-loss (conditional or oco)."""

    # Margin currency
    ccy: NotRequired[str]
    # Position side: long or short
    posSide: NotRequired[str]
    # Order quantity (float->str)
    sz: NotRequired[float]
    # Fraction to close; only '1' supported (float->str)
    closeFraction: NotRequired[float]
    # Order tag (max 16 chars)
    tag: NotRequired[str]
    # Quantity unit: base_ccy or quote_ccy (spot only)
    tgtCcy: NotRequired[str]
    # Custom client order ID (max 32 chars)
    algoClOrdId: NotRequired[str]
    # Quote currency (spot only)
    tradeQuoteCcy: NotRequired[str]
    # Take-profit trigger price (float->str)
    tpTriggerPx: NotRequired[float]
    # Take-profit trigger px type: last, index, mark
    tpTriggerPxType: NotRequired[str]
    # Take-profit order price (float->str)
    tpOrdPx: NotRequired[float]
    # TP order kind: condition/limit
    tpOrdKind: NotRequired[str]
    # Stop-loss trigger price (float->str)
    slTriggerPx: NotRequired[float]
    # Stop-loss trigger px type: last, index, mark
    slTriggerPxType: NotRequired[str]
    # Stop-loss order price (float->str)
    slOrdPx: NotRequired[float]
    # Cancel on position close
    cxlOnClosePos: NotRequired[bool]
    # Only reduce the position
    reduceOnly: NotRequired[bool]
    # Attached nested TP/SL orders
    attachAlgoOrds: NotRequired[list[AttachAlgorithmOrderNested]]


class ChaseAlgorithmOrderParams(BaseAlgorithmOrderParams, total=False):
    """Algo order: chase order."""

    # Margin currency
    ccy: NotRequired[str]
    # Position side: long/short
    posSide: NotRequired[str]
    # Order quantity (float->str)
    sz: NotRequired[float]
    # Fraction to close (float->str)
    closeFraction: NotRequired[float]
    # Order tag (max 16 chars)
    tag: NotRequired[str]
    # Quantity unit: base_ccy/quote_ccy (spot)
    tgtCcy: NotRequired[str]
    # Client Algo ID (max 32 chars)
    algoClOrdId: NotRequired[str]
    # Quote currency (spot only)
    tradeQuoteCcy: NotRequired[str]
    # Chase type: distance or ratio
    chaseType: NotRequired[str]
    # Chase value (float->str); abs value or ratio, e.g. 0.1=10%
    chaseVal: NotRequired[float]
    # Max chase type: distance or ratio (together with maxChaseVal)
    maxChaseType: NotRequired[str]
    # Max chase value (float->str)
    maxChaseVal: NotRequired[float]
    # Only reduce the position
    reduceOnly: NotRequired[bool]


class TriggerAlgorithmOrderParams(BaseAlgorithmOrderParams, total=False):
    """Algo order: trigger."""

    # Margin currency
    ccy: NotRequired[str]
    # Position side: long/short
    posSide: NotRequired[str]
    # Quantity (float->str)
    sz: NotRequired[float]
    # Fraction to close (float->str)
    closeFraction: NotRequired[float]
    # Order tag (max 16 chars)
    tag: NotRequired[str]
    # Quantity unit: base_ccy/quote_ccy (spot)
    tgtCcy: NotRequired[str]
    # Client Algo ID (max 32 chars)
    algoClOrdId: NotRequired[str]
    # Quote currency (spot only)
    tradeQuoteCcy: NotRequired[str]
    # Trigger price (REQUIRED, float->str)
    triggerPx: float
    # Triggered order price, -1 for market (REQUIRED, float->str)
    orderPx: float
    # Trigger order advanced type: fok/ioc
    advanceOrdType: NotRequired[str]
    # Trigger px type: last/index/mark
    triggerPxType: NotRequired[str]


class TrailingStopAlgorithmOrderParams(BaseAlgorithmOrderParams, total=False):
    """Algo order: trailing stop."""

    # Margin currency
    ccy: NotRequired[str]
    # Position side: long/short
    posSide: NotRequired[str]
    # Quantity (float->str)
    sz: NotRequired[float]
    # Fraction to close (float->str)
    closeFraction: NotRequired[float]
    # Order tag (max 16 chars)
    tag: NotRequired[str]
    # Quantity unit: base_ccy/quote_ccy (spot)
    tgtCcy: NotRequired[str]
    # Client Algo ID (max 32 chars)
    algoClOrdId: NotRequired[str]
    # Quote currency (spot only)
    tradeQuoteCcy: NotRequired[str]
    # Callback ratio, e.g. 0.01=1%
    callbackRatio: NotRequired[float]
    # Callback spread (float->str)
    callbackSpread: NotRequired[float]
    # Activation price (float->str)
    activePx: NotRequired[float]
    # Only reduce the position
    reduceOnly: NotRequired[bool]


class TwapAlgorithmOrderParams(BaseAlgorithmOrderParams, total=False):
    """Algo order: TWAP time-weighted average price."""

    # Margin currency
    ccy: NotRequired[str]
    # Position side: long/short
    posSide: NotRequired[str]
    # Quantity (float->str)
    sz: NotRequired[float]
    # Fraction to close (float->str)
    closeFraction: NotRequired[float]
    # Order tag (max 16 chars)
    tag: NotRequired[str]
    # Quantity unit: base_ccy/quote_ccy (spot)
    tgtCcy: NotRequired[str]
    # Client Algo ID (max 32 chars)
    algoClOrdId: NotRequired[str]
    # Quote currency (spot only)
    tradeQuoteCcy: NotRequired[str]
    # Price variance by percent (float->str, [0.0001 ~ 0.01])
    pxVar: NotRequired[float]
    # Price variance as constant (float->str, >=0)
    pxSpread: NotRequired[float]
    # Average size (float->str), required
    szLimit: float
    # Price limit (float->str, >=0), required
    pxLimit: float
    # Interval in seconds (float->str), required
    timeInterval: float


AlgorithmOrderParams = (
    ConditionalAlgorithmOrderParams
    | ChaseAlgorithmOrderParams
    | TriggerAlgorithmOrderParams
    | TrailingStopAlgorithmOrderParams
    | TwapAlgorithmOrderParams
)


class CancelAlgorithmOrderParams(TypedDict, total=False):
    """Params for canceling an algo order."""

    instId: str
    algoId: str
    algoClOrdId: str
