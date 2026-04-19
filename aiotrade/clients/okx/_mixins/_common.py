from typing import Any

from aiotrade._protocols import HttpClientProtocol


class CommonMixin:
    async def get_server_time(self: HttpClientProtocol) -> dict[str, Any]:
        """Fetch OKX server time.

        Returns:
            Server time response from OKX API.

        See:
            https://www.okx.com/docs-v5/en/#public-data-rest-api-get-system-time
        """
        return await self.get("/api/v5/public/time")
