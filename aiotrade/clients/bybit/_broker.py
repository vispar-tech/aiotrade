import urllib.parse
from types import TracebackType
from typing import Any, Self

import aiohttp


class BrokerClient:
    """
    Bybit OAuth Broker Client for API Integration.

    Handles OAuth flow:
    1. Construct authorization URL for redirecting user.
    2. Parse callback 'code' (from redirect_uri).
    3. Exchange code for access_token (and refresh_token).
    4. Use access_token to fetch OpenAPI credentials.

    NOTE:
        Never expose client_secret or api_secret publicly.
    """

    AUTHORIZATION_URL = "https://www.bybit.com/en/oauth"
    TOKEN_URL = "https://api2.bybit.com/oauth/v1/public/access_token"  # noqa: S105
    OPENAPI_URL = "https://api2.bybit.com/oauth/v1/resource/restrict/openapi"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
    ) -> None:
        """
        Initialize the Bybit OAuth Broker Client.

        Args:
            client_id: Bybit app client ID.
            client_secret: Bybit app client secret.
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
        redirect_uri: str,
        state: str,
        scope: str = "openapi",
        response_type: str = "code",
    ) -> str:
        """
        Construct the Bybit OAuth2.0 authorization URL.

        Args:
            client_id: Your Bybit APP client ID.
            redirect_uri: The redirect URI set in your Bybit app.
            state: A random string for CSRF protection.
            scope: Scope for OAuth (default 'openapi').
            response_type: Typically 'code'.

        Returns:
            URL to redirect user for authorization.
        """
        params = {
            "client_id": self.client_id,
            "response_type": response_type,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "state": state,
        }
        return f"{BrokerClient.AUTHORIZATION_URL}?" + urllib.parse.urlencode(params)

    async def fetch_access_token(
        self,
        code: str,
    ) -> dict[str, Any]:
        """
        Obtain the access token using the code received on the redirect URI.

        Args:
            code: Authorization code received from callback

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

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "user-agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/143.0.0.0 Safari/537.36"
            ),
        }
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
        }
        async with self._session.post(
            BrokerClient.TOKEN_URL, headers=headers, data=data
        ) as resp:
            resp.raise_for_status()  # Raises aiohttp.ClientResponseError if not 2xx
            return await resp.json()  # type: ignore[no-any-return]

    async def get_openapi_credentials(
        self,
        access_token: str,
    ) -> dict[str, Any]:
        """
        Obtain OpenAPI api_key and api_secret using the access token.

        Args:
            access_token: Bearer token received from fetch_access_token

        Returns:
            Dict containing 'api_key' and 'api_secret'

        Raises:
            aiohttp.ClientResponseError: If HTTP request fails.
            RuntimeError: If server returns error or session is not initialized.
        """
        if self._session is None:
            raise RuntimeError(
                "BrokerClient session is not initialized. Use 'async with' context."
            )

        headers = {"Authorization": f"Bearer {access_token}"}
        async with self._session.get(BrokerClient.OPENAPI_URL, headers=headers) as resp:
            resp.raise_for_status()  # Raises aiohttp.ClientResponseError if not 2xx
            data = await resp.json()
            if data.get("ret_code", 1) != 0:
                raise RuntimeError(f"OpenAPI credential error: {data}")
            return data["result"]  # type: ignore[no-any-return]
