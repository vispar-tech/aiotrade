import urllib.parse
from types import TracebackType
from typing import Any, Self

import aiohttp


class BrokerClient:
    """
    OKX OAuth Broker Client for API Integration.

    Handles OAuth flow:
    1. Construct authorization URL for redirecting user.
    2. Parse callback 'code' (from redirect_uri).
    3. Exchange code for access_token (and refresh_token).
    4. Use access_token to fetch API credentials.

    NOTE:
        Never expose client_secret or api_secret publicly.
    """

    AUTHORIZATION_URL = "https://www.okx.com/account/oauth"
    TOKEN_URL = "https://www.okx.com/api/v5/users/oauth/token"  # noqa: S105
    OPENAPI_URL = "https://www.okx.com/api/v5/users/oauth/apikey"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        channel_id: str | None = None,
    ) -> None:
        """
        Initialize the OKX OAuth Broker Client.

        Args:
            client_id: OKX app client ID.
            client_secret: OKX app client secret.
            channel_id: Optional channel ID for partner integrations.
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.channel_id = channel_id
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
        channel_id: str | None = None,
        scope: str = "read_only,trade",
        response_type: str = "code",
        access_type: str = "offline",
    ) -> str:
        """
        Construct the OKX OAuth2.0 authorization URL.

        Args:
            client_id: Your OKX APP client ID.
            redirect_uri: The redirect URI set in your OKX app.
            state: A random string for CSRF protection.
            channel_id: Channel ID for integration, if applicable.
            scope: Scope for OAuth, default 'read_only,trade'.
            response_type: Typically 'code'.
            access_type: Typically 'offline' (for refresh_token).

        Returns:
            URL to redirect user for authorization.
        """
        params = {
            "client_id": self.client_id,
            "response_type": response_type,
            "access_type": access_type,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "state": state,
        }
        if channel_id:
            params["channelId"] = channel_id
        return f"{BrokerClient.AUTHORIZATION_URL}?" + urllib.parse.urlencode(
            params, quote_via=urllib.parse.quote
        )

    async def fetch_access_token(
        self,
        code: str,
        grant_type: str = "authorization_code",
        code_verifier: str | None = None,
    ) -> dict[str, Any]:
        """
        Obtain the access token using the code received on the redirect URI.

        Args:
            code: Authorization code received from callback.
            redirect_uri: Redirect URI for verification.
            grant_type: Must be 'authorization_code'.
            channel_id: Channel ID for integration, if applicable.
            code_verifier: The code_verifier if PKCE OAuth was used (optional).

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
            "grant_type": grant_type,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
        }
        # Add optional parameters if provided
        if code_verifier:
            data["code_verifier"] = code_verifier

        async with self._session.post(
            BrokerClient.TOKEN_URL, headers=headers, data=data
        ) as resp:
            resp.raise_for_status()
            return await resp.json()  # type: ignore[no-any-return]

    async def get_api_keys(
        self,
        access_token: str,
        label: str,
        passphrase: str,
        perm: str = "read_only,trade",
        bind_app: bool = False,
    ) -> dict[str, Any]:
        """
        Create or retrieve an API key using the provided OAuth access token.

        Parameters:
            access_token (str): Bearer token received from `fetch_access_token()`.
            label (str): Name for the API key (must be fewer than 50 characters).
            passphrase (str): Passphrase to associate with the API key.
            perm (str, optional): API key permissions. Defaults to 'read_only,trade'.
            bind_app (bool, optional): If True, binds the key to app-based trading.
                Defaults to False.

        Returns:
            dict[str, Any]: JSON response containing API key
                information or error structure.
                The structure matches OKX OpenAPI documentation.

        Raises:
            aiohttp.ClientResponseError: If the HTTP request fails.
            RuntimeError: If the aiohttp session is
                not initialized or a server-side error occurs.
            ValueError: If the API key label is 50 characters or more.
        """
        if self._session is None:
            raise RuntimeError(
                "BrokerClient session is not initialized. Use 'async with' context."
            )
        if len(label) > 49:
            raise ValueError(
                "label (API key name) must be a string less than 50 characters"
            )

        headers = {
            "Authorization": f"Bearer {access_token}",
            "user-agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/143.0.0.0 Safari/537.36"
            ),
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "label": label,
            "passphrase": passphrase,
            "perm": perm,
        }
        if bind_app:
            payload["bindApp"] = bind_app

        async with self._session.post(
            BrokerClient.OPENAPI_URL, headers=headers, json=payload
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
            if data.get("code") not in ("0", 0):
                raise RuntimeError(f"OpenAPI credential error: {data}")
            return data  # type: ignore[no-any-return]
