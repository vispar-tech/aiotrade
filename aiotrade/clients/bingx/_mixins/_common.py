from typing import Any, Dict

from aiotrade._protocols import HttpClientProtocol


class CommonMixin:
    async def get_server_time(self: HttpClientProtocol) -> Dict[str, Any]:
        """Get BingX server time.

        Returns:
            Server time response from BingX API.

        See:
            https://bingx-api.github.io/docs-v3/#/en/Quick%20Start/Basic%20Information
        """
        return await self.get("/openApi/swap/v2/server/time")
