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

    async def get_account_uid(
        self: HttpClientProtocol,
    ) -> Dict[str, Any]:
        """
        Query the Account UID.

        GET /openApi/account/v1/uid

        https://bingx-api.github.io/docs-v3/#/en/Account%20and%20Wallet/Sub-account%20Management/Query%20Account%20UID

        Returns:
            Dict[str, Any]: Response containing the account UID and related info.

        Example response:
            {
                "code": 0,
                "timestamp": 1702558965648,
                "data": {
                    "uid": 16844999
                }
            }
        """
        return await self.get("/openApi/account/v1/uid", auth=True)
