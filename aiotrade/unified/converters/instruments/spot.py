"""Spot instrument converters for unified format."""

import math
from decimal import Decimal
from typing import Any

from aiotrade.unified.types import UnifiedSpotInstrumentInfo
from aiotrade.utils import parse_decimal


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
