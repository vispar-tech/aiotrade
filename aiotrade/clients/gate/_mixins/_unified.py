from typing import Any

from aiotrade._protocols import HttpClientProtocol
from aiotrade.types.gate import UnifiedModeSet


class UnifiedMixin:
    async def get_unified_account(
        self: HttpClientProtocol,
        currency: str | None = None,
        sub_uid: str | None = None,
    ) -> dict[str, Any]:
        """
        Get unified account information.

        The assets of each currency are adjusted by their coefficients,
        then converted to USD to calculate total asset and position value.

        Args:
            currency: Query by specified currency name.
            sub_uid: Sub account user ID.

        Returns:
            UnifiedAccount: Information about unified account.
        """
        params: dict[Any, Any] = {}
        if currency is not None:
            params["currency"] = currency
        if sub_uid is not None:
            params["sub_uid"] = sub_uid

        return await self.get("/unified/accounts", params=params, auth=True)

    async def get_unified_mode(
        self: HttpClientProtocol,
    ) -> dict[str, Any]:
        """
        Query mode of the unified account.

        Unified account mode options:
          - 'classic': Classic account mode
          - 'multi_currency': Cross-currency margin
          - 'portfolio': Portfolio margin
          - 'single_currency': Single-currency margin

        Returns:
            UnifiedModeSet: Current unified account mode and settings.
        """
        return await self.get("/unified/unified_mode", auth=True)

    async def set_unified_mode(
        self: HttpClientProtocol,
        params: UnifiedModeSet,
    ) -> dict[str, Any]:
        """
        Set unified account mode.

        Switch account mode by passing the corresponding "mode" parameter.
        Example:
            { "mode": "classic" }
            { "mode": "multi_currency", "settings": { "usdt_futures": true } }
            { "mode": "portfolio", "settings": { "spot_hedge": true } }
            { "mode": "single_currency" }

        Args:
            unified_mode_set (UnifiedModeSet): Parameters for mode switch.

        Returns:
            None
        """
        return await self.put(
            "/unified/unified_mode",
            params=params,
            auth=True,
        )

    async def get_user_leverage_currency_config(
        self: HttpClientProtocol,
        currency: str,
    ) -> dict[str, Any]:
        """
        Get maximum and minimum currency leverage that can be set.

        Args:
            currency: Currency to query.

        Returns:
            UnifiedLeverageConfig: Per-currency leverage config.
        """
        return await self.get(
            "/unified/leverage/user_currency_config",
            params={"currency": currency},
            auth=True,
        )

    async def get_user_leverage_currency_setting(
        self: HttpClientProtocol,
        currency: str | None = None,
    ) -> dict[str, Any]:
        """
        Get user currency leverage.

        If 'currency' is not specified, query all currencies.

        Args:
            currency: Currency to query.

        Returns:
            list[UnifiedLeverageSetting]: List of leverage currency settings.
        """
        params: dict[str, Any] = {}
        if currency is not None:
            params["currency"] = currency

        return await self.get(
            "/unified/leverage/user_currency_setting",
            params=params,
            auth=True,
        )

    async def set_user_leverage_currency_setting(
        self: HttpClientProtocol,
        currency: str,
        leverage: str,
    ) -> dict[str, Any]:
        """
        Set loan currency leverage.

        Args:
            currency (str): The currency to set the leverage for.
            leverage (str): The leverage value to set.

        Returns:
            The API response as a dictionary.
        """
        params = {
            "currency": currency,
            "leverage": leverage,
        }
        return await self.post(
            "/unified/leverage/user_currency_setting",
            params=params,
            auth=True,
        )
