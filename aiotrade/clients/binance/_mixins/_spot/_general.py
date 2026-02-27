from collections.abc import Sequence
from typing import Any, Literal

from aiotrade._protocols import HttpClientProtocol
from aiotrade.types.binance import SymbolPermissions


class GeneralMixin:
    """Spot General endpoints mixin."""

    async def get_exchange_info(
        self: HttpClientProtocol,
        symbol: str | None = None,
        symbols: Sequence[str] | None = None,
        permissions: (SymbolPermissions | Sequence[SymbolPermissions] | None) = None,
        show_permission_sets: bool | None = None,
        symbol_status: None | Literal["TRADING", "HALT", "BREAK"] = None,
    ) -> dict[str, Any]:
        """
        Get current exchange trading rules and symbol information.

        API Docs:
            GET /api/v3/exchangeInfo

        Weight: 20

        Args:
            symbol: Single symbol to query info for.
            symbols: List of symbols to query info for.
            permissions: String or list of permissions.
            show_permission_sets: Controls whether the content of
                the permissionSets field is populated. Defaults to True.
            symbol_status: Symbol tradingStatus filter.

        Notes:
            - If symbol(s) do not exist, an error will be thrown.
            - All parameters are optional, but some combinations are invalid.

        Returns:
            dict: API JSON response with exchange information.
        """
        params: dict[str, Any] = {}

        if symbol:
            params["symbol"] = symbol
        if symbols:
            params["symbols"] = symbols
        if permissions:
            params["permissions"] = permissions

        if show_permission_sets is not None:
            params["showPermissionSets"] = str(show_permission_sets).lower()
        if symbol_status:
            params["symbolStatus"] = symbol_status

        return await self.get(
            "/api/v3/exchangeInfo",
            params=params,
            auth=False,
        )
