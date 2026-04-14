"""Futures instruments converters for unified format."""

from decimal import Decimal
from typing import Any

from aiotrade.unified.types import UnifiedInstrumentInfo
from aiotrade.utils.formatters import float_to_str
from aiotrade.utils.numbers import parse_decimal


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
                return f  # type: ignore[no-any-return]
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


def unified_instrument_info_from_kucoin(
    instrument: dict[str, Any],
) -> "UnifiedInstrumentInfo":
    """Create UnifiedInstrumentInfo from a KuCoin swap instrument."""
    tick_sz = float_to_str(instrument["tickSize"], use_exp=False)
    lot_sz = float_to_str(instrument["lotSize"], use_exp=False)
    # Determine decimal_places for qty_step (lotSz)
    decimal_places = 0
    if "." in lot_sz:
        decimal_places = len(lot_sz.rstrip("0").split(".")[1])
    price_precision = 0
    # price_precision (decimal places of tickSz)
    if "." in tick_sz:
        price_precision = len(tick_sz.rstrip("0").split(".")[1])
    qty_step = float(lot_sz)
    return UnifiedInstrumentInfo(
        symbol=instrument["symbol"],
        decimal_places=decimal_places,
        price_precision=price_precision,
        tick_size=float(tick_sz),
        qty_step=parse_decimal(qty_step),
        min_order_qty=parse_decimal(lot_sz),
        max_order_qty=parse_decimal(instrument["maxOrderQty"]),
        max_mkt_qty=parse_decimal(instrument["marketMaxOrderQty"]),
        min_notional=Decimal("0"),
        max_notional=Decimal("inf"),
        max_mkt_notional=Decimal("inf"),
        max_absolute_margin=Decimal("inf"),
        min_leverage=1,
        max_leverage=float(instrument["maxLeverage"]),
        additional={
            "ct_mult": parse_decimal(
                float_to_str(instrument["multiplier"], use_exp=False)
            ),
            "ct_val": parse_decimal(lot_sz),
        },
        source="kucoin",
    )
