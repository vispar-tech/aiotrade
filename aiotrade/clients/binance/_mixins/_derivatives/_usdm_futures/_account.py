from typing import Any, Literal

from aiotrade._protocols import HttpClientProtocol


class AccountMixin:
    """Account endpoints."""

    async def get_account_balance(
        self: "HttpClientProtocol",
    ) -> dict[str, Any]:
        """
        Query account balance info.

        API Docs:
            GET /fapi/v3/balance

        Returns:
            dict: API JSON response containing account balance information.
        """
        return await self.get(
            "/fapi/v3/balance",
            auth=True,
        )

    async def get_account_info(
        self: "HttpClientProtocol",
    ) -> dict[str, Any]:
        """
        Get current account information.

        API Docs:
            GET /fapi/v3/account

        Returns:
            dict: API JSON response containing account information.
        """
        return await self.get(
            "/fapi/v3/account",
            auth=True,
        )

    async def get_account_config(
        self: "HttpClientProtocol",
    ) -> dict[str, Any]:
        """
        Query account configuration.

        API Docs:
            GET /fapi/v1/accountConfig

        Returns:
            dict: API JSON response containing account configuration.
        """
        return await self.get(
            "/fapi/v1/accountConfig",
            auth=True,
        )

    async def get_symbol_config(
        self: "HttpClientProtocol",
        symbol: str | None = None,
    ) -> dict[str, Any]:
        """
        Get current account symbol configuration.

        API Docs:
            GET /fapi/v1/symbolConfig

        Args:
            symbol: Trading pair symbol (optional).

        Returns:
            dict: API JSON response containing symbol configuration.
        """
        params: dict[str, Any] = {}
        if symbol is not None:
            params["symbol"] = symbol
        return await self.get(
            "/fapi/v1/symbolConfig",
            params=params,
            auth=True,
        )

    async def get_position_mode(
        self: "HttpClientProtocol",
    ) -> dict[str, Any]:
        """
        Get user's position mode (Hedge Mode or One-way Mode) on EVERY symbol.

        API Docs:
            GET /fapi/v1/positionSide/dual
        Returns:
            dict: API JSON response containing position mode information.
        """
        return await self.get(
            "/fapi/v1/positionSide/dual",
            auth=True,
        )

    async def get_multi_assets_mode(
        self: "HttpClientProtocol",
    ) -> dict[str, Any]:
        """
        Get user's Multi-Assets mode on Every symbol.

        API Docs:
            GET /fapi/v1/multiAssetsMargin


        Returns:
            dict: API JSON response containing Multi-Assets mode information.
        """
        return await self.get(
            "/fapi/v1/multiAssetsMargin",
            auth=True,
        )

    async def get_income_history(
        self: "HttpClientProtocol",
        symbol: str | None = None,
        income_type: (
            Literal[
                "TRANSFER",
                "WELCOME_BONUS",
                "REALIZED_PNL",
                "FUNDING_FEE",
                "COMMISSION",
                "INSURANCE_CLEAR",
                "REFERRAL_KICKBACK",
                "COMMISSION_REBATE",
                "API_REBATE",
                "CONTEST_REWARD",
                "CROSS_COLLATERAL_TRANSFER",
                "OPTIONS_PREMIUM_FEE",
                "OPTIONS_SETTLE_PROFIT",
                "INTERNAL_TRANSFER",
                "AUTO_EXCHANGE",
                "DELIVERED_SETTELMENT",
                "COIN_SWAP_DEPOSIT",
                "COIN_SWAP_WITHDRAW",
                "POSITION_LIMIT_INCREASE_FEE",
                "STRATEGY_UMFUTURES_TRANSFER",
                "FEE_RETURN",
                "BFUSD_REWARD",
            ]
            | None
        ) = None,
        start_time: int | None = None,
        end_time: int | None = None,
        page: int | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """
        Query income history.

        API Docs:
            GET /fapi/v1/income

        Args:
            symbol: Trading pair symbol (optional).
            income_type: Income type (e.g., "TRANSFER", "REALIZED_PNL", etc.)
            start_time: Start time in milliseconds (optional).
            end_time: End time in milliseconds (optional).
            page: Page number (optional).
            limit: Number of records to retrieve (default 100, max 1000) (optional).

        Returns:
            dict: API JSON response containing income history.
        """
        params: dict[str, Any] = {}
        if symbol is not None:
            params["symbol"] = symbol
        if income_type is not None:
            params["incomeType"] = income_type
        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit
        return await self.get(
            "/fapi/v1/income",
            params=params,
            auth=True,
        )
