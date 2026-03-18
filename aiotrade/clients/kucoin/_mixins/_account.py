from typing import Any

from aiotrade._protocols import HttpClientProtocol
from aiotrade.clients.kucoin._consts import base_url


class AccountMixin:
    async def get_api_key_info(self: HttpClientProtocol) -> dict[str, Any]:
        """
        Get current API key information.

        Endpoint: GET /api/v1/user/api-key

        Returns:
            dict[str, Any]: API key information.
        """
        return await self.get("/api/v1/user/api-key", auth=True)

    async def get_futures_account(
        self: HttpClientProtocol, currency: str = "USDT"
    ) -> dict[str, Any]:
        """
        Get Account - Futures.

        Endpoint: GET /api/v1/account-overview

        Args:
            currency (str, optional): Currency code. Default is 'XBT'.

        Returns:
            dict[str, Any]: Futures account overview information,
                including balances and risk info.

        Example response:
            {
                "code": "200000",
                "data": {
                    "accountEquity": 198.733127406,
                    "unrealisedPNL": 0,
                    "marginBalance": 198.733127406,
                    "positionMargin": 0,
                    "orderMargin": 0,
                    "frozenFunds": 0,
                    "availableBalance": 198.733127406,
                    "availableMargin": 198.733127406,
                    "currency": "USDT",
                    "riskRatio": 0,
                    "maxWithdrawAmount": 198.733127406
                }
            }
        """
        params: dict[str, str] = {"currency": currency}

        return await self.get(
            "/api/v1/account-overview",
            params=params,
            auth=True,
            base_url=base_url("futures"),
        )
