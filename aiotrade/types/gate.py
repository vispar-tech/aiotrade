"""Types for Gate futures position mode switching."""

from typing import Literal, NotRequired, TypedDict

type Settle = Literal["usdt", "btc"]
type MarginMode = Literal["ISOLATED", "CROSS"]
type PositionMarginMode = Literal["isolated", "cross"]
type UnifiedMode = Literal["classic", "multi_currency", "portfolio", "single_currency"]


class UnifiedModeSettings(TypedDict, total=False):
    """Optional settings for unified account mode switch."""

    usdt_futures: bool
    spot_hedge: bool
    use_funding: bool
    options: bool


class UnifiedModeSet(TypedDict):
    """Request body for switching Gate unified account mode."""

    mode: UnifiedMode
    settings: NotRequired[UnifiedModeSettings]


class FuturesPlaceOrder(TypedDict):
    """Futures order details."""

    # required
    contract: str
    # required, trading quantity
    size: float
    # required
    price: float
    # write-only
    close: NotRequired[bool]
    # write-only
    reduce_only: NotRequired[bool]
    tif: NotRequired[Literal["gtc", "ioc", "poc", "fok"]]
    text: NotRequired[str]
    # read-only, referrer user ID
    refu: NotRequired[int]
    # write-only
    auto_size: NotRequired[Literal["close_long", "close_short"]]
    stp_act: NotRequired[Literal["co", "cn", "cb", "-"]]
    # write-only, position ID
    pid: NotRequired[int]
    market_order_slip_ratio: NotRequired[str]
    # e.g., "isolated", "cross"
    pos_margin_mode: NotRequired[PositionMarginMode]


class FuturesPriceTriggeredOrderInitial(TypedDict, total=False):
    """Initial/order fields for Futures price-triggered order (Gate)."""

    contract: str  # required
    size: NotRequired[int]  # optional, number of contracts to close (0=full close)
    amount: NotRequired[str]  # optional, takes precedence over size if set
    price: str  # required, order price as string ("0" for market)
    close: NotRequired[
        bool
    ]  # optional; must be true for full close in single-position mode
    tif: NotRequired[Literal["gtc", "ioc"]]  # optional, time in force
    text: NotRequired[str]  # optional, order source ("web", "api", "app")
    reduce_only: NotRequired[bool]  # optional, only closes/reduces pos
    auto_size: NotRequired[
        Literal["close_long", "close_short", "close"]
    ]  # optional, see docs


class FuturesPriceTriggeredOrderTrigger(TypedDict, total=False):
    """Trigger fields for Futures price-triggered order (Gate)."""

    strategy_type: NotRequired[int]  # 0 (price trigger), 1 (spread trigger)
    price_type: NotRequired[int]  # 0=Last, 1=Mark, 2=Index
    price: str  # required, price value or spread as string
    rule: int  # required, 1: >=, 2: <=
    expiration: NotRequired[int]  # optional, trigger timeout seconds


class FuturesPriceTriggeredOrder(TypedDict, total=False):
    """
    Payload model for placing a Gate Futures price-triggered order.

    Example:
    {
        "initial": {
            "contract": "BTC_USDT",
            "size": 100,
            "price": "5.03"
        },
        "trigger": {
            "strategy_type": 0,
            "price_type": 0,
            "price": "3000",
            "rule": 1,
            "expiration": 86400
        },
        "order_type": "close-long-order"
    }
    """

    initial: FuturesPriceTriggeredOrderInitial  # required
    trigger: FuturesPriceTriggeredOrderTrigger  # required
    order_type: NotRequired[
        Literal[
            "close-long-order",
            "close-short-order",
            "close-long-position",
            "close-short-position",
            "plan-close-long-position",
            "plan-close-short-position",
        ]
    ]  # optional, see docs


class FuturesPlaceTrailingOrder(TypedDict, total=False):
    """Model for Gate Futures trailing order (price-tracked order) request."""

    # Contract name (required)
    contract: str
    # Trading quantity in contracts, positive for buy, negative for sell (required)
    amount: float
    # Activation price (0 means trigger immediately)
    activation_price: NotRequired[str]
    # True: activate when market price >= activation price;
    # False: <= activation price
    is_gte: NotRequired[bool]
    # 1: latest price, 2: index price, 3: mark price
    price_type: NotRequired[Literal[1, 2, 3]]
    # Callback ratio or price distance (e.g., "0.1" or "0.1%")
    price_offset: NotRequired[str]
    # Whether reduce only
    reduce_only: NotRequired[bool]
    # Whether bound to a position (if True, reduce_only must also be True)
    position_related: NotRequired[bool]
    # Order custom information. Used to identify order source or set a user-defined ID
    text: NotRequired[str]
    # Position margin mode
    pos_margin_mode: NotRequired[PositionMarginMode]
    # Position mode
    position_mode: NotRequired[Literal["single", "dual", "dual_plus"]]
