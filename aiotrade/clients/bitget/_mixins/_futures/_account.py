from typing import Any, Literal

from aiotrade._protocols import HttpClientProtocol
from aiotrade.types.bitget import ProductType


class AccountMixin:
    """Mixin for Bitget Futures Account API endpoints."""

    async def get_single_account(
        self: HttpClientProtocol,
        symbol: str,
        product_type: ProductType,
        margin_coin: str,
    ) -> dict[str, Any]:
        """
        Get account details with the given 'marginCoin' and 'productType'.

        Frequency limit: 10 times/1s (per uid).

        API Docs:
            GET /api/v2/mix/account/account

        Args:
            symbol: Trading pair.
            product_type: Product type
            margin_coin: Margin coin (e.g. "usdt", "btc", "usdc").

        Returns:
            dict: API JSON response.

        Example:
            await client.get_single_account(
                symbol="btcusdt",
                product_type="USDT-FUTURES",
                margin_coin="usdt"
            )
        """
        params = {
            "symbol": symbol,
            "productType": product_type,
            "marginCoin": margin_coin,
        }
        return await self.get(
            "/api/v2/mix/account/account",
            params=params,
            auth=True,
        )

    async def get_account_list(
        self: HttpClientProtocol,
        product_type: ProductType,
    ) -> dict[str, Any]:
        """
        Query all account information under a certain product type.

        Frequency limit: 10 times/1s (per uid).

        Description:
            Query all account information under a certain product type.

        API Docs:
            GET /api/v2/mix/account/accounts

        Args:
            product_type: Product type ("USDT-FUTURES", "COIN-FUTURES", "USDC-FUTURES").

        Returns:
            dict: API JSON response.


        """
        params = {
            "productType": product_type,
        }
        return await self.get(
            "/api/v2/mix/account/accounts",
            params=params,
            auth=True,
        )

    async def set_margin_mode(
        self: HttpClientProtocol,
        symbol: str,
        product_type: ProductType,
        margin_coin: str,
        margin_mode: Literal["isolated", "crossed"],
    ) -> dict[str, Any]:
        """
        Set margin mode (isolated or crossed) for a trading pair.

        This interface cannot be used when the users have an open position or an order.

        API Docs:
            POST /api/v2/mix/account/set-margin-mode

        Args:
            symbol: Trading pair (e.g. "btcusdt").
            product_type: Product type ("USDT-FUTURES", "COIN-FUTURES", "USDC-FUTURES").
            margin_coin: Margin coin, must be capitalized (e.g. "USDT", "BTC", "USDC").
            margin_mode: Margin mode - "isolated" or "crossed".

        Returns:
            dict: API JSON response.
        """
        body = {
            "symbol": symbol,
            "productType": product_type,
            "marginCoin": margin_coin,
            "marginMode": margin_mode,
        }
        return await self.post(
            "/api/v2/mix/account/set-margin-mode",
            params=body,
            auth=True,
        )

    async def set_position_mode(
        self: HttpClientProtocol,
        product_type: ProductType,
        pos_mode: Literal["one_way_mode", "hedge_mode"],
    ) -> dict[str, Any]:
        """
        Adjust the position mode between 'one way mode' and 'hedge mode'.

        The position mode can't be adjusted when there is an open position or order
        under the product type. When users hold positions or orders on any side of
        any trading pair in the specific product type, the request may fail.

        Frequency limit: 5 times/1s (uid).

        API Docs:
            POST /api/v2/mix/account/set-position-mode

        Args:
            product_type: Product type ("USDT-FUTURES", "COIN-FUTURES", "USDC-FUTURES").
            pos_mode: Position mode - "one_way_mode" or "hedge_mode".

        Returns:
            dict: API JSON response.
        """
        body = {
            "productType": product_type,
            "posMode": pos_mode,
        }
        return await self.post(
            "/api/v2/mix/account/set-position-mode",
            params=body,
            auth=True,
        )

    async def get_isolated_symbols(
        self: HttpClientProtocol,
        product_type: ProductType,
    ) -> dict[str, Any]:
        """
        Retrieve trading pairs with isolated margin mode under the account.

        Rate limits: 10 times/1s (uid).

        API Docs:
            GET /api/v2/mix/account/isolated-symbols

        Args:
            product_type: Product type ("USDT-FUTURES", "COIN-FUTURES", "USDC-FUTURES").

        Returns:
            dict: API JSON response.
        """
        params = {"productType": product_type}
        return await self.get(
            "/api/v2/mix/account/isolated-symbols",
            params=params,
            auth=True,
        )

    async def set_leverage(
        self: HttpClientProtocol,
        symbol: str,
        product_type: ProductType,
        margin_coin: str,
        *,
        leverage: str | None = None,
        long_leverage: str | None = None,
        short_leverage: str | None = None,
        hold_side: Literal["long", "short"] | None = None,
    ) -> dict[str, Any]:
        """
        Adjust the leverage on the given symbol and productType.

        Note: When adjusting leverage in cross margin mode, use leverage parameter
        instead of longLeverage/shortLeverage. In hedge-mode isolated margin, use
        longLeverage/shortLeverage. holdSide is required for hedge-mode when setting
        one direction at a time.

        Frequency limit: 5 times/1s (uid).

        API Docs:
            POST /api/v2/mix/account/set-leverage

        Args:
            symbol: Trading pair (e.g. "btcusdt").
            product_type: Product type ("USDT-FUTURES", "COIN-FUTURES", "USDC-FUTURES").
            margin_coin: Margin coin, must be capitalized (e.g. "USDT", "BTC", "USDC").
            leverage: Leverage ratio (cross-margin or one-way isolated).
            long_leverage: Long position leverage (hedge-mode isolated).
            short_leverage: Short position leverage (hedge-mode isolated).
            hold_side: Position direction - "long" or "short" (required for hedge-mode
                when setting one direction; not required when setting both).

        Returns:
            dict: API JSON response.
        """
        body: dict[str, Any] = {
            "symbol": symbol,
            "productType": product_type,
            "marginCoin": margin_coin,
        }
        if leverage is not None:
            body["leverage"] = leverage
        if long_leverage is not None:
            body["longLeverage"] = long_leverage
        if short_leverage is not None:
            body["shortLeverage"] = short_leverage
        if hold_side is not None:
            body["holdSide"] = hold_side
        return await self.post(
            "/api/v2/mix/account/set-leverage",
            params=body,
            auth=True,
        )
