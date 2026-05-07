import hashlib
import hmac
import json
import secrets
import time
import urllib.parse
from types import TracebackType
from typing import Any, Self

import aiohttp

from aiotrade.clients._utils import RSAUtils


class BrokerClient:
    """
    Gate OAuth Broker Client for API Integration.

    Handles Gate API OAuth flow to obtain access token and exchange for API keys.
    """

    AUTHORIZATION_URL = "https://www.gate.com/{broker_name}/oauth/authorize"
    TOKEN_URL = "https://openplatform.gateapi.io/oauth/token"  # noqa: S105
    APIKEY_URL = "https://openplatform.gateapi.io/api/v1/fastapi/keys"

    def __init__(
        self,
        broker_name: str,
        client_id: str,
        client_secret: str,
        rsa_public_key: str | None = None,
        rsa_private_key: str | None = None,
    ) -> None:
        """
        Initialize the Gate OAuth Broker Client.

        Args:
            broker_name: Gate Broker Name
            client_id: Gate app client ID.
            client_secret: Gate app client secret ("api_secret" for signature HMAC).
            rsa_public_key: User's RSA public key for final API key encryption (PEM).
            rsa_private_key: User's RSA private key for decrypting key/secret (PEM).
        """
        self.broker_name = broker_name
        self.client_id = client_id
        self.client_secret = client_secret
        self._rsa_public_key = rsa_public_key
        self._rsa_private_key = rsa_private_key
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
        scope: str = "read_openid,read_account_status,create_apikey",
    ) -> str:
        """
        Construct Gate OAuth authorization URL.

        Args:
            redirect_uri: after-auth callback.
            state: recommended as a random/nonce to protect session.
            scope: permissions for user consent.

        Returns:
            Full URL to redirect end-user for Gate OAuth consent.
        """
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": scope,
            "state": state,
        }
        auth_url_with_broker = self.AUTHORIZATION_URL.format(
            broker_name=self.broker_name
        )
        return f"{auth_url_with_broker}?{urllib.parse.urlencode(params)}"

    async def fetch_access_token(
        self,
        code: str,
        redirect_uri: str,
    ) -> dict[str, Any]:
        r"""
        Obtain access token from Gate API.

        Args:
            code: Received from callback.
            redirect_uri: Must match that supplied in auth request.

        Returns:
            Token response (token_type, access_token, expires_in, etc).
        """
        body = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": self.client_id,
        }
        # Ensure serialization matches signature (compact style)
        body_str = json.dumps(body, separators=(",", ":"))

        # Gate expects timestamp in milliseconds.
        timestamp = str(int(time.time() * 1000))
        # Gate recommends an alphanumeric (a-zA-Z0-9), max 32 chars
        nonce = secrets.token_hex(16)[:32]
        signature = self._generate_signature(
            timestamp, nonce, body_str, self.client_secret
        )

        headers = {
            "Content-Type": "application/json",
            "X-GatePay-Certificate-ClientId": self.client_id,
            "X-GatePay-Timestamp": timestamp,
            "X-GatePay-Nonce": nonce,
            "X-GatePay-Signature": signature,
        }

        # aiohttp expects timeout as ClientTimeout, not a raw int
        timeout = aiohttp.ClientTimeout(total=15)
        if self._session is None:
            self._session = aiohttp.ClientSession()
        async with self._session.post(
            self.TOKEN_URL, headers=headers, data=body_str, timeout=timeout
        ) as resp:
            resp.raise_for_status()
            return await resp.json()  # type:ignore [no-any-return]

    async def fetch_api_keys(
        self,
        access_token: str,
        enable_spot: int = 2,
        enable_futures: int = 2,
        enable_wallet: int = 1,
        enable_subaccount: int = 0,
        *,
        decode: bool = False,
    ) -> dict[str, Any]:
        """
        Request Gate API to generate API credentials encrypted to user's public key.

        https://www.gate.io/docs/miniapp/manual/en/#_3-5-obtain-api-key

        Args:
            access_token: The Bearer token from /oauth/token.
            rsa_public_key: User's RSA public key in PEM (if not provided in class).
            enable_spot: 0=disable, 1=read_only, 2=write
            enable_futures: 0=disable, 1=read_only, 2=write
            enable_wallet: 1=read_only, 2=write
            enable_subaccount: 0=disable, 1=read_only, 2=write
            decode: If True, decode and decrypt API keys (requires private key at init)

        Returns:
            API response; on success, contains "status", "code", and "data".
        """
        pubkey = self._rsa_public_key
        if not pubkey:
            raise ValueError("User RSA public key is required to create keys.")

        payload = {
            "enable_spot": enable_spot,
            "enable_futures": enable_futures,
            "enable_wallet": enable_wallet,
            "enable_subaccount": enable_subaccount,
            "public_key": pubkey,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        }
        timeout = aiohttp.ClientTimeout(total=15)
        if self._session is None:
            self._session = aiohttp.ClientSession()

        async with self._session.post(
            self.APIKEY_URL, headers=headers, json=payload, timeout=timeout
        ) as resp:
            resp.raise_for_status()
            resp_data = await resp.json()
            if (
                decode
                and resp_data.get("status") == "SUCCESS"
                and resp_data.get("data")
            ):
                if not self._rsa_private_key:
                    resp_data["data_decode_error"] = (
                        "No RSA private key set on client for decoding."
                    )
                else:
                    try:
                        decrypted = self.decode_and_decrypt_key_data(resp_data["data"])
                        resp_data["data"] = decrypted
                    except Exception as exc:
                        resp_data["data_decode_error"] = (
                            f"Failed to decode/decrypt: {exc}"
                        )
            return resp_data  # type:ignore [no-any-return]

    def decode_and_decrypt_key_data(
        self,
        encrypted_b64: str,
    ) -> dict[str, str]:
        """
        Decode and decrypt the API key data returned by Gate (base64+RSA(PKCS1v15)).

        The RSA private key must be a 2048bit key in standard PEM format.
        Cipher Type: RSA, PKCS v1.5 padding.

        Args:
            encrypted_b64: Base64-encoded encrypted data.

        Returns:
            dict with keys "key" and "secret" on success.
        """
        if not self._rsa_private_key:
            raise ValueError("RSA private key is not set on client.")
        decrypted = RSAUtils.decrypt_rsa(encrypted_b64, self._rsa_private_key)
        try:
            key_info = json.loads(decrypted)
        except Exception as e:
            raise ValueError(
                f"Decoded key data could not be parsed as JSON: {e}"
            ) from e

        if (
            not isinstance(key_info, dict)
            or "key" not in key_info
            or "secret" not in key_info
        ):
            raise ValueError(
                f"Decoded data missing 'key' or 'secret': got {key_info!r}"
            )

        return key_info

    @staticmethod
    def _generate_signature(
        timestamp: str,
        nonce: str,
        body: str,
        secret_key: str,
    ) -> str:
        r"""
        Compute the Gate HMAC-SHA512 signature.

        - Signature = HMAC_SHA512(secretKey, "{timestamp}\n{nonce}\n{body}\n")
        - All parameters MUST be used as strings.
        - body: serialized JSON (compact, e.g. separators=(",", ":"))
        - Output is a lowercase hex digest string.

        Example:
            timestamp := "1685349858720"
            nonce := "12wsetc"
            body := "hello"
            secretKey := "12345"
            # Signature is: 095ea1328d53a0cb...

        Returns:
            Hex string signature.
        """
        payload = f"{timestamp}\n{nonce}\n{body}\n"
        mac = hmac.new(
            secret_key.encode("utf-8"), payload.encode("utf-8"), hashlib.sha512
        )
        return mac.hexdigest()
