from typing import Any, Dict

from aiotrade._protocols import HttpClientProtocol
from aiotrade.types.bybit import AccountType, MarginMode


class AccountMixin:
    """Mixin for account endpoints."""

    async def get_wallet_balance(
        self: HttpClientProtocol,
        account_type: AccountType = "UNIFIED",
        coin: str | None = None,
    ) -> Dict[str, Any]:
        """
        Get wallet balance from Bybit API.

        See:
            https://bybit-exchange.github.io/docs/v5/account/wallet-balance

        Args:
            account_type: Account type ("UNIFIED", "CONTRACT", "SPOT",
                "FUND", "OPTION", "INVESTMENT"). Default is "UNIFIED".
            coin: Optional. Single coin or comma-separated list
                (e.g. "BTC,ETH,USDT"). If omitted, returns all coins.

        Returns:
            Dict with wallet balance response as received from Bybit API.

        Raises:
            Any exception raised by the underlying HTTP request.
        """
        params: Dict[str, Any] = {"accountType": account_type}
        if coin:
            params["coin"] = coin
        return await self.get(
            "/v5/account/wallet-balance",
            params=params,
            auth=True,
        )

    async def get_transferable_amount(self: HttpClientProtocol) -> Dict[str, Any]:
        """Get transferable amount (Unified)."""
        raise NotImplementedError

    async def get_transaction_log(self: HttpClientProtocol) -> Dict[str, Any]:
        """Get transaction log (UTA)."""
        raise NotImplementedError

    async def get_account_info(
        self: HttpClientProtocol,
    ) -> Dict[str, Any]:
        """
        Get account info from Bybit API.

        See:
            https://bybit-exchange.github.io/docs/v5/account/account-info

        Returns:
            Dict with account info response as received from Bybit API.

        Raises:
            Any exception raised by the underlying HTTP request.
        """
        return await self.get(
            "/v5/account/info",
            auth=True,
        )

    async def get_account_instruments_info(self: HttpClientProtocol) -> Dict[str, Any]:
        """Get account instruments info."""
        raise NotImplementedError

    async def manual_borrow(self: HttpClientProtocol) -> Dict[str, Any]:
        """Manual borrow."""
        raise NotImplementedError

    async def manual_repay_without_asset_conversion(
        self: HttpClientProtocol,
    ) -> Dict[str, Any]:
        """Manual repay without asset conversion."""
        raise NotImplementedError

    async def manual_repay(self: HttpClientProtocol) -> Dict[str, Any]:
        """Manual repay."""
        raise NotImplementedError

    async def get_fee_rate(self: HttpClientProtocol) -> Dict[str, Any]:
        """Get fee rate."""
        raise NotImplementedError

    async def get_collateral_info(self: HttpClientProtocol) -> Dict[str, Any]:
        """Get collateral info."""
        raise NotImplementedError

    async def get_dcp_info(self: HttpClientProtocol) -> Dict[str, Any]:
        """Get DCP info."""
        raise NotImplementedError

    async def set_collateral_coin(self: HttpClientProtocol) -> Dict[str, Any]:
        """Set collateral coin."""
        raise NotImplementedError

    async def set_margin_mode(
        self: HttpClientProtocol,
        set_margin_mode: MarginMode,
    ) -> Dict[str, Any]:
        """
        Set margin mode from Bybit API.

        See:
            https://bybit-exchange.github.io/docs/v5/account/set-margin-mode

        Args:
            set_margin_mode: Margin mode to set. One of:
                - "ISOLATED_MARGIN": Isolated margin mode
                - "REGULAR_MARGIN": Regular (cross) margin mode
                - "PORTFOLIO_MARGIN": Portfolio margin mode

        Returns:
            Dict with set margin mode response as received from Bybit API.

        Raises:
            Any exception raised by the underlying HTTP request.
        """
        params = {"setMarginMode": set_margin_mode}
        return await self.post(
            "/v5/account/set-margin-mode",
            params=params,
            auth=True,
        )

    async def set_spot_hedging(self: HttpClientProtocol) -> Dict[str, Any]:
        """Set spot hedging."""
        raise NotImplementedError

    async def get_borrow_history(self: HttpClientProtocol) -> Dict[str, Any]:
        """Get borrow history (2 years)."""
        raise NotImplementedError

    async def batch_set_collateral_coin(self: HttpClientProtocol) -> Dict[str, Any]:
        """Batch set collateral coin."""
        raise NotImplementedError

    async def get_coin_greeks(self: HttpClientProtocol) -> Dict[str, Any]:
        """Get coin greeks."""
        raise NotImplementedError

    async def get_mmp_state(self: HttpClientProtocol) -> Dict[str, Any]:
        """Get MMP state."""
        raise NotImplementedError

    async def reset_mmp(self: HttpClientProtocol) -> Dict[str, Any]:
        """Reset MMP."""
        raise NotImplementedError

    async def set_mmp(self: HttpClientProtocol) -> Dict[str, Any]:
        """Set MMP."""
        raise NotImplementedError

    async def get_smp_group_id(self: HttpClientProtocol) -> Dict[str, Any]:
        """Get SMP group ID."""
        raise NotImplementedError

    async def get_trade_behaviour_setting(self: HttpClientProtocol) -> Dict[str, Any]:
        """Get trade behaviour setting."""
        raise NotImplementedError

    async def set_limit_price_behaviour(self: HttpClientProtocol) -> Dict[str, Any]:
        """Set limit price behaviour."""
        raise NotImplementedError

    async def repay_liability(self: HttpClientProtocol) -> Dict[str, Any]:
        """Repay liability."""
        raise NotImplementedError

    async def upgrade_to_unified_account_pro(
        self: HttpClientProtocol,
    ) -> Dict[str, Any]:
        """Upgrade to unified account pro."""
        raise NotImplementedError
