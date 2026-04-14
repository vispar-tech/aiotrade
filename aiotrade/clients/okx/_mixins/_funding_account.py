from collections.abc import Iterable
from typing import Any

from aiotrade._protocols import HttpClientProtocol
from aiotrade.utils.formatters import join_iterable_field


class FundingAccountMixin:
    """Mixin for OKX funding account balance endpoint."""

    async def get_funding_balance(
        self: HttpClientProtocol,
        ccy: str | Iterable[str] | None = None,
    ) -> dict[str, Any]:
        """
        Get balance.

        Retrieve the funding account balances of all the assets and the amount
        that is available or on hold.

        Only asset information of a currency with a balance greater than 0 will
        be returned.

        Rate Limit: 6 requests per second
        Rate limit rule: User ID
        Permission: Read

        See:
            https://www.okx.com/docs-v5/en/#funding-account-rest-api-get-balance

        Args:
            ccy: Single currency or multiple currencies separated with a comma
                (e.g. "BTC" or "BTC,ETH" or ["BTC", "ETH"]). Optional.

        Returns:
            Dict with funding balance response.
        """
        params: dict[str, str] = {}
        if ccy:
            params["ccy"] = join_iterable_field(ccy)
        return await self.get(
            "/api/v5/asset/balances",
            params=params,
            auth=True,
        )
