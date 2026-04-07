import logging
import uuid
from typing import Any, Literal

from aiotrade import KuCoinClient
from aiotrade.types.kucoin import PlaceOrderParams, TakeProfitStopLossOrderParams
from aiotrade.unified.converters.pending_order import unified_pending_order_from_kucoin
from aiotrade.unified.converters.place.futures import (
    convert_unified_place_order_to_kucoin,
)
from aiotrade.unified.converters.position import unified_position_info_from_kucoin
from aiotrade.unified.types import (
    UnifiedAssetMode,
    UnifiedCancelOrderRequest,
    UnifiedMarginMode,
    UnifiedPendingOrder,
    UnifiedPlaceOrderRequest,
    UnifiedPlaceSpotOrderRequest,
    UnifiedPositionInfo,
    UnifiedSide,
)

logger = logging.getLogger("aiotrade.unified")
SET_TRADING_STOP_MAX_RETRIES = 3
SET_TRADING_STOP_RETRY_DELAY = 2  # seconds
MAX_CANCEL_BATCH = 10


class UnifiedKuCoinClient:
    """JKuCoinClient client implementing ExchangeClient."""

    def __init__(
        self,
        account_display: str,
        api_key: str | None = None,
        api_secret: str | None = None,
        passphrase: str | None = None,
        recv_window: int = 5000,
        broker_partner: str | None = None,
        broker_key: str | None = None,
        broker_name: str | None = None,
    ) -> None:
        self._account_display = account_display

        self._client = KuCoinClient(
            api_key=api_key,
            api_secret=api_secret,
            passphrase=passphrase,
            recv_window=recv_window,
            broker_partner=broker_partner,
            broker_key=broker_key,
            broker_name=broker_name,
        )

    async def get_margin_mode(self, symbol: str | None) -> UnifiedMarginMode:
        """Get current margin mode for a symbol/account."""
        if symbol is None:
            raise ValueError("symbol must be specified for KuCoin margin mode query")
        response = await self._client.get_margin_mode(symbol)
        data = response.get("data", {})
        margin_mode = str(data.get("marginMode", "")).upper()
        if margin_mode == "CROSS":
            return UnifiedMarginMode.CROSS
        if margin_mode == "ISOLATED":
            return UnifiedMarginMode.ISOLATED
        raise RuntimeError(f"Could not parse KuCoin margin mode response: {response}")

    async def update_margin_mode(
        self, symbol: str | None, mode: UnifiedMarginMode
    ) -> None:
        """Update margin mode for a symbol/account."""
        if symbol is None:
            raise ValueError("symbol must be specified for KuCoin set margin mode")
        await self._client.switch_margin_mode(
            symbol=symbol, margin_mode=mode.to_kucoin()
        )

    async def get_hedge_mode(self, symbol: str | None) -> bool | None:
        """Query whether hedge mode is enabled."""
        response = await self._client.get_position_mode()
        data = response.get("data", {})
        position_mode = data.get("positionMode", None)
        if position_mode is None:
            return None
        # "1" or 1: hedge mode enabled, "0" or 0: one-way mode
        return bool(int(position_mode))

    async def set_hedge_mode(self, enabled: bool) -> None:
        """Enable or disable hedge mode."""
        await self._client.switch_position_mode(position_mode=enabled)

    async def get_asset_mode(self) -> UnifiedAssetMode | None:
        """Query the current asset mode (e.g., 'USDT', 'multi-asset', etc)."""
        raise NotImplementedError("KuCoin does not support querying asset mode.")

    async def set_asset_mode(self, mode: UnifiedAssetMode) -> None:
        """Set the asset mode (e.g., 'USDT', 'multi-asset', etc)."""
        raise NotImplementedError("KuCoin does not support setting asset mode.")

    async def get_usdt_available_balance(self) -> float | None:
        """Get the available USDT balance for the account."""
        response = await self._client.get_futures_account()
        data = response.get("data", {})
        if data.get("currency") != "USDT":
            return None
        balance = data.get("availableBalance")
        return float(balance) if balance is not None else None

    async def get_spot_usdt_balance(self) -> float | None:
        """Get the spot USDT balance for the account."""
        raise NotImplementedError("Spot account queries are not supported for KuCoin.")

    async def get_position_info(
        self, symbol: str | None = None
    ) -> list[UnifiedPositionInfo]:
        """Get current position information incl. open conditional/tp/sl orders."""
        response = await self._client.get_positions()
        positions: list[dict[str, Any]] = response.get("data", [])

        orders_response = await self._client.get_stop_orders(page_size=1000)
        orders_list: list[dict[str, Any]] = orders_response.get("data", {}).get(
            "items", []
        )

        # Optionally filter by symbol (if provided)
        if symbol is not None:
            positions = [pos for pos in positions if pos.get("symbol") == symbol]

        return [
            unified_position_info_from_kucoin(self._account_display, orders_list, item)
            for item in positions
        ]

    # Order methods
    async def close_position(
        self, position: UnifiedPositionInfo, order: UnifiedPlaceOrderRequest
    ) -> dict[str, Any]:
        """Close position."""
        side: Literal["sell", "buy"] = (
            "sell" if position["side"] == UnifiedSide.LONG else "buy"
        )
        order_type: Literal["market", "limit"] = "market"
        close_params = PlaceOrderParams(
            symbol=position["symbol"],
            side=side,
            type=order_type,
            size=int(position["size"]),
            closeOrder=True,
        )
        if (order_link_id := order.get("order_link_id")) is not None:
            close_params["clientOid"] = order_link_id
        else:
            close_params["clientOid"] = "jd_close_" + uuid.uuid4().hex[:8]
        return await self._client.add_order(params=close_params)

    async def place_spot_order(
        self, params: UnifiedPlaceSpotOrderRequest
    ) -> dict[str, Any]:
        """Place spot order."""
        raise NotImplementedError("Spot order placement is not supported for KuCoin.")

    async def get_spot_order_exec_qty(self, response: dict[str, Any]) -> float:
        """Get the executed quantity for a placed spot order.

        Accepts the response as returned from place_spot_order.
        """
        raise NotImplementedError(
            "Spot order execution quantity query is not supported for KuCoin."
        )

    async def batch_place_order(
        self, has_existing_position: bool, requests: list[UnifiedPlaceOrderRequest]
    ) -> dict[str, Any]:
        """
        Place multiple orders at once and return all results.

        Unified response schema for each order result:
        {
            "orderId": ...,
            "clientOid": ...,
            "symbol": ...,
            "code": ...,
            "success": True/False,
            "raw": ...,
        }
        """
        main_orders: list[PlaceOrderParams] = []
        tp_sl_orders: list[TakeProfitStopLossOrderParams] = []

        for req in requests:
            main_params, tp_sl_params = convert_unified_place_order_to_kucoin(req)
            if main_params is not None:
                main_orders.append(main_params)
            if tp_sl_params is not None:
                tp_sl_orders.append(tp_sl_params)

        results: list[dict[str, Any]] = []
        batch_error = None

        # Handle main group (batch)
        if main_orders:
            try:
                batch_result = await self._client.batch_add_orders(orders=main_orders)
                res_list: list[dict[str, Any]] = batch_result.get("data", [])

                for entry in res_list:
                    results.append(
                        {
                            "orderId": entry.get("orderId"),
                            "clientOid": entry.get("clientOid"),
                            "symbol": entry.get("symbol"),
                            "code": entry.get("code"),
                            "success": entry.get("code") == "200000",
                            "raw": entry,
                        }
                    )
            except Exception as e:
                batch_error = e
                logger.warning(
                    "%s Exception during batch_add_orders: %s",
                    self._account_display,
                    str(e),
                    exc_info=True,
                )
                for main_order in main_orders:
                    results.append(
                        {
                            "orderId": None,
                            "clientOid": main_order.get("clientOid"),
                            "symbol": main_order.get("symbol"),
                            "code": None,
                            "success": False,
                            "raw": None,
                        }
                    )

        # Handle individual TP/SL orders
        for tp_sl in tp_sl_orders:
            try:
                result = await self._client.add_tp_sl_order(params=tp_sl)
                code = result.get("code")
                success = code == "200000"
                data = result.get("data", {})
                results.append(
                    {
                        "orderId": data.get("orderId"),
                        "clientOid": data.get("clientOid", tp_sl.get("clientOid")),
                        "symbol": tp_sl.get("symbol"),
                        "code": code,
                        "success": success,
                        "raw": result,
                    }
                )
            except Exception as e:
                logger.warning(
                    "%s Exception during add_tp_sl_order: %s",
                    self._account_display,
                    str(e),
                    exc_info=True,
                )
                results.append(
                    {
                        "orderId": None,
                        "clientOid": tp_sl.get("clientOid"),
                        "symbol": tp_sl.get("symbol"),
                        "code": None,
                        "success": False,
                        "raw": None,
                    }
                )

        # Если не удалось отправить ни одного ордера — бросаем ошибку
        if batch_error is not None and not tp_sl_orders:
            raise Exception(
                "Batch orders failed: "
                + (repr(batch_error) if batch_error else "Unknown error")
            )

        return {"results": results}

    async def batch_cancel_order(
        self, requests: list[UnifiedCancelOrderRequest]
    ) -> None:
        """Cancel multiple orders at once using KuCoin batch cancel endpoint."""
        if not requests:
            return

        # KuCoin allows up to 10 cancels per request

        order_ids_list: list[str] = []
        client_oids_list: list[dict[str, str]] = []

        for req in requests:
            order_id = req.get("order_id")
            order_link_id = req.get("order_link_id")
            symbol = req["symbol"]

            if order_id is not None:
                # KuCoin expects str type for orderIdsList, coerce if int
                order_ids_list.append(str(order_id))
            elif order_link_id is not None:
                client_oids_list.append({"symbol": symbol, "clientOid": order_link_id})

        errors: list[Exception] = []

        # Соблюдаем лимит Kucoin: не более 10 ордеров за вызов
        total = max(len(order_ids_list), len(client_oids_list))
        for i in range(0, total, MAX_CANCEL_BATCH):
            batch_payload: dict[str, Any] = {}
            order_ids_batch = order_ids_list[i : i + MAX_CANCEL_BATCH]
            client_oids_batch = (
                client_oids_list[i : i + MAX_CANCEL_BATCH]
                if not order_ids_batch
                else []
            )
            if order_ids_batch:
                batch_payload["orderIdsList"] = order_ids_batch
            elif client_oids_batch:
                batch_payload["clientOidsList"] = client_oids_batch
            else:
                continue
            try:
                await self._client.batch_cancel_orders(batch_payload)  # type: ignore
            except Exception as exc:
                logger.warning(
                    "%s batch_cancel_order: Error while cancelling orders: %s",
                    self._account_display,
                    exc,
                )
                errors.append(exc)

        if errors:
            raise errors[0]

    async def get_pending_orders(self) -> list[UnifiedPendingOrder]:
        """Retrieve all pending (regular + algo) orders."""
        orders_response = await self._client.get_order_list(
            status="active", page_size=1000
        )
        orders_list: list[dict[str, Any]] = orders_response.get("data", {}).get(
            "items", []
        )

        # Also fetch stop/algo orders, from Kucoin's stop order API
        stop_orders_response = await self._client.get_stop_orders(page_size=1000)
        stop_orders_list: list[dict[str, Any]] = stop_orders_response.get(
            "data", {}
        ).get("items", [])

        # Combine regular and stop orders
        combined_orders = orders_list + stop_orders_list

        return [unified_pending_order_from_kucoin(x) for x in combined_orders]

    # Trading methods
    async def _cancel_trading_stop_orders(
        self,
        symbol: str,
        position: UnifiedPositionInfo | None,
        take_profit: float | None,
        stop_loss: float | None,
        active_price: float | None,
        trailing_delivation: float | None,
    ) -> None:
        """Cancel TP/SL/Trailing orders that need to be replaced."""
        if position is None:
            return
        if not (additional := position.get("additional")):
            logger.warning(
                "%s set_trading_stop: Provided position has no "
                "'additional' field for symbol=%s",
                self._account_display,
                symbol,
            )
            return

        cancel_orders: list[UnifiedCancelOrderRequest] = []

        if len(additional["matching_tp_orders"]) and (
            take_profit is not None
            or (trailing_delivation is not None and active_price is not None)
        ):
            cancel_orders.extend(
                [
                    UnifiedCancelOrderRequest(
                        symbol=order["symbol"], order_id=order["id"]
                    )
                    for order in additional["matching_tp_orders"]
                ]
            )

        if len(additional["matching_sl_orders"]) and stop_loss is not None:
            cancel_orders.extend(
                [
                    UnifiedCancelOrderRequest(
                        symbol=order["symbol"], order_id=order["id"]
                    )
                    for order in additional["matching_sl_orders"]
                ]
            )

        if len(additional["matching_trailing_orders"]) and (
            trailing_delivation is not None and active_price is not None
        ):
            cancel_orders.extend(
                [
                    UnifiedCancelOrderRequest(
                        symbol=order["symbol"], order_id=order["id"]
                    )
                    for order in additional["matching_trailing_orders"]
                ]
            )

        if cancel_orders:
            logger.info(
                "%s set_trading_stop: Cancelling %d TP/SL/Trailing orders "
                "for symbol=%s. Order IDs: %s",
                self._account_display,
                len(cancel_orders),
                symbol,
                [order.get("order_id") for order in cancel_orders],
            )
            try:
                await self.batch_cancel_order(cancel_orders)
                logger.info(
                    "%s set_trading_stop: Successfully cancelled orders for symbol=%s",
                    self._account_display,
                    symbol,
                )
            except Exception as exc:
                logger.warning(
                    "%s set_trading_stop: Failed to cancel orders for symbol=%s: %s",
                    self._account_display,
                    symbol,
                    exc,
                )

    async def set_trading_stop(
        self,
        symbol: str,
        take_profit: float | None = None,
        stop_loss: float | None = None,
        active_price: float | None = None,
        trailing_delivation: float | None = None,
        position: UnifiedPositionInfo | None = None,
        side: UnifiedSide | None = None,
        qty: float | None = None,
    ) -> None:
        """Set trading stop on KuCoin."""
        await self._cancel_trading_stop_orders(
            symbol=symbol,
            position=position,
            take_profit=take_profit,
            stop_loss=stop_loss,
            active_price=active_price,
            trailing_delivation=trailing_delivation,
        )

        order_side: Literal["buy", "sell"]
        size: float | None = position["size"] if position else qty
        if size is None:
            raise ValueError(
                "set_trading_stop: Either a valid 'position' or "
                "'qty' must be provided for KuCoin."
            )
        if position is not None:
            order_side = "buy" if position["side"] == UnifiedSide.LONG else "sell"
        elif side is not None:
            order_side = "buy" if side == UnifiedSide.LONG else "sell"
        else:
            raise ValueError(
                "set_trading_stop: Either a valid 'position' or "
                "both 'side' and 'qty' must be provided for KuCoin."
            )

        batch_orders: list[PlaceOrderParams] = []

        def _append_trading_stop(
            price: float,
            remark: str,
            stop_direction: Literal["down", "up"],
        ) -> None:
            params: PlaceOrderParams = {
                "clientOid": uuid.uuid4().hex,
                "symbol": symbol,
                "positionSide": "BOTH",
                "side": "sell" if order_side == "buy" else "buy",
                "type": "market",
                "stopPrice": price,
                "stop": stop_direction,
                "stopPriceType": "TP",
                "reduceOnly": True,
                "size": int(size),
                "remark": remark,
            }

            batch_orders.append(params)

        if take_profit is not None:
            _append_trading_stop(
                price=take_profit,
                remark="set_trading_stop_tp",
                stop_direction="up" if order_side == "buy" else "down",
            )
        if active_price is not None:
            _append_trading_stop(
                price=active_price,
                remark="set_trading_stop_tp",
                stop_direction="up" if order_side == "buy" else "down",
            )
        if stop_loss is not None:
            _append_trading_stop(
                price=stop_loss,
                remark="set_trading_stop_sl",
                stop_direction="down" if order_side == "buy" else "up",
            )
        response = await self._client.batch_add_orders(batch_orders)

        response_data: list[dict[str, Any]] = response.get("data", [])

        if response_data:
            # Kucoin returns per-order results in `data`
            errors: list[dict[str, Any]] = [
                x
                for x in response_data
                if x.get("code") != "200000" and x.get("code") is not None
            ]
            if errors:
                raise Exception(f"Kucoin batch_add_orders errors: {errors}")

    async def set_leverage(self, symbol: str, leverage: float) -> None:
        """Set leverage for a symbol or account."""
        return
