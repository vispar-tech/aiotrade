from typing import Any, Dict

from aiotrade._protocols import HttpClientProtocol


class SubMixin:
    """Sub-account related methods for BingX API client.

    This mixin provides methods for managing sub-accounts and their operations.
    """

    async def get_api_permissions(
        self: HttpClientProtocol,
    ) -> Dict[str, Any]:
        """Get API permission information.

        GET /openApi/v1/account/apiPermissions

        https://bingx-api.github.io/docs-v3/#/en/Account%20and%20Wallet/Sub-account%20Management/%20Query%20API%20KEY%20Permissions
        """
        return await self.get("/openApi/v1/account/apiPermissions", auth=True)
