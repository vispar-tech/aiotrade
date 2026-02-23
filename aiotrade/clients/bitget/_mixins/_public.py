from typing import Any, Literal

from aiotrade._protocols import HttpClientProtocol


class PublicMixin:
    """Public REST endpoints for Bitget."""

    async def get_server_time(self: HttpClientProtocol) -> dict[str, Any]:
        """
        Get server time from Bitget.

        Reference:
            https://www.bitget.com/api-doc/common/public/Get-Server-Time

        HTTP Request:
            GET /api/v2/public/time

        Returns:
            dict: Response with server time in milliseconds.
            Example:
                {
                    "code": "00000",
                    "msg": "success",
                    "requestTime": 1688008631614,
                    "data": {
                        "serverTime": "1688008631614"
                    }
                }
        """
        return await self.get(
            "/api/v2/public/time",
            auth=False,
        )

    async def get_trade_rate(
        self: HttpClientProtocol,
        symbol: str,
        business_type: Literal["mix", "spot", "margin"],
    ) -> dict[str, Any]:
        """
        Get Trade Rate (taker/maker fee rates) for a trading pair and business type.

        Frequency limit: 10 times/1s (UID)

        Reference:
            https://www.bitget.com/api-doc/common/public/Get-Trade-Rate

        HTTP Request:
            GET /api/v2/common/trade-rate

        Args:
            symbol: Trading pair name, e.g. "BTCUSDT".
            business_type: Business type. Allowed: "mix" (contract), "spot", "margin".

        Returns:
            dict: Response data with "makerFeeRate" and "takerFeeRate" fields.
            Example:
                {
                    "code": "00000",
                    "msg": "success",
                    "requestTime": 1683875302853,
                    "data": {
                        "makerFeeRate": "0.0002",
                        "takerFeeRate": "0.0006"
                    }
                }

        Raises:
            ExchangeResponseError: If the response indicates an error from Bitget.

        Example:
            await self.get_trade_rate("BTCUSDT", "mix")
        """
        params = {
            "symbol": symbol,
            "businessType": business_type,
        }
        return await self.get(
            "/api/v2/common/trade-rate",
            params=params,
            auth=True,
        )
