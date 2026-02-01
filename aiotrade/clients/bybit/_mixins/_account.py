from typing import Any, Dict, Literal

from aiotrade._protocols import HttpClientProtocol
from aiotrade.types.bybit import (
    AccountType,
    BatchSetCollateralRequest,
    ContractTransLogType,
    MarginMode,
    UTATransLogType,
)


class AccountMixin:
    """Mixin for account endpoints."""

    async def get_wallet_balance(
        self: HttpClientProtocol,
        account_type: AccountType = "UNIFIED",
        coin: str | None = None,
    ) -> Dict[str, Any]:
        """
        Get wallet balance.

        See:
            https://bybit-exchange.github.io/docs/v5/account/wallet-balance

        Args:
            account_type: Account type. Default is "UNIFIED".
            coin: Single coin or comma-separated list, e.g. "BTC,ETH,USDT".
                If omitted, returns all coins.

        Returns:
            Dict with wallet balance response.
        """
        params: dict[str, str] = {"accountType": account_type}
        if coin:
            params["coin"] = coin
        return await self.get(
            "/v5/account/wallet-balance",
            params=params,
            auth=True,
        )

    async def get_transferable_amount(
        self: HttpClientProtocol,
        coin_name: str,
    ) -> Dict[str, Any]:
        """
        Get transferable amount for coins in Unified Wallet.

        See:
            https://bybit-exchange.github.io/docs/v5/account/unified-trans-amnt

        Args:
            coin_name: Coin names
                (uppercase, comma-separated for multiple, e.g. "BTC,ETH,SOL").

        Returns:
            Dict with transferable amount response.
        """
        params = {"coinName": coin_name}
        return await self.get(
            "/v5/account/withdrawal",
            params=params,
            auth=True,
        )

    async def get_transaction_log(
        self: HttpClientProtocol,
        account_type: AccountType | None = None,
        category: Literal["spot", "linear", "option", "inverse"] | None = None,
        currency: str | None = None,
        base_coin: str | None = None,
        trans_type: UTATransLogType | ContractTransLogType | None = None,
        trans_sub_type: Literal["movePosition"] | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> Dict[str, Any]:
        """
        Get transaction log for Unified Trading Account.

        See:
            https://bybit-exchange.github.io/docs/v5/account/transaction-log

        Args:
            account_type: Account type, e.g. "UNIFIED".
            category: Product type. "spot", "linear", "option", or "inverse".
            currency: Currency, uppercase (e.g. "USDT").
            base_coin: Base coin, uppercase (e.g. "BTC" for BTCPERP).
            trans_type: Transaction log type (see API docs).
            trans_sub_type: Transaction subtype (e.g. "movePosition").
            start_time: Start timestamp in ms.
            end_time: End timestamp in ms.
            limit: Limit per page, [1, 50].
            cursor: Pagination cursor token from previous page.

        Returns:
            Dict with transaction log response.
        """
        params: Dict[str, Any] = {}
        if account_type is not None:
            params["accountType"] = account_type
        if category is not None:
            params["category"] = category
        if currency is not None:
            params["currency"] = currency
        if base_coin is not None:
            params["baseCoin"] = base_coin
        if trans_type is not None:
            params["type"] = trans_type
        if trans_sub_type is not None:
            params["transSubType"] = trans_sub_type
        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time
        if limit is not None:
            params["limit"] = limit
        if cursor is not None:
            params["cursor"] = cursor

        return await self.get(
            "/v5/account/transaction-log",
            params=params,
            auth=True,
        )

    async def get_account_info(
        self: HttpClientProtocol,
    ) -> Dict[str, Any]:
        """
        Get account info.

        See:
            https://bybit-exchange.github.io/docs/v5/account/account-info

        Returns:
            Dict with account info response.
        """
        return await self.get(
            "/v5/account/info",
            auth=True,
        )

    async def get_account_instruments_info(
        self: HttpClientProtocol,
        category: Literal["spot", "linear", "inverse"],
        symbol: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> Dict[str, Any]:
        """
        Get instrument specification of online trading pairs.

        See:
            https://bybit-exchange.github.io/docs/v5/account/instrument

        Args:
            category: Product type. "spot", "linear", "inverse".
            symbol: Symbol name, e.g. "BTCUSDT", uppercase.
            limit: Limit per page, [1, 200].
            cursor: Pagination cursor from response.

        Returns:
            Dict with instruments info response.
        """
        params: Dict[str, Any] = {"category": category}
        if symbol is not None:
            params["symbol"] = symbol
        if limit is not None:
            params["limit"] = limit
        if cursor is not None:
            params["cursor"] = cursor

        return await self.get(
            "/v5/account/instruments-info",
            params=params,
            auth=True,
        )

    async def manual_borrow(
        self: HttpClientProtocol,
        coin: str,
        amount: float,
    ) -> Dict[str, Any]:
        """
        Manually borrow funds.

        See:
            https://bybit-exchange.github.io/docs/v5/account/borrow

        Args:
            coin: Coin name to borrow (uppercase), e.g. "BTC".
            amount: Borrow amount (float).

        Returns:
            Dict with borrow operation response.
        """
        params = {
            "coin": coin,
            "amount": str(amount),
        }
        return await self.post(
            "/v5/account/borrow",
            params=params,
            auth=True,
        )

    async def manual_repay_without_asset_conversion(
        self: HttpClientProtocol,
        coin: str,
        amount: float | None = None,
    ) -> Dict[str, Any]:
        """
        Manually repay debt without asset conversion.

        See:
            https://bybit-exchange.github.io/docs/v5/account/no-convert-repay

        Args:
            coin: Coin name to repay (uppercase), e.g. "BTC".
            amount: Repay amount (float).  If not provided, repays in full.

        Returns:
            Dict with manual repay operation response.
        """
        params = {"coin": coin}
        if amount is not None:
            params["amount"] = str(amount)

        return await self.post(
            "/v5/account/no-convert-repay",
            params=params,
            auth=True,
        )

    async def manual_repay(
        self: HttpClientProtocol,
        coin: str | None = None,
        amount: float | None = None,
    ) -> Dict[str, Any]:
        """
        Manually repay debt.

        See:
            https://bybit-exchange.github.io/docs/v5/account/repay

        Args:
            coin: Coin name to repay (uppercase), e.g. "BTC".
                If not provided and amount is not provided, repays all liabilities.
            amount: Repay amount (float).
                If coin is not provided, amount must also not be provided.

        Returns:
            Dict with repay operation response.
        """
        params: dict[str, Any] = {}
        if coin is not None:
            params["coin"] = coin
            if amount is not None:
                params["amount"] = str(amount)
        elif amount is not None:
            raise ValueError("If coin is not passed, amount cannot be passed.")

        return await self.post(
            "/v5/account/repay",
            params=params,
            auth=True,
        )

    async def get_fee_rate(
        self: HttpClientProtocol,
        category: Literal["spot", "linear", "inverse", "option"],
        symbol: str | None = None,
        base_coin: str | None = None,
    ) -> Dict[str, Any]:
        """
        Get trading fee rate.

        See:
            https://bybit-exchange.github.io/docs/v5/account/fee-rate

        Args:
            category: Product type. "spot", "linear", "inverse", or "option".
            symbol: Symbol name, e.g. "BTCUSDT", uppercase.
                Only for spot, linear, inverse.
            base_coin: Base coin (uppercase), e.g. "BTC". Only for option.

        Returns:
            Dict with trading fee rate response.
        """
        params: dict[str, str] = {"category": category}
        if symbol is not None:
            params["symbol"] = symbol
        if base_coin is not None:
            params["baseCoin"] = base_coin

        return await self.get(
            "/v5/account/fee-rate",
            params=params,
            auth=True,
        )

    async def get_collateral_info(
        self: HttpClientProtocol,
        currency: str | None = None,
    ) -> Dict[str, Any]:
        """
        Get collateral information for the unified margin account.

        See:
            https://bybit-exchange.github.io/docs/v5/account/collateral-info

        Args:
            currency: Asset currency for collateral info, uppercase (e.g. "BTC").

        Returns:
            Dict with collateral info response.
        """
        params: dict[str, Any] = {}
        if currency is not None:
            params["currency"] = currency

        return await self.get(
            "/v5/account/collateral-info",
            params=params,
            auth=True,
        )

    async def get_dcp_info(self: HttpClientProtocol) -> Dict[str, Any]:
        """
        Query the DCP configuration of the account.

        See:
            https://bybit-exchange.github.io/docs/v5/account/dcp-info

        Returns:
            Dict with DCP configuration response.
        """
        return await self.get(
            "/v5/account/query-dcp-info",
            auth=True,
        )

    async def set_collateral_coin(
        self: HttpClientProtocol,
        coin: str,
        collateral_switch: bool,
    ) -> Dict[str, Any]:
        """
        Set if a coin is enabled/disabled as collateral in the Unified account.

        See:
            https://bybit-exchange.github.io/docs/v5/account/set-collateral

        Args:
            coin: Coin to set collateral status for (uppercase, e.g. "BTC").
                Cannot be "USDT" or "USDC".
            collateral_switch: True to enable, False to disable as collateral.

        Returns:
            Dict with set collateral coin response.
        """
        params = {
            "coin": coin,
            "collateralSwitch": "ON" if collateral_switch else "OFF",
        }
        return await self.post(
            "/v5/account/set-collateral-switch",
            params=params,
            auth=True,
        )

    async def set_margin_mode(
        self: HttpClientProtocol,
        set_margin_mode: MarginMode,
    ) -> Dict[str, Any]:
        """
        Set margin mode.

        See:
            https://bybit-exchange.github.io/docs/v5/account/set-margin-mode

        Args:
            set_margin_mode: Margin mode value

        Returns:
            Dict with set margin mode response.
        """
        params = {"setMarginMode": set_margin_mode}
        return await self.post(
            "/v5/account/set-margin-mode",
            params=params,
            auth=True,
        )

    async def set_spot_hedging(
        self: HttpClientProtocol,
        enable: bool,
    ) -> Dict[str, Any]:
        """
        Turn on or off Spot Hedging feature for Portfolio margin.

        See:
            https://bybit-exchange.github.io/docs/v5/account/set-spot-hedge

        Args:
            enable: True to turn ON spot hedging, False to turn OFF.

        Returns:
            Dict with spot hedging response.
        """
        params = {"setHedgingMode": "ON" if enable else "OFF"}
        return await self.post(
            "/v5/account/set-hedging-mode",
            params=params,
            auth=True,
        )

    async def get_borrow_history(
        self: HttpClientProtocol,
        currency: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int | None = None,
        cursor: str | None = None,
    ) -> Dict[str, Any]:
        """
        Get interest borrow history.

        See:
            https://bybit-exchange.github.io/docs/v5/account/borrow-history

        Args:
            currency: Currency code (uppercase, e.g. "USDT").
            start_time: Start timestamp in ms.
            end_time: End timestamp in ms.
            limit: Records per page [1, 50].
            cursor: Pagination cursor.

        Returns:
            Dict with interest borrow history response.
        """
        params: dict[str, Any] = {}
        if currency is not None:
            params["currency"] = currency
        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time
        if limit is not None:
            params["limit"] = limit
        if cursor is not None:
            params["cursor"] = cursor

        return await self.get(
            "/v5/account/borrow-history",
            params=params,
            auth=True,
        )

    async def batch_set_collateral_coin(
        self: "HttpClientProtocol",
        request: list[BatchSetCollateralRequest],
    ) -> dict[str, Any]:
        """
        Batch set collateral coin.

        See:
            https://bybit-exchange.github.io/docs/v5/account/set-collateral

        Args:
            request: List of dicts, each with:
                - coin: Coin name (uppercase, can't be USDT or USDC)
                - collateralSwitch: True for ON, False for OFF

        Returns:
            Dict with batch set collateral coin response.
        """
        converted_request = [
            {
                "coin": item["coin"],
                "collateralSwitch": "ON" if item["collateralSwitch"] else "OFF",
            }
            for item in request
        ]
        params = {"request": converted_request}
        return await self.post(
            "/v5/account/set-collateral-switch-batch",
            params=params,
            auth=True,
        )

    async def get_coin_greeks(
        self: HttpClientProtocol, base_coin: str | None = None
    ) -> Dict[str, Any]:
        """
        Get current account Greeks information.

        See:
            https://bybit-exchange.github.io/docs/v5/account/coin-greeks

        Args:
            base_coin: Base coin (uppercase, e.g. "BTC").

        Returns:
            Dict with coin greeks response.
        """
        params: dict[str, str] = {}
        if base_coin is not None:
            params["baseCoin"] = base_coin
        return await self.get(
            "/v5/asset/coin-greeks",
            params=params,
            auth=True,
        )

    async def get_mmp_state(self: HttpClientProtocol, base_coin: str) -> Dict[str, Any]:
        """
        Get MMP (Market Maker Protection) state.

        See:
            https://bybit-exchange.github.io/docs/v5/account/get-mmp-state

        Args:
            base_coin: Base coin (uppercase, e.g. "BTC").

        Returns:
            Dict with MMP state response.
        """
        params = {"baseCoin": base_coin}
        return await self.get(
            "/v5/account/mmp-state",
            params=params,
            auth=True,
        )

    async def reset_mmp(self: HttpClientProtocol, base_coin: str) -> Dict[str, Any]:
        """
        Reset Market Maker Protection (MMP) for base coin.

        See:
            https://bybit-exchange.github.io/docs/v5/account/reset-mmp

        Args:
            base_coin: Base coin (uppercase, e.g. "BTC").

        Returns:
            Dict with MMP reset response.
        """
        params = {"baseCoin": base_coin}
        return await self.post(
            "/v5/account/mmp-reset",
            params=params,
            auth=True,
        )

    async def set_mmp(
        self: HttpClientProtocol,
        base_coin: str,
        window: str,
        frozen_period: str,
        qty_limit: str,
        delta_limit: str,
    ) -> Dict[str, Any]:
        """
        Set Market Maker Protection (MMP) parameters.

        See:
            https://bybit-exchange.github.io/docs/v5/account/set-mmp

        Args:
            base_coin: Base coin (uppercase, e.g. "BTC").
            window: Window in ms (as string).
            frozen_period: Frozen period in ms (as string). "0" means trade
                stays frozen until manual reset.
            qty_limit: Trade quantity limit, positive, string.
            delta_limit: Delta limit, positive, string.

        Returns:
            Dict with set MMP response.
        """
        params = {
            "baseCoin": base_coin,
            "window": window,
            "frozenPeriod": frozen_period,
            "qtyLimit": qty_limit,
            "deltaLimit": delta_limit,
        }
        return await self.post(
            "/v5/account/mmp-modify",
            params=params,
            auth=True,
        )

    async def get_smp_group_id(self: HttpClientProtocol) -> Dict[str, Any]:
        """
        Get SMP (Self Match Prevention) group ID.

        See:
            https://bybit-exchange.github.io/docs/v5/account/smp-group

        Returns:
            Dict with SMP group ID response.
        """
        return await self.get(
            "/v5/account/smp-group",
            auth=True,
        )

    async def get_trade_behaviour_setting(self: HttpClientProtocol) -> Dict[str, Any]:
        """
        Get trade behaviour setting (limit price behaviour for spot and futures).

        See:
            https://bybit-exchange.github.io/docs/v5/account/get-user-setting-config

        Returns:
            Dict with trade behaviour setting response.
        """
        return await self.get(
            "/v5/account/user-setting-config",
            auth=True,
        )

    async def set_limit_price_behaviour(
        self: HttpClientProtocol,
        category: Literal["linear", "inverse", "spot"],
        modify_enable: bool,
    ) -> Dict[str, Any]:
        """
        Set limit price behaviour for spot or futures.

        See:
            https://bybit-exchange.github.io/docs/v5/account/set-price-limit

        Args:
            category: Market type, one of "linear", "inverse", "spot".
            modify_enable: If True, order price may be modified to allowed boundary.
                If False, order will be rejected if exceeds boundary.

        Returns:
            Dict with set limit price behaviour response.
        """
        params = {
            "category": category,
            "modifyEnable": modify_enable,
        }
        return await self.post(
            "/v5/account/set-limit-px-action",
            params=params,
            auth=True,
        )

    async def repay_liability(
        self: HttpClientProtocol, coin: str | None = None
    ) -> Dict[str, Any]:
        """
        Repay liability for Unified account.

        See:
            https://bybit-exchange.github.io/docs/v5/account/quick-repayment

        Args:
            coin: Coin with liability, uppercase (optional).
                If not provided, repays all coins with liabilities.

        Returns:
            Dict with repay liability response.
        """
        params: dict[str, str] = {}
        if coin is not None:
            params["coin"] = coin
        return await self.post(
            "/v5/account/quick-repayment",
            params=params,
            auth=True,
        )

    async def upgrade_to_unified_account_pro(
        self: HttpClientProtocol,
    ) -> Dict[str, Any]:
        """
        Upgrade current account to Unified Account Pro (UTA2.0 Pro).

        See:
            https://bybit-exchange.github.io/docs/v5/account/upgrade-unified-account

        Returns:
            Dict with upgrade to Unified Account Pro response.
        """
        return await self.post(
            "/v5/account/upgrade-to-uta",
            params={},
            auth=True,
        )
