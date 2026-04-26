from typing import Any, Literal

from aiotrade._protocols import HttpClientProtocol
from aiotrade.types.gate import (
    FuturesPlaceOrder,
    FuturesPlaceTrailingOrder,
    FuturesPriceTriggeredOrder,
    MarginMode,
    Settle,
)
from aiotrade.utils.formatters import to_str_fields


class FuturesMixin:
    async def get_futures_contracts(
        self: HttpClientProtocol,
        settle: Settle,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        """
        Query all futures contracts.

        See:
            https://www.gate.io/docs/developers/apiv4/en/#list-all-futures-contracts

        Args:
            settle: Settle currency.
            limit: Maximum number of records returned in a single list.
            offset: List offset, starting from 0.

        Returns:
            List of contract information for all futures contracts (per settle).
        """
        params: dict[str, int] = {}

        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset

        return await self.get(f"/futures/{settle}/contracts", params=params)

    async def get_futures_contract(
        self: HttpClientProtocol, settle: Settle, contract: str
    ) -> dict[str, Any]:
        """
        Query single contract information.

        See:
            https://www.gate.io/docs/developers/apiv4/en/#get-a-single-futures-contract

        Args:
            settle: Settle currency.
            contract: Futures contract.

        Returns:
            Contract information for the given contract and settle.
        """
        endpoint = f"/futures/{settle}/contracts/{contract}"
        return await self.get(endpoint)

    async def list_futures_candlesticks(
        self: HttpClientProtocol,
        settle: Settle,
        contract: str,
        interval: str | None = None,
        range_from: int | None = None,
        range_to: int | None = None,
        limit: int | None = None,
        timezone: str | None = None,
    ) -> dict[str, Any]:
        """
        Futures market K-line (candlestick) chart.

        Return specified contract candlesticks. If `contract` is prefixed with
        `mark_`, the contract's mark price candlesticks are returned; if
        prefixed with `index_`, index price candlesticks will be returned.
        Maximum of 2000 points are returned in one query. Be sure not to exceed
        the limit when specifying `from`, `to` and `interval`.

        See:
            https://www.gate.io/docs/developers/apiv4/en/#futures-market-candlesticks

        Args:
            settle: Settle currency.
            contract: Futures contract.
            interval: Interval time between data points.
                Note: '1w' = natural week (Mon-Sun), '7d' = every 7 days since
                unix 0. '30d' = 1 natural month (not 30 days).
            range_from: Start time of candlesticks, as unix timestamp (seconds).
                Defaults to (to - 100 * interval) if not specified.
            range_to: End time of the K-line chart (unix timestamp in seconds),
                defaults to current time if not specified.
            limit: Maximum number of recent data points to return (conflicts
                with _from/to, if either is specified, request will be rejected).
                Max 2000.
            timezone: Time zone: all/utc0/utc8, default utc0.
        Returns:
            Dict[str, Any]: List of candlestick data points.

        Raises:
            ValueError: If any argument is invalid.
        """
        params: dict[str, str | int] = {"contract": contract}

        if interval is not None:
            params["interval"] = interval
        if range_from is not None:
            params["from"] = range_from
        if range_to is not None:
            params["to"] = range_to
        if limit is not None:
            if limit > 2000:
                raise ValueError("Invalid value for parameter `limit`, must be ≤ 2000")
            params["limit"] = limit
        if timezone is not None:
            params["timezone"] = timezone

        return await self.get(f"/futures/{settle}/candlesticks", params=params)

    async def list_futures_tickers(
        self: HttpClientProtocol,
        settle: Settle,
        contract: str | None = None,
    ) -> dict[str, Any]:
        """
        Get all futures trading statistics.

        See:
            https://www.gate.io/docs/developers/apiv4/en/#list-futures-tickers

        Args:
            settle: Settle currency.
            contract: Futures contract to query data for only this contract.
        Returns:
            Dict[str, Any]: List of ticker data.
        """
        params: dict[str, str] = {}
        if contract is not None:
            params["contract"] = contract

        return await self.get(f"/futures/{settle}/tickers", params=params)

    async def list_futures_risk_limit_tiers(
        self: HttpClientProtocol,
        settle: Settle,
        contract: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        """
        Query risk limit tiers.

        When the 'contract' parameter is not passed,
        this queries the risk limits for the top 100 markets.
        Limit and offset operate at the market level (not on return array).

        See:
            https://www.gate.io/docs/developers/apiv4/en/#query-risk-limit-tiers

        Args:
            settle: Settle currency.
            contract: Futures contract. Query for a single contract.
            limit: Maximum number of records returned, [1-1000]
            offset: Offset for pagination, starting from 0.

        Returns:
            Dict[str, Any]: List of risk limit tiers.
        """
        params: dict[str, str | int] = {}
        if contract is not None:
            params["contract"] = contract
        if limit is not None:
            if limit < 1 or limit > 1000:
                raise ValueError(
                    "Invalid value for parameter `limit`, must be between 1 and 1000"
                )
            params["limit"] = limit
        if offset is not None:
            if offset < 0:
                raise ValueError("Invalid value for parameter `offset`, must be ≥ 0")
            params["offset"] = offset

        return await self.get(f"/futures/{settle}/risk_limit_tiers", params=params)

    async def get_futures_account(
        self: HttpClientProtocol,
        settle: Settle,
    ) -> dict[str, Any]:
        """
        Get futures account.

        See:
            https://www.gate.io/docs/developers/apiv4/en/#get-futures-account

        Args:
            settle: Settle currency.

        Returns:
            dict[str, Any]: Futures account info.
        """
        return await self.get(f"/futures/{settle}/accounts", auth=True)

    async def list_positions(
        self: HttpClientProtocol,
        settle: Settle,
        holding: bool | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        """
        Get user position list.

        See:
            https://www.gate.io/docs/developers/apiv4/en/#list-positions

        Args:
            settle: Settle currency.
            holding: Return only positions with holdings (true) or all (false).
            limit: Maximum number of records [1-1000].
            offset: Pagination offset, starting from 0.

        Returns:
            Dict[str, Any]: List of positions.
        """
        params: dict[str, str | int | bool] = {}
        if holding is not None:
            params["holding"] = holding
        if limit is not None:
            if limit < 1 or limit > 1000:
                raise ValueError(
                    "Invalid value for parameter `limit`, must be between 1 and 1000"
                )
            params["limit"] = limit
        if offset is not None:
            if offset < 0:
                raise ValueError("Invalid value for parameter `offset`, must be ≥ 0")
            params["offset"] = offset

        return await self.get(
            f"/futures/{settle}/positions",
            params=params,
            auth=True,
        )

    async def get_position(
        self: HttpClientProtocol,
        settle: Settle,
        contract: str,
    ) -> dict[str, Any]:
        """
        Get single position information.

        See:
            https://www.gate.io/docs/developers/apiv4/en/#get-single-position

        Args:
            settle: Settle currency.
            contract: Futures contract.

        Returns:
            dict[str, Any]: Position info.
        """
        return await self.get(f"/futures/{settle}/positions/{contract}", auth=True)

    async def update_position_leverage(
        self: HttpClientProtocol,
        settle: Settle,
        contract: str,
        leverage: float | None = None,
        cross_leverage_limit: float | None = None,
        pid: int | None = None,
    ) -> dict[str, Any]:
        """
        Update position leverage.

        See:
            https://www.gate.io/docs/developers/apiv4/en/#update-position-leverage

        Args:
            settle: Settle currency.
            contract: Futures contract.
            leverage: New position leverage.
            cross_leverage_limit: Cross margin leverage
                (valid only when `leverage` is 0).
            pid: Product ID.

        Returns:
            dict[str, Any]: Position info after update.
        """
        params: dict[str, str | int] = {}
        if leverage is not None:
            params["leverage"] = str(leverage)
        if cross_leverage_limit is not None:
            params["cross_leverage_limit"] = str(cross_leverage_limit)
        if pid is not None:
            params["pid"] = pid

        return await self.post(
            f"/futures/{settle}/positions/{contract}/leverage",
            params=params,
            use_params_as_query=True,
            auth=True,
        )

    async def update_position_cross_mode(
        self: HttpClientProtocol, settle: Settle, mode: MarginMode, contract: str
    ) -> dict[str, Any]:
        """
        Switch Position Margin Mode.

        See:
            https://www.gate.io/docs/developers/apiv4/en/#switch-cross-mode

        Args:
            settle: Settle currency.
            futures_position_cross_mode:
                Dictionary for cross mode switch request.

        Returns:
            dict[str, Any]: Updated position info.
        """
        return await self.post(
            f"/futures/{settle}/positions/cross_mode",
            params={"mode": mode, "contract": contract},
            auth=True,
        )

    async def set_dual_mode(
        self: HttpClientProtocol,
        settle: Settle,
        dual_mode: bool,
    ) -> dict[str, Any]:
        """
        Set position mode.

        See:
            https://www.gate.io/docs/developers/apiv4/en/#set-position-mode

        Args:
            settle: Settle currency.
            dual_mode: Whether to enable dual mode.

        Returns:
            dict[str, Any]: Account info after mode update.
        """
        params = {"dual_mode": str(dual_mode)}
        return await self.post(
            f"/futures/{settle}/dual_mode",
            params=params,
            use_params_as_query=True,
            auth=True,
        )

    async def list_futures_orders(
        self: HttpClientProtocol,
        settle: Settle,
        status: str,
        contract: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        last_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Query futures order list.

        - Zero-fill order cannot be retrieved for 10 minutes after cancellation.
        - Historical orders: only data within the past 6 months is supported by default.
            For a longer period, use GET /futures/{settle}/orders_timerange.

        See:
            https://www.gate.io/docs/developers/apiv4/en/#list-futures-orders

        Args:
            settle: Settle currency.
            status: Order status to filter.
            contract: Futures contract to filter.
            limit: Maximum number of records [1-1000].
            offset: List offset, starting from 0.
            last_id: Use the ID of the last record of the previous list for pagination.
        Returns:
            dict[str, Any]: List of orders.
        """
        params: dict[str, str | int] = {"status": status}
        if contract is not None:
            params["contract"] = contract
        if limit is not None:
            if limit < 1 or limit > 1000:
                raise ValueError(
                    "Invalid value for parameter `limit`, must be between 1 and 1000"
                )
            params["limit"] = limit
        if offset is not None:
            if offset < 0:
                raise ValueError("Invalid value for parameter `offset`, must be ≥ 0")
            params["offset"] = offset
        if last_id is not None:
            params["last_id"] = last_id

        return await self.get(f"/futures/{settle}/orders", params=params, auth=True)

    async def create_futures_order(
        self: HttpClientProtocol,
        settle: Settle,
        order: FuturesPlaceOrder,
        x_gate_exptime: str | None = None,
    ) -> dict[str, Any]:
        """
        Place a single futures order.

        - When placing an order, specify the number of contracts via `size`,
            not the number of coins.
        - The number of coins per contract is returned in contract
            details under `quanto_multiplier`.
        - Cannot retrieve completed orders after 10 minutes of withdrawal.
        - Setting `reduce_only` to `true` can prevent the position from
            being penetrated when reducing the position.
        - In single-position mode: to close the position, set `size=0` and `close=true`.
        - In double warehouse mode:
            - Reduce position: `reduce_only=true`, positive `size` for short,
                negative for long.
            - Add position: positive `size` for long, negative for short.
            - Close position: set `size=0`, provide direction via `auto_size`,
                and set `reduce_only=true`.
        - Set `stp_act` for advanced transaction restrictions.
            See body param `stp_act` in docs.

        Args:
            settle: Settle currency (e.g., 'usdt').
            order: Order parameters as dict.
            x_gate_exptime: Optional, expiration timestamp (in ms) for the order.

        Returns:
            Dict[str, Any]: Placed order result.

        Raises:
            ValueError: If required arguments are missing or invalid.
        """
        headers: dict[str, str] = {}
        if x_gate_exptime is not None:
            headers["x-gate-exptime"] = x_gate_exptime

        return await self.post(
            f"/futures/{settle}/orders",
            params=to_str_fields(order, {"size", "price"}),
            headers=headers,
            auth=True,
        )

    async def create_batch_futures_order(
        self: HttpClientProtocol,
        settle: Settle,
        orders: list[FuturesPlaceOrder],
        x_gate_exptime: str | None = None,
    ) -> dict[str, Any]:
        """
        Place batch futures orders.

        - Up to 10 orders per request.
        - If any of the order's parameters are missing or in the wrong format,
            all will fail with HTTP 400.
        - Orders that pass parameter validation execute independently.
        - The response is an array corresponding to the input orders,
            with `succeeded` key indicating success.
        - On failure, a `label` field indicates the cause of the error.

        Args:
            settle: Settle currency (e.g., 'usdt').
            orders: List of order dicts.
            x_gate_exptime: Expiration time in ms.

        Returns:
            List of order result dicts.

        Raises:
            ValueError: If settle or futures_order is not provided or invalid.
        """
        if not orders:
            raise ValueError("Missing `futures_order`, must be a non-empty list")

        headers: dict[str, str] = {}
        if x_gate_exptime is not None:
            headers["x-gate-exptime"] = x_gate_exptime

        return await self.post(
            f"/futures/{settle}/batch_orders",
            params=to_str_fields(orders, {"size", "price"}),
            headers=headers,
            auth=True,
        )

    async def list_position_close(
        self: HttpClientProtocol,
        settle: Settle,
        contract: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        range_from: int | None = None,
        range_to: int | None = None,
        side: Literal["long", "short"] | None = None,
        pnl: Literal["profit", "loss"] | None = None,
    ) -> dict[str, Any]:
        """
        Query position close history.

        Args:
            settle: Settle currency.
            contract: Futures contract, return related data only if specified.
            limit: Maximum number of records returned in a single list (1~1000).
            offset: List offset, starting from 0.
            range_from: Start timestamp (Unix timestamp).
            range_to: Termination timestamp (Unix timestamp).
            side: Query side, "long" or "short".
            pnl: Query profit or loss, "profit" or "loss".

        Returns:
            Dictionary with position close history.

        Raises:
            ValueError: If settle is not provided.
        """
        params: dict[str, Any] = {}
        if contract is not None:
            params["contract"] = contract
        if limit is not None:
            if limit > 1000 or limit < 1:
                raise ValueError("`limit` must be between 1 and 1000")
            params["limit"] = limit
        if offset is not None:
            if offset < 0:
                raise ValueError("`offset` must be greater than or equal to 0")
            params["offset"] = offset
        if range_from is not None:
            params["from"] = range_from
        if range_to is not None:
            params["to"] = range_to
        if side is not None:
            params["side"] = side
        if pnl is not None:
            params["pnl"] = pnl

        return await self.get(
            f"/futures/{settle}/position_close",
            params=params,
            auth=True,
        )

    async def cancel_batch_future_orders(
        self: HttpClientProtocol,
        settle: Settle,
        order_ids: list[str],
        x_gate_exptime: str | None = None,
    ) -> dict[str, Any]:
        """
        Cancel batch futures orders by order ID.

        Args:
            settle: Settle currency.
            order_ids: List of order IDs (maximum 20).
            x_gate_exptime: Expiration time.

        Returns:
            Dictionary with cancel order result.

        Raises:
            ValueError: If parameters are missing or invalid.
        """
        if not order_ids:
            raise ValueError("Missing `order_ids`, must be a non-empty list")

        headers: dict[str, str] = {}
        if x_gate_exptime is not None:
            headers["x-gate-exptime"] = x_gate_exptime

        return await self.post(
            f"/futures/{settle}/batch_cancel_orders",
            params=order_ids,  # type: ignore
            headers=headers,
            auth=True,
        )

    async def get_futures_risk_limit_table(
        self: HttpClientProtocol,
        settle: Settle,
        table_id: str,
    ) -> dict[str, Any]:
        """
        Query risk limit table by table_id.

        Args:
            settle: Settle currency.
            table_id: Risk limit table ID.

        Returns:
            Dictionary with risk limit table information.

        Raises:
            ValueError: If any argument is missing or invalid.
        """
        params: dict[str, str] = {"table_id": table_id}
        return await self.get(
            f"/futures/{settle}/risk_limit_table",
            params=params,
            auth=True,
        )

    async def list_trailing_orders(  # noqa: C901, PLR0912
        self: HttpClientProtocol,
        settle: Settle,
        contract: str | None = None,
        is_finished: bool | None = None,
        start_at: int | None = None,
        end_at: int | None = None,
        page_num: int | None = None,
        page_size: int | None = None,
        sort_by: Literal[1, 2] | None = None,
        hide_cancel: bool | None = None,
        related_position: Literal[1, 2] | None = None,
        sort_by_trigger: bool | None = None,
        reduce_only: Literal[1, 2] | None = None,
        side: Literal[1, 2] | None = None,
    ) -> dict[str, Any]:
        """
        Get trail order list.

        Args:
            settle: Settle currency ('usdt' or 'btc')
            contract: Contract name
            is_finished: Whether historical order
            start_at: Start time of time range (optional, int - epoch ms)
            end_at: End time of time range (optional, int - epoch ms)
            page_num: Page number, starting from 1
            page_size: Items per page
            sort_by: Sort field, 1-creation time, 2-end time
            hide_cancel: Hide cancelled orders
            related_position: Only return orders associated with
                this position, 1-long, 2-short
            sort_by_trigger: Sort by trigger price and activation price
            reduce_only: Whether reduce only, 1-yes, 2-no
            side: Direction, 1-long, 2-short

        Returns:
            Dict[str, Any]: List of trailing orders.

        Raises:
            ValueError: If any argument is invalid.
        """
        params: dict[str, str | int | bool] = {}
        if contract is not None:
            params["contract"] = contract
        if is_finished is not None:
            params["is_finished"] = is_finished
        if start_at is not None:
            params["start_at"] = start_at
        if end_at is not None:
            params["end_at"] = end_at
        if page_num is not None:
            if page_num < 1:
                raise ValueError("Page number must be ≥ 1")
            params["page_num"] = page_num
        if page_size is not None:
            if page_size < 1:
                raise ValueError("Page size must be ≥ 1")
            params["page_size"] = page_size
        if sort_by is not None:
            params["sort_by"] = sort_by
        if hide_cancel is not None:
            params["hide_cancel"] = hide_cancel
        if related_position is not None:
            params["related_position"] = related_position
        if sort_by_trigger is not None:
            params["sort_by_trigger"] = sort_by_trigger
        if reduce_only is not None:
            params["reduce_only"] = reduce_only
        if side is not None:
            params["side"] = side

        return await self.get(
            f"/futures/{settle}/autoorder/v1/trail/list", params=params, auth=True
        )

    async def create_trailing_order(
        self: HttpClientProtocol,
        settle: Settle,
        order: FuturesPlaceTrailingOrder,
    ) -> dict[str, Any]:
        """
        Create a new trailing order (price-tracked order).

        See: https://www.gate.io/docs/developers/apiv4/en/#create-trail-order

        Args:
            settle: Settle currency (e.g., "usdt").
            order: Parameters for the trailing order creation,
                see FuturesPlaceTrailingOrder.

        Returns:
            dict[str, Any]: Created trailing order result.

        Raises:
            ValueError: If required arguments are missing or invalid.
        """
        return await self.post(
            f"/futures/{settle}/autoorder/v1/trail/create",
            params=to_str_fields(order, {"activation_price", "amount"}),
            auth=True,
        )

    async def list_price_triggered_orders(
        self: HttpClientProtocol,
        settle: Settle,
        status: Literal[
            "open",  # Active
            "finished",  # Finished
            "inactive",  # Inactive, only applies to order take-profit/stop-loss
            "invalid",  # Invalid, only applies to order take-profit/stop-loss
        ],
        contract: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        """
        Query auto order list (price-triggered orders).

        Args:
            settle: Settle currency (e.g., 'usdt').
            status: Query order list based on status.
            contract: Futures contract, return related data only if specified.
            limit: Maximum number of records returned (max 1000).
            offset: List offset, starting from 0.

        Returns:
            Dict[str, Any]: List of price-triggered (conditional) orders.

        Raises:
            ValueError: If any argument is invalid.
        """
        params: dict[str, str | int] = {"status": status}
        if contract is not None:
            params["contract"] = contract
        if limit is not None:
            if limit > 1000:
                raise ValueError("Invalid value for `limit`, must be ≤ 1000")
            if limit < 1:
                raise ValueError("Invalid value for `limit`, must be ≥ 1")
            params["limit"] = limit
        if offset is not None:
            if offset < 0:
                raise ValueError("Invalid value for `offset`, must be ≥ 0")
            params["offset"] = offset

        return await self.get(
            f"/futures/{settle}/price_orders", params=params, auth=True
        )

    async def create_price_triggered_order(
        self: HttpClientProtocol,
        settle: Settle,
        order: "FuturesPriceTriggeredOrder",
        *,
        x_gate_exptime: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a price-triggered (conditional) order.

        Args:
            settle: Settle currency (e.g. "usdt" or "btc").
            order: Price-triggered order request body (FuturesPriceTriggeredOrder).
            x_gate_exptime: Set customized request expiration epoch time (s).

        Returns:
            Dict[str, Any]: Price-triggered order response.

        Raises:
            ValueError: If required arguments are missing or invalid.
        """
        headers: dict[str, str] = {}
        if x_gate_exptime is not None:
            headers["x-gate-exptime"] = x_gate_exptime

        return await self.post(
            f"/futures/{settle}/price_orders",
            params=to_str_fields(order, {"price"}),
            headers=headers,
            auth=True,
        )

    async def cancel_price_triggered_order(
        self: HttpClientProtocol,
        settle: Settle,
        order_id: str,
        x_gate_exptime: str | None = None,
    ) -> dict[str, Any]:
        """
        Cancel a single price-triggered (conditional) order.

        Args:
            settle: Settle currency (e.g., "usdt" or "btc").
            order_id: ID returned when order is successfully created.
            x_gate_exptime: Set customized request expiration epoch time (s).

        Returns:
            Dictionary with cancel order result.

        Raises:
            ValueError: If required arguments are missing or invalid.
        """
        if not order_id:
            raise ValueError("Missing required argument `order_id`")

        headers: dict[str, str] = {}
        if x_gate_exptime is not None:
            headers["x-gate-exptime"] = x_gate_exptime

        return await self.delete(
            f"/futures/{settle}/price_orders/{order_id}",
            headers=headers,
            use_params_as_query=True,
            auth=True,
        )

    async def terminate_trail_order(
        self: HttpClientProtocol,
        settle: Settle,
        id: int | None = None,
        text: str | None = None,
        x_gate_exptime: str | None = None,
    ) -> dict[str, Any]:
        """
        Terminate a trailing order.

        Args:
            settle: Settle currency (either 'usdt' or 'btc').
            id: Order ID. If specified, 'text' is not needed.
            text: Custom text for terminating (if 'id' is not specified,
                terminate based on user_id and text).
            x_gate_exptime: Set customized request expiration epoch time (s).

        Returns:
            Dictionary with result of termination.

        Raises:
            ValueError: If required arguments are missing or invalid.
        """
        if id is None and not text:
            raise ValueError("Must specify at least one of `id` or `text`.")

        headers: dict[str, str] = {}
        if x_gate_exptime is not None:
            headers["x-gate-exptime"] = x_gate_exptime

        params: dict[str, Any] = {}
        if id is not None:
            params["id"] = id
        if text is not None:
            params["text"] = text

        return await self.post(
            f"/futures/{settle}/autoorder/v1/trail/stop",
            params=params,
            headers=headers,
            auth=True,
        )
