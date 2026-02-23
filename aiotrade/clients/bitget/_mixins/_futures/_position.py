from typing import Any, Literal

from aiotrade._protocols import HttpClientProtocol
from aiotrade.types.bitget import ProductType


class PositionMixin:
    async def get_all_positions(
        self: HttpClientProtocol,
        product_type: ProductType,
        margin_coin: str | None = None,
    ) -> dict[str, Any]:
        """
        Get all current positions for the given productType.

        Rate limit: 5 requests/sec/UID

        API Reference:
            GET /api/v2/mix/position/all-position

        Args:
            product_type: Product type.
            margin_coin: Capitalized margin coin (e.g., "USDT").

        Returns:
            dict[str, Any]: API response containing all open positions.
        """
        params: dict[str, str] = {"productType": product_type}
        if margin_coin:
            params["marginCoin"] = margin_coin
        return await self.get(
            "/api/v2/mix/position/all-position",
            params=params,
            auth=True,
        )

    async def get_historical_position(
        self: HttpClientProtocol,
        *,
        symbol: str | None = None,
        product_type: ProductType | None = None,
        id_less_than: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """
        Check position history (only data within 3 months).

        Rate limit: 20 times/s (uid).

        API Reference:
            GET /api/v2/mix/position/history-position

        Args:
            symbol: Trading pair (optional). If provided, productType is ignored.
            product_type: Product type (optional, default: USDT-FUTURES).
            id_less_than: Requests content before this ID (older data). Use endId from
                a previous response for pagination.
            start_time: Start time in milliseconds (Unix timestamp).
            end_time: End time in milliseconds (Unix timestamp). Max range is 3 months.
            limit: Number of results (default 20, max 100).

        Returns:
            dict[str, Any]: API response containing historical positions.
        """
        params: dict[str, Any] = {}
        if symbol is not None:
            params["symbol"] = symbol
        if product_type is not None:
            params["productType"] = product_type
        if id_less_than is not None:
            params["idLessThan"] = id_less_than
        if start_time is not None:
            params["startTime"] = str(start_time)
        if end_time is not None:
            params["endTime"] = str(end_time)
        if limit is not None:
            params["limit"] = str(limit)
        return await self.get(
            "/api/v2/mix/position/history-position",
            params=params,
            auth=True,
        )

    async def flash_close_position(
        self: HttpClientProtocol,
        product_type: ProductType,
        symbol: str | None = None,
        hold_side: Literal["long", "short"] | None = None,
    ) -> dict[str, Any]:
        """
        Flash Close Position: Close position at market price.

        Frequency limit: 1 time/1s (User ID)

        API Reference:
            POST /api/v2/mix/order/close-positions

        Args:
            product_type: Product type (required). E.g., "USDT-FUTURES"
            symbol: Trading pair (optional).
            hold_side: Position direction (optional).
                - One-way mode: leave blank (or None).
                - Hedge-mode:
                    * If blank, all positions will be closed.
                    * Set to "long" or "short" to
                    close positions of specified direction.

        Returns:
            dict[str, Any]: API response.
        """
        body: dict[str, Any] = {"productType": product_type}
        if symbol is not None:
            body["symbol"] = symbol
        if hold_side is not None:
            body["holdSide"] = hold_side

        return await self.post(
            "/api/v2/mix/order/close-positions",
            params=body,
            auth=True,
        )
