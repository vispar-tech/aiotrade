import urllib.parse
from types import TracebackType
from typing import Any, Self

import aiohttp


class BrokerClient:
    """
    KuCoin OAuth Broker Client for API Integration.

    Implements OAuth 2.0 authorization code flow for KuCoin broker fast API.
    https://www.kucoin.xxx documentation reference.
    """

    AUTHORIZATION_URL = "https://www.kucoin.xxx/oauth"
    TOKEN_URL = "https://www.kucoin.xxx/_oauth/access-token"  # noqa: S105
    OPENAPI_URL = "https://www.kucoin.xxx/_oauth/resource/ucenter/outer/api-key/add"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
    ) -> None:
        """
        Initialize the KuCoin OAuth Broker Client.

        Args:
            client_id: Broker's unique client_id (from KuCoin).
            client_secret: Broker's client secret (from KuCoin).
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self._session: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> Self:
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if self._session is not None:
            await self._session.close()
            self._session = None

    def build_authorization_url(
        self,
        *,
        redirect_uri: str,
        state: str,
        scope: str = "OAUTH_CREATE_API",
        response_type: str = "code",
    ) -> str:
        """
        Construct the KuCoin OAuth2.0 authorization URL.

        Args:
            redirect_uri: Redirect URL registered with KuCoin.
            state: CSRF protection - usually passed your user ID or random string.
            scope: Typically "OAUTH_CREATE_API".
            response_type: Typically "code".

        Returns:
            URL to redirect user for authorization.
        """
        # Build query string, but insert redirect_uri as-is (not encoded)
        params = {
            "response_type": response_type,
            "client_id": self.client_id,
            "scope": scope,
            "state": state,
        }
        # Manually assemble, so redirect_uri is NOT urlencoded
        query = urllib.parse.urlencode(params)
        # Append unencoded redirect_uri
        return f"{BrokerClient.AUTHORIZATION_URL}?{query}&redirect_uri={redirect_uri}"

    async def fetch_access_token(
        self,
        code: str,
        redirect_uri: str,
    ) -> dict[str, Any]:
        """
        Obtain the access token using the code received on the redirect URI.

        Args:
            code: Authorization code received from callback
            redirect_uri: Redirect URL corresponding to the OAuth flow
            client_secret: Broker's client_secret as provided by KuCoin

        Returns:
            Dict containing access_token, refresh_token, expires_in etc.

        Raises:
            aiohttp.ClientResponseError: If HTTP request fails.
            RuntimeError: If session is not initialized.
        """
        if self._session is None:
            raise RuntimeError(
                "BrokerClient session is not initialized. Use 'async with' context."
            )
        # All query string except redirect_uri, which we'll append unencoded
        params = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        # urlencode params, then add redirect_uri (not encoded)
        query = urllib.parse.urlencode(params)
        url = f"{BrokerClient.TOKEN_URL}?{query}&redirect_uri={redirect_uri}"

        async with self._session.get(url) as resp:
            resp.raise_for_status()
            return await resp.json()  # type: ignore[no-any-return]

    async def get_openapi_credentials(
        self,
        access_token: str,
    ) -> dict[str, Any]:
        """
        Obtain API credentials with the given access token.

        Args:
            access_token: Bearer token for the user

        Returns:
            Dict containing apiKey, secret, passphrase, brokerId, etc.

        Raises:
            aiohttp.ClientResponseError: If HTTP request fails.
            RuntimeError: If response error or session is not initialized.
        """
        if self._session is None:
            raise RuntimeError(
                "BrokerClient session is not initialized. Use 'async with' context."
            )
        headers = {
            "Authorization": f"bearer {access_token}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        # No body params needed
        async with self._session.post(
            BrokerClient.OPENAPI_URL, headers=headers
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
            if not data.get("success", False):
                raise RuntimeError(f"OpenAPI credential error: {data}")
            return data["data"]  # type: ignore[no-any-return]
