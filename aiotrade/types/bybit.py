"""Type definitions for bybit client."""

from typing import Literal, NotRequired, TypedDict

AccountType = Literal["UNIFIED", "FUND"]
MarginMode = Literal["ISOLATED_MARGIN", "REGULAR_MARGIN", "PORTFOLIO_MARGIN"]

# Market types
InstrumentStatus = Literal["Trading", "PreLaunch", "Delivering"]
SymbolType = Literal["innovation", "adventure", "xstocks"]

# Trade types
Side = Literal["Buy", "Sell"]
PlaceOrderType = Literal["Market", "Limit"]
MarketUnit = Literal["baseCoin", "quoteCoin"]
OrderPriceTriggerBy = Literal["LastPrice", "IndexPrice", "MarkPrice"]
TimeInForce = Literal["GTC", "IOC", "FOK"]
PositionIdx = Literal[0, 1, 2]
TpSlTriggerBy = Literal["LastPrice", "IndexPrice", "MarkPrice"]
TpSlMode = Literal["Full", "Partial"]
TpSlOrderType = Literal["Market", "Limit"]


class SetTradingStopParams(TypedDict):
    """Parameters for setting trading stop (TP/SL)."""

    # Required fields
    symbol: str
    tpsl_mode: TpSlMode  # Full or Partial
    position_idx: PositionIdx  # 0, 1, 2

    # Optional TP/SL fields
    take_profit: NotRequired[float]  # need to str
    stop_loss: NotRequired[float]  # need to str
    trailing_stop: NotRequired[float]  # need to str
    tp_trigger_by: NotRequired[TpSlTriggerBy]
    sl_trigger_by: NotRequired[TpSlTriggerBy]
    active_price: NotRequired[float]  # need to str

    # Partial mode fields
    tp_size: NotRequired[float]  # need to str
    sl_size: NotRequired[float]  # need to str
    tp_limit_price: NotRequired[float]  # need to str
    sl_limit_price: NotRequired[float]  # need to str
    tp_order_type: NotRequired[TpSlOrderType]
    sl_order_type: NotRequired[TpSlOrderType]


class GetOrderHistoryParams(TypedDict, total=False):
    """Parameters for querying order history."""

    symbol: str
    base_coin: str
    settle_coin: str
    order_id: str
    order_link_id: str
    order_filter: Literal[
        "Order", "StopOrder", "tpslOrder", "OcoOrder", "BidirectionalTpslOrder"
    ]
    order_status: Literal[
        # Open status
        "New",
        "PartiallyFilled",
        "Untriggered",
        # Closed status
        "Rejected",
        "PartiallyFilledCanceled",
        "Filled",
        "Cancelled",
        "Triggered",
        "Deactivated",
    ]
    start_time: int
    end_time: int
    limit: int
    cursor: str


class CancelOrderParams(TypedDict):
    """Parameters for canceling an order."""

    symbol: str  # required
    order_id: NotRequired[str]
    order_link_id: NotRequired[str]


class PlaceOrderParams(TypedDict):
    """Parameters for placing an order."""

    # Symbol name, like BTCUSDT, uppercase only. (required)
    symbol: str

    # Whether to borrow.
    # 0(default): false, spot trading
    # 1: true, margin trading, make sure you turn on margin trading,
    # and set the relevant currency as collateral
    is_leverage: NotRequired[int]

    side: Side
    order_type: PlaceOrderType

    # Order quantity .
    # For Spot: Market Buy order defaults to "by value".
    # You can set `market_unit` to choose ordering by value
    # or by quantity for market orders.
    # For Perps, Futures & Options: Always order by quantity.
    # For Perps & Futures: If qty="0" and you set `reduce_only=True`
    # and `close_on_trigger=True`, you can close the position
    # up to maxMktOrderQty or maxOrderQty
    # (see "Get Instruments Info" for the relevant symbol).
    qty: float  # need to str

    # Select the unit for qty when creating Spot market orders. Optional.
    # "baseCoin": For example, buy BTCUSDT, then "qty" unit is BTC.
    # "quoteCoin": For example, sell BTCUSDT, then "qty" unit is USDT.
    market_unit: NotRequired[MarketUnit]

    # Order price.
    # Market orders will ignore this field.
    # Please check the min price and price precision from the instrument info endpoint.
    # If you have a position, price must be better than the liquidation price.
    price: NotRequired[float]  # need to str

    # The conditional order trigger price.
    # For Perps & Futures: Set trigger_price > market price
    # if you expect the price to rise to trigger your order.
    # Otherwise, set trigger_price < market price.
    # For Spot: Used for TP/SL and Conditional order trigger price.
    trigger_price: NotRequired[float]  # need to str

    # Trigger price type, Conditional order param for Perps & Futures.
    # Valid for linear & inverse.
    trigger_by: NotRequired[OrderPriceTriggerBy]

    # Time in force for the order.
    # Market orders will always use IOC.
    # If not passed, GTC is used by default.
    time_in_force: NotRequired[TimeInForce]

    # Position index. Used to identify positions in different position modes.
    # Under hedge-mode, this param is required.
    # 0: one-way mode
    # 1: hedge-mode Buy side
    # 2: hedge-mode Sell side
    position_idx: NotRequired[PositionIdx]

    # User customised order ID.
    # A max of 36 characters. Combinations of numbers, letters
    # (upper and lower cases), dashes, and underscores are supported.
    #
    # Futures & Perps: order_link_id is optional and must always be unique if provided.
    # Options: order_link_id is required and must always be unique.
    order_link_id: NotRequired[str]

    # Take profit price.
    # Spot Limit order supports take profit, stop loss or limit take profit,
    # limit stop loss when creating an order.
    take_profit: NotRequired[float]  # need to str

    # Stop loss price.
    # Spot Limit order supports take profit, stop loss or limit take profit,
    # limit stop loss when creating an order.
    stop_loss: NotRequired[float]  # need to str

    # The price type to trigger take profit. MarkPrice, IndexPrice, default: LastPrice.
    # Valid for linear & inverse.
    tp_trigger_by: NotRequired[TpSlTriggerBy]

    # The price type to trigger stop loss. MarkPrice, IndexPrice, default: LastPrice.
    # Valid for linear & inverse.
    sl_trigger_by: NotRequired[TpSlTriggerBy]

    # reduce_only specifies if the order is reduce-only.
    # true means your position can only reduce in size if this order is triggered.
    # You must specify it as true when you are about to close/reduce the position.
    # When reduce_only is true, take profit/stop loss cannot be set.
    # Valid for linear, inverse & option.
    reduce_only: NotRequired[bool]

    # TP/SL mode.
    # Full: entire position for TP/SL. Then, tp_order_type or sl_order_type
    # must be Market.
    # Partial: partial position TP/SL
    # (creates TP/SL orders with the qty you actually fill).
    #   Limit TP/SL orders are only supported in Partial mode.
    #   When creating limit TP/SL, tpsl_mode is required and must be Partial.
    # Valid for linear & inverse.
    tpsl_mode: NotRequired[TpSlMode]

    # The limit order price when take profit price is triggered.
    # linear & inverse: only works when tpsl_mode=Partial and tp_order_type=Limit.
    # Spot: required when the order has take_profit and tp_order_type=Limit.
    tp_limit_price: NotRequired[str]

    # The limit order price when stop loss price is triggered.
    # linear & inverse: only works when tpsl_mode=Partial and sl_order_type=Limit.
    # Spot: required when the order has stop_loss and sl_order_type=Limit.
    sl_limit_price: NotRequired[str]

    # The order type when take profit is triggered.
    # linear & inverse: Market (default), Limit.
    #   For tpsl_mode=Full, only supports tp_order_type=Market.
    # Spot: Market when you set take_profit,
    # Limit when you set both take_profit and tp_limit_price.
    tp_order_type: NotRequired[TpSlOrderType]

    # The order type when stop loss is triggered.
    # linear & inverse: Market (default), Limit.
    #   For tpsl_mode=Full, only supports sl_order_type=Market.
    # Spot: Market when you set stop_loss,
    # Limit when you set both stop_loss and sl_limit_price.
    sl_order_type: NotRequired[TpSlOrderType]
