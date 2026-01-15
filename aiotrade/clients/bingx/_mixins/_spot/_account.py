from typing import Any, Dict, Optional

from aiotrade._protocols import HttpClientProtocol
from aiotrade.types.bingx import AccountType


class AccountMixin:
    """Mixin for spot account endpoints on BingX."""

    async def get_spot_account_assets(
        self: HttpClientProtocol,
    ) -> Dict[str, Any]:
        """
        Get spot account balances from BingX API.

        See:
            https://bingx-api.github.io/docs-v3/#/en/Spot/Account%20Endpoints/Query%20Assets

        Returns:
            Dict with spot account balances.
        """
        return await self.get("/openApi/spot/v1/account/balance", auth=True)

    async def get_account_asset_overview(
        self: HttpClientProtocol,
        account_type: Optional[AccountType] = None,
    ) -> Dict[str, Any]:
        """
        Get asset overview for all or specific BingX account types.

        See: https://bingx-api.github.io/docs-v3/#/en/Spot/Account%20Endpoints/Asset%20overview

        Args:
            account_type: (optional) See `AccountType`. If omitted, returns all assets.

        Returns:
            Response dictionary with asset overview.
        """
        params: Dict[str, Any] = {}
        if account_type is not None:
            params["accountType"] = account_type

        return await self.get(
            "/openApi/account/v1/allAccountBalance",
            params=params,
            auth=True,
        )
