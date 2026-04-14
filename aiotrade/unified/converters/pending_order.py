"""Converters for pending order data structures."""

from typing import Any

from aiotrade.unified.types import (
    UnifiedOrderStatus,
    UnifiedOrderType,
    UnifiedPendingOrder,
    UnifiedSide,
)
from aiotrade.utils.numbers import parse_float


def unified_pending_order_from_bingx(order: dict[str, Any]) -> "UnifiedPendingOrder":
    """Create UnifiedPendingOrder from a BingX order dict."""
    return UnifiedPendingOrder(
        createdTime=int(order["time"]),
        updatedTime=int(order["updateTime"]),
        orderStatus=UnifiedOrderStatus.from_exchange(order["status"]),
        orderType=UnifiedOrderType.from_exchange(order["type"]),
        orderId=order["orderId"],
        orderLinkId=str(order["clientOrderId"]),
        symbol=str(order["symbol"]),
        side=UnifiedSide.from_exchange(order["side"]),
        avgPrice=parse_float(order["avgPrice"]),
        qty=float(order["executedQty"]),
        source="bingx",
    )


def unified_pending_order_from_bybit(order: dict[str, Any]) -> "UnifiedPendingOrder":
    """Create UnifiedPendingOrder from a Bybit order dict."""
    return UnifiedPendingOrder(
        createdTime=int(order["createdTime"]),
        updatedTime=int(order["updatedTime"]),
        orderStatus=UnifiedOrderStatus.from_exchange(order["orderStatus"]),
        orderType=UnifiedOrderType.from_exchange(order["orderType"]),
        orderId=order["orderId"],
        orderLinkId=str(order["orderLinkId"]),
        symbol=str(order["symbol"]),
        side=UnifiedSide.from_exchange(order["side"]),
        avgPrice=parse_float(order["avgPrice"]),
        qty=float(order["cumExecQty"]),
        source="bybit",
    )


def unified_pending_order_from_bitget(order: dict[str, Any]) -> "UnifiedPendingOrder":
    """Create UnifiedPendingOrder from a Bitget order dict."""
    return UnifiedPendingOrder(
        createdTime=int(order["cTime"]),
        updatedTime=int(order["uTime"]),
        orderStatus=UnifiedOrderStatus.from_exchange(order["status"]),
        orderType=UnifiedOrderType.from_exchange(order["orderType"]),
        orderId=order["orderId"],
        orderLinkId=str(order.get("clientOid", "")),
        symbol=str(order["symbol"]),
        side=UnifiedSide.from_exchange(order["side"]),
        avgPrice=parse_float(order.get("priceAvg") or order.get("price") or None),
        qty=float(order["size"]),
        source="bitget",
    )


def unified_pending_order_from_okx(order: dict[str, Any]) -> "UnifiedPendingOrder":
    """Create UnifiedPendingOrder from an OKX order dict."""
    return UnifiedPendingOrder(
        createdTime=int(order["cTime"]),
        updatedTime=int(order["uTime"]),
        orderStatus=UnifiedOrderStatus.from_exchange(order["state"]),
        orderType=UnifiedOrderType.from_exchange(order["ordType"]),
        orderId=order["ordId"],
        orderLinkId=str(order.get("clOrdId", "")),
        symbol=str(order["instId"]),
        side=UnifiedSide.from_exchange(order["side"]),
        avgPrice=parse_float(order.get("avgPx") or order.get("px") or None),
        qty=float(order["sz"]),
        source="okx",
    )


def unified_pending_order_from_binance(order: dict[str, Any]) -> "UnifiedPendingOrder":
    """Create UnifiedPendingOrder from a Binance order dict, checking required keys."""

    def get_first_existing(
        order: dict[str, Any],
        keys: list[str],
        required: bool = True,
        err_msg: str | None = None,
    ) -> Any:
        for k in keys:
            if k in order:
                return order[k]
        if required:
            raise ValueError(
                err_msg or f"None of required keys {keys} found in order: {order}"
            )
        return None

    created_time = get_first_existing(
        order,
        ["time", "createTime"],
        err_msg="Neither 'time' nor 'createTime' found in Binance order.",
    )
    updated_time = get_first_existing(
        order, ["updateTime"], err_msg="'updateTime' not found in Binance order."
    )
    order_status = get_first_existing(
        order,
        ["status", "algoStatus"],
        err_msg="Neither 'status' nor 'algoStatus' found in Binance order.",
    )
    order_type = get_first_existing(
        order,
        ["type", "algoType"],
        err_msg="Neither 'type' nor 'algoType' found in Binance order.",
    )
    order_id = get_first_existing(
        order,
        ["orderId", "algoId"],
        err_msg="Neither 'orderId' nor 'algoId' found in Binance order.",
    )
    order_link_id = get_first_existing(
        order,
        ["clientOrderId", "clientAlgoId"],
        err_msg="Neither 'clientOrderId' nor 'clientAlgoId' found in Binance order.",
    )
    symbol = get_first_existing(
        order, ["symbol"], err_msg="'symbol' not found in Binance order."
    )
    side = get_first_existing(
        order, ["side"], err_msg="'side' not found in Binance order."
    )

    # avgPrice logic: try price, then avgPrice, then activatePrice, then triggerPrice
    avg_price = None
    if "price" in order and order["price"] is not None:
        avg_price = parse_float(order["price"])
    for pkey in ["avgPrice", "activatePrice", "triggerPrice"]:
        if avg_price is None and pkey in order and order[pkey] is not None:
            avg_price = parse_float(order[pkey])

    # qty logic: try quantity, then executedQty, then origQty, else 0
    qty = None
    for qkey in ["quantity", "executedQty", "origQty"]:
        if qkey in order and order[qkey] is not None:
            q = parse_float(order[qkey])
            if q is not None:
                qty = q
                break
    if qty is None:
        qty = 0

    return UnifiedPendingOrder(
        createdTime=int(created_time),
        updatedTime=int(updated_time),
        orderStatus=UnifiedOrderStatus.from_exchange(order_status),
        orderType=UnifiedOrderType.from_exchange(order_type),
        orderId=order_id,
        orderLinkId=str(order_link_id),
        symbol=str(symbol),
        side=UnifiedSide.from_exchange(side),
        avgPrice=avg_price,
        qty=qty,
        source="binance",
    )


def unified_pending_order_from_kucoin(order: dict[str, Any]) -> "UnifiedPendingOrder":
    """Create UnifiedPendingOrder from a KuCoin order dict."""
    # KuCoin orderId = `id`
    order_id = order["id"]
    # clientOid is optional
    order_link_id = str(order["clientOid"])

    # Symbol
    symbol = str(order["symbol"])

    side = UnifiedSide.from_exchange(order["side"])

    # Status ("open" = active, "done" = completed/canceled)
    order_status = UnifiedOrderStatus.from_exchange(order["status"])

    # Order type ('limit', 'market', etc.)
    if order["stop"] in ["up", "down"]:
        order_type = UnifiedOrderType.CONDITIONAL
    else:
        order_type = UnifiedOrderType.from_exchange(order["type"])

    # Created and updated
    created_time = int(order["createdAt"])
    updated_time = int(order["updatedAt"])

    # Average price: just use price
    avg_price = parse_float(order.get("price"))

    # Quantity: just use size
    size = parse_float(order.get("size"))
    if not size:
        raise ValueError(f"Missing or invalid order size in KuCoin order: {order}")

    return UnifiedPendingOrder(
        createdTime=created_time,
        updatedTime=updated_time,
        orderStatus=order_status,
        orderType=order_type,
        orderId=order_id,
        orderLinkId=order_link_id,
        symbol=symbol,
        side=side,
        avgPrice=avg_price,
        qty=size,
        source="kucoin",
    )
