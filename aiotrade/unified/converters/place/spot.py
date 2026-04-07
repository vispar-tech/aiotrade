"""Converters for unified spot order requests to exchange-specific formats."""

from aiotrade.types.bingx import PlaceSpotOrderParams as BingxSpotOrderParams
from aiotrade.types.bybit import PlaceOrderParams as BybitOrderParams
from aiotrade.unified.types import (
    UnifiedPlaceSpotOrderRequest,
    UnifiedSide,
)


def convert_unified_place_spot_order_to_bingx(
    order: UnifiedPlaceSpotOrderRequest,
) -> BingxSpotOrderParams:
    """Convert unified place spot order request to bingx format."""
    params = BingxSpotOrderParams(
        symbol=order["symbol"],
        side="BUY" if order["side"] == UnifiedSide.LONG else "SELL",
        order_type="MARKET" if order["order_type"] == "Market" else "TAKE_STOP_MARKET",
        quantity=order["qty"],
    )

    if (order_link_id := order.get("order_link_id")) is not None:
        params["new_client_order_id"] = order_link_id
    if (price := order.get("price")) is not None:
        if order["order_type"] == "Market":
            params["price"] = price
        else:
            params["stop_price"] = price
    return params


def convert_unified_place_spot_order_to_bybit(
    order: UnifiedPlaceSpotOrderRequest,
) -> BybitOrderParams:
    """Convert unified place spot order request to bybit format."""
    params = BybitOrderParams(
        symbol=order["symbol"],
        side="Buy" if order["side"] == UnifiedSide.LONG else "Sell",
        order_type="Market",
        qty=order["qty"],
        market_unit="baseCoin",
        is_leverage=0,
    )

    if order["order_type"] == "TakeProfit":
        params["tp_order_type"] = "Market"
        if (price := order.get("price")) is not None:
            params["trigger_price"] = price
        params["order_filter"] = "tpslOrder"

    if (price := order.get("price")) is not None:
        params["price"] = price
    if (order_link_id := order.get("order_link_id")) is not None:
        params["order_link_id"] = order_link_id

    return params
