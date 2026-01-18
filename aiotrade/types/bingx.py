"""Type definitions for bingx client."""

from typing import Literal, NotRequired, TypedDict

AccountType = Literal[
    "spot",  # Spot (fund account)
    "stdFutures",  # Standard futures account
    "coinMPerp",  # Coin base account
    "USDTMPerp",  # U base account
    "copyTrading",  # Copy trading account
    "grid",  # Grid account
    "eran",  # Wealth account
    "c2c",  # C2C account
]
MarginMode = Literal["ISOLATED", "CROSSED", "SEPARATE_ISOLATED"]


SwapOrderType = Literal[
    "LIMIT",
    "MARKET",
    "STOP_MARKET",
    "TAKE_PROFIT_MARKET",
    "STOP",
    "TAKE_PROFIT",
    "TRIGGER_LIMIT",
    "TRIGGER_MARKET",
    "TRAILING_STOP_MARKET",
    "TRAILING_TP_SL",
]
TpSlOrderType = Literal["STOP", "TAKE_PROFIT", "STOP_MARKET", "TAKE_PROFIT_MARKET"]
OrderSide = Literal["SELL", "BUY"]
PositionSide = Literal["BOTH", "LONG", "SHORT"]
TriggerPriceType = Literal["MARK_PRICE", "CONTRACT_PRICE", "INDEX_PRICE"]
TimeInForce = Literal["PostOnly", "GTC", "IOC", "FOK"]
StopGuaranteed = Literal["true", "false", "cutfee"]


class TpSlStruct(TypedDict, total=False):
    """Structured dict for takeProfit/stopLoss fields."""

    order_type: TpSlOrderType
    stop_price: float
    price: float
    working_type: TriggerPriceType


class PlaceSwapOrderParams(TypedDict, total=False):
    """Request parameters for creating/modifying an order on BingX."""

    # There must be a hyphen "-" in the trading pair symbol. eg: BTC-USDT
    symbol: str
    # Order type
    order_type: SwapOrderType
    # buying and selling direction
    side: OrderSide
    # Position direction
    position_side: NotRequired[PositionSide]
    # Only for single position mode
    reduce_only: NotRequired[bool]  # need to str
    # Price, or trailing stop distance for certain order types
    price: NotRequired[float]
    # Order quantity in COIN
    quantity: NotRequired[float]
    # Quote order quantity, e.g. 100USDT
    quote_order_qty: NotRequired[float]
    # Trigger price for some order types
    stop_price: NotRequired[float]
    # For trailing orders; Maximum: 1
    price_rate: NotRequired[float]
    # Stop loss setting, only STOP_MARKET/STOP
    working_type: NotRequired[TriggerPriceType]
    # Take-profit order (accepts a TpSlStruct dict, or stringified JSON)
    take_profit: NotRequired[TpSlStruct]
    # Stop-loss order (accepts a TpSlStruct dict, or stringified JSON)
    stop_loss: NotRequired[TpSlStruct]
    # User-custom order ID (1-40 chars, lowercased)
    client_order_id: NotRequired[str]
    # Order execution time-in-force
    time_in_force: NotRequired[TimeInForce]
    # Close all position after trigger
    close_position: NotRequired[bool]  # need to str
    # Used with trailing stop orders
    activation_price: NotRequired[float]
    # Guaranteed SL/TP feature
    stop_guaranteed: NotRequired[StopGuaranteed]
    # Required when closing in Separate Isolated mode
    position_id: NotRequired[int]
