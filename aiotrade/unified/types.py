"""Unified types and normalized trading conversion helpers."""

import logging
from decimal import Decimal
from enum import StrEnum
from typing import Any, Literal, NotRequired, TypedDict, cast

from aiotrade import ExchangeLiteral
from aiotrade.types.binance import MarginType as BinanceMarginMode
from aiotrade.types.bingx import MarginMode as BingxMarginMode
from aiotrade.types.bitget import MarginMode as BitgetMarginMode
from aiotrade.types.bybit import MarginMode as BybitMarginMode
from aiotrade.types.gate import MarginMode as GateMarginMode
from aiotrade.types.kucoin import MarginMode as KuCoinMarginMode
from aiotrade.types.okx import TradeMode as OkxMarginMode

logger = logging.getLogger("aiotrade.unified")

type UnifiedAssetMode = Literal["single", "union"]


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
            "okx": {
                UnifiedMarginMode.CROSS: "cross",
                UnifiedMarginMode.ISOLATED: "isolated",
            },
            "gate": {
                UnifiedMarginMode.CROSS: "CROSS",
                UnifiedMarginMode.ISOLATED: "ISOLATED",
            },
        }

    def to_exchange(self, exchange: ExchangeLiteral) -> str:
        """Return exchange-specific string value for this margin mode."""
        try:
            return self._exchange_map[exchange][self]
        except KeyError as err:
            raise ValueError(
                f"Unsupported margin mode or exchange: {self} for {exchange}"
            ) from err

    def to_bybit(self) -> BybitMarginMode:
        """Return Bybit-specific margin mode string."""
        return cast(BybitMarginMode, self.to_exchange("bybit"))

    def to_bingx(self) -> BingxMarginMode:
        """Return BingX-specific margin mode string."""
        return cast(BingxMarginMode, self.to_exchange("bingx"))

    def to_bitget(self) -> BitgetMarginMode:
        """Return Bitget-specific margin mode string."""
        return cast(BitgetMarginMode, self.to_exchange("bitget"))

    def to_binance(self) -> BinanceMarginMode:
        """Return Binance-specific margin mode string."""
        return cast(BinanceMarginMode, self.to_exchange("binance"))

    def to_kucoin(self) -> KuCoinMarginMode:
        """Return KuCoin-specific margin mode string."""
        return cast(KuCoinMarginMode, self.to_exchange("kucoin"))

    def to_okx(self) -> OkxMarginMode:
        """Return OKX-specific margin mode string."""
        return cast(OkxMarginMode, self.to_exchange("okx"))

    def to_gate(self) -> GateMarginMode:
        """Return Gate-specific margin mode string."""
        return cast(GateMarginMode, self.to_exchange("gate"))


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
    source: ExchangeLiteral
    additional: NotRequired[dict[str, Any]]


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
    source: ExchangeLiteral


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
    source: ExchangeLiteral


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
    source: ExchangeLiteral


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
    leverage: float
    order_link_id: NotRequired[str]
    order_type: Literal["Market", "Limit"]
    take_profit: NotRequired[float]
    stop_loss: NotRequired[float]
    reduce_only: NotRequired[bool]


class UnifiedPlaceSpotOrderRequest(TypedDict):
    """Unified model for placing a spot order."""

    symbol: str
    side: UnifiedSide
    price: NotRequired[float]
    qty: float
    order_link_id: NotRequired[str]
    order_type: Literal["Market", "TakeProfit"]
