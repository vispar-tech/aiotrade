from typing import Any, Literal

from aiotrade._protocols import HttpClientProtocol
from aiotrade.clients._utils import to_str_fields
from aiotrade.types.bitget import (
    CancelTriggerOrderItem,
    GetPendingTriggerOrdersParams,
    PlaceTpslPlanOrderParams,
    PlaceTriggerOrderParams,
    ProductType,
)


class TriggerMixin:
    """Mixin for Bitget Futures Trigger/Plan Order endpoints."""

    async def get_pending_trigger_orders(
        self: HttpClientProtocol,
        params: GetPendingTriggerOrdersParams,
    ) -> dict[str, Any]:
        """
        Get all (or single) pending trigger/plan orders.

        Rate limit: 10 req/sec/UID.

        Can be used to query one or all current trigger orders.

        API Reference:
            GET /api/v2/mix/order/orders-plan-pending

        Args:
            params: See GetPendingTriggerOrdersParams TypedDict.
                All float fields should be passed as floats when possible.

                Required:
                  - productType (USDT-FUTURES, COIN-FUTURES, USDC-FUTURES)
                  - planType
                Either orderId or clientOid is required
                    (orderId prevails if both provided).

        Returns:
            dict: API JSON response.
        """
        return await self.get(
            "/api/v2/mix/order/orders-plan-pending",
            params=to_str_fields(
                params,
                {"startTime", "endTime", "limit"},
            ),
            auth=True,
        )

    async def cancel_trigger_orders(
        self: HttpClientProtocol,
        product_type: ProductType,
        symbol: str,
        margin_coin: str,
        plan_type: Literal[
            "normal_plan",
            "profit_plan",
            "loss_plan",
            "pos_profit",
            "pos_loss",
            "moving_plan",
        ],
        order_id_list: list[CancelTriggerOrderItem],
    ) -> dict[str, Any]:
        """
        Cancel trigger/plan orders by product type, symbol, and/or ID list.

        Speed limit: 10 times/s (UID).

        This endpoint can cancel by productType, symbol and/or orderIdList.
        If orderIdList is passed, symbol is also required.

        API Reference:
            POST /api/v2/mix/order/cancel-plan-order

        Returns:
            dict: API JSON response.
        """
        params = {
            "productType": product_type,
            "symbol": symbol,
            "marginCoin": margin_coin,
            "planType": plan_type,
            "orderIdList": order_id_list,
        }
        return await self.post(
            "/api/v2/mix/order/cancel-plan-order",
            params=params,
            auth=True,
        )

    async def place_trigger_order(
        self: HttpClientProtocol,
        params: PlaceTriggerOrderParams,
        *,
        channel_api_code: str,
    ) -> dict[str, Any]:
        """
        Place a trigger/plan (normal or trailing stop) order.

        Rate limit: 10 req/sec/UID.

        The interface for placing a trigger or trailing stop order with TP/SL.

        API Reference:
            POST /api/v2/mix/order/place-plan-order

        Args:
            params: See PlaceTriggerOrderParams TypedDict.
                Accepts float or str for all numeric (amount/price/rate) fields.
                All float fields will be serialized as required by the exchange.
            channel_api_code

        Returns:
            dict: API JSON response.
        """
        return await self.post(
            "/api/v2/mix/order/place-plan-order",
            params=to_str_fields(
                params,
                {
                    "size",
                    "price",
                    "callbackRatio",
                    "triggerPrice",
                    "stopSurplusTriggerPrice",
                    "stopSurplusExecutePrice",
                    "stopLossTriggerPrice",
                    "stopLossExecutePrice",
                },
            ),
            auth=True,
            headers={"X-CHANNEL-API-CODE": channel_api_code},
        )

    async def place_tpsl_plan_order(
        self: HttpClientProtocol,
        params: PlaceTpslPlanOrderParams,
        *,
        channel_api_code: str,
    ) -> dict[str, Any]:
        """
        Place a stop-profit (take-profit) or stop-loss plan order.

        Rate limit: 10 times/s (UID).

        Place a stop-profit and stop-loss plan order.

        API Reference:
            POST /api/v2/mix/order/place-tpsl-order

        Args:
            params: See PlaceTpslPlanOrderParams TypedDict.
                Accepts float or str for all numeric (amount/price/rate) fields.
            channel_api_code

        Returns:
            dict: API JSON response.
        """
        return await self.post(
            "/api/v2/mix/order/place-tpsl-order",
            params=to_str_fields(
                params,
                {"triggerPrice", "executePrice", "size", "rangeRate"},
            ),
            auth=True,
            headers={"X-CHANNEL-API-CODE": channel_api_code},
        )
