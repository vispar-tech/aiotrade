import base64
import json
import time
import urllib.parse
from types import TracebackType
from typing import Any, Self

import aiohttp
from Crypto import Random
from Crypto.Cipher import PKCS1_v1_5
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15


class RSAUtils:
    """Utility class for performing RSA-related operations."""

    @staticmethod
    def encrypt_rsa(plaintext: str, public_key_str: str) -> str:
        public_key = RSAUtils.get_public_key(public_key_str)
        cipher = PKCS1_v1_5.new(public_key)
        encrypted_data = cipher.encrypt(plaintext.encode("utf-8"))
        return base64.b64encode(encrypted_data).decode("utf-8")

    @staticmethod
    def decrypt_rsa(encrypted_data: str, private_key_str: str) -> str:
        private_key = RSAUtils.get_private_key(private_key_str)
        cipher = PKCS1_v1_5.new(private_key)
        ciphertext = base64.b64decode(encrypted_data)
        sentinel = Random.new().read(15)
        decrypted = cipher.decrypt(ciphertext, sentinel)
        if decrypted == sentinel:
            raise ValueError("Failed to decrypt: incorrect padding or key")
        return decrypted.decode("utf-8")

    @staticmethod
    def get_public_key(key: str) -> RSA.RsaKey:
        """Decode PEM or Base64 public key string to RSA RsaKey."""
        try:
            key_bytes = key.encode() if "-----BEGIN" in key else base64.b64decode(key)
            return RSA.import_key(key_bytes)
        except Exception as exc:
            raise ValueError(f"Invalid public key format: {exc}") from exc

    @staticmethod
    def get_private_key(key: str) -> RSA.RsaKey:
        """Decode PEM or Base64 private key string to RSA RsaKey."""
        try:
            key_bytes = key.encode() if "-----BEGIN" in key else base64.b64decode(key)
            return RSA.import_key(key_bytes)
        except Exception as exc:
            raise ValueError(f"Invalid private key format: {exc}") from exc

    @staticmethod
    def sign(data: str, private_key_str: str) -> str:
        private_key = RSAUtils.get_private_key(private_key_str)
        hasher = SHA256.new(data.encode("utf-8"))
        signature = pkcs1_15.new(private_key).sign(hasher)
        return base64.b64encode(signature).decode("utf-8")

    @staticmethod
    def get_sign_data(params: dict[str, str]) -> str:
        """Sort params by key and return a concatenated string of key+value."""
        return "".join(f"{k}{params[k]}" for k in sorted(params.keys()))

    @staticmethod
    def encrypt_state(state: str, public_key_str: str) -> str:
        """Encrypt state string ('SUCCESS'/'FAIL') using the broker's public key."""
        return RSAUtils.encrypt_rsa(state, public_key_str)

    @staticmethod
    def decrypt_state(encrypted_state: str, private_key_str: str) -> str:
        """Decrypt state string using the broker's private key."""
        return RSAUtils.decrypt_rsa(encrypted_state, private_key_str)

    @staticmethod
    def encrypt_serial_no(serial_no: str, public_key_str: str) -> str:
        """
        Encrypt serialNo with broker public key for 'sign' param.

        Bitget should encrypt 'serialNo' with the broker's public key and
        pass in 'sign'.
        """
        return RSAUtils.encrypt_rsa(serial_no, public_key_str)

    @staticmethod
    def decrypt_sign(sign: str, private_key_str: str) -> str:
        """Decrypt Bitget 'sign' param (should yield the serialNo)."""
        return RSAUtils.decrypt_rsa(sign, private_key_str)


class BrokerClient:
    """
    Bitget OAuth Broker Client for API Integration.

    Handles Bitget API credential delivery/callback as well.
    """

    AUTHORIZATION_URL = "https://www.bitget.com/oauth/v2/authorize"

    def __init__(
        self,
        client_id: str,
        client_user_id: str,
        rsa_public_key: str | None = None,
        rsa_private_key: str | None = None,
    ) -> None:
        """
        Initialize the Bitget OAuth Broker Client.

        Args:
            client_id: Bitget app client ID.
            rsa_public_key: RSA public key for data encryption (optional).
            rsa_private_key: RSA private key for decryption/signing.
        """
        self.client_id = client_id
        self.client_user_id = client_user_id
        self.rsa_public_key = rsa_public_key
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
        redirect_url: str,
        serial_no: str,
        timestamp: int | None = None,
    ) -> str:
        """
        Construct the Bitget OAuth2.0 authorization URL.

        Steps:
            1. Prepare param dict: clientId, clientUserId, timestamp.
            2. Generate sign_data string using get_sign_data.
            3. Sign the string with rsa_private_key.
            4. Add sign and build the authorization URL.

        Returns:
            The complete OAuth2.0 redirect URL as a string.
        """
        if not self._rsa_private_key:
            raise ValueError(
                "rsa_private_key must be provided to sign authorization data."
            )

        if timestamp is None:
            timestamp = int(time.time() * 1000)

        # Prepare data to sign
        sign_map = {
            "timestamp": str(timestamp),
            "clientId": self.client_id,
            "clientUserId": self.client_user_id,
        }
        sign_data = RSAUtils.get_sign_data(sign_map)
        sign = RSAUtils.sign(sign_data, self._rsa_private_key)

        url_params = {
            "clientId": self.client_id,
            "clientUserId": self.client_user_id,
            "timestamp": str(timestamp),
            "redirectUrl": redirect_url,
            "serialNo": serial_no,
            "sign": sign,
        }

        return f"{self.AUTHORIZATION_URL}?" + urllib.parse.urlencode(url_params)

    def decode_api_keys(
        self,
        encrypted_json: str,
    ) -> tuple[dict[str, Any] | None, dict[str, Any]]:
        """
        Decode encrypted Bitget API key data.

        Args:
            encrypted_json: Base64-encoded string, encrypted with the broker's key.
                The string, when decrypted, is a JSON object with key information.

        Returns:
            result: dict with parsed API keys or None on error.
            response: dict for Bitget API callback response (code/msg/requestTime).
        """
        if not self._rsa_private_key:
            raise ValueError(
                "rsa_private_key must be provided to sign authorization data."
            )

        request_time = str(int(time.time() * 1000))

        try:
            decrypted_json = RSAUtils.decrypt_rsa(encrypted_json, self._rsa_private_key)
        except Exception as exc:
            return None, {
                "code": "90008",
                "msg": f"Data decrypt failed: {exc}",
                "requestTime": request_time,
            }

        try:
            api_creds = json.loads(decrypted_json)
        except Exception as exc:
            return None, {
                "code": "90009",
                "msg": f"Invalid API credentials JSON: {exc}",
                "requestTime": request_time,
            }

        return api_creds, {
            "code": "00000",
            "msg": "success",
            "requestTime": request_time,
        }

    def validate_bitget_redirect(
        self,
        sign: str,
        client_user_id: str,
        state: str,
        serial_no_expected: str,
        client_user_id_expected: str,
    ) -> tuple[bool, str]:
        """
        Validate Bitget redirect parameters.

        Args:
            sign: The "sign" parameter from Bitget of the callback URL (should be the
                encrypted serialNo).
            client_user_id: The "clientUserId" parameter from Bitget
                of the callback URL.
            state: The "state" parameter from Bitget of the callback URL
                (encrypted or not, usually 'SUCCESS' or 'FAIL' encrypted).
            serial_no_expected: The serialNo that was originally generated and sent to
                Bitget (should match decrypted 'sign').
            client_user_id_expected: The clientUserId value that the broker expects
                (should match client_user_id).

        Returns:
            (is_valid, reason)
            is_valid: bool indicating if the redirect parameters are valid
                and authorized.
            reason: If invalid, the string describes why; on success, "OK".
        """
        if not self._rsa_private_key:
            raise ValueError(
                "rsa_private_key must be provided to validate redirect data."
            )
        # 1. Decrypt and validate "sign" matches serialNo
        try:
            serial_no_from_sign = RSAUtils.decrypt_sign(sign, self._rsa_private_key)
        except Exception as e:
            return False, f"Failed to decrypt 'sign': {e}"
        if serial_no_from_sign != serial_no_expected:
            return False, ("Invalid sign: serialNo mismatch (unauthorized request)")

        # 2. Validate clientUserId
        if client_user_id != client_user_id_expected:
            return False, ("Invalid clientUserId: mismatch (unauthorized request)")

        # 3. Optionally: Decrypt 'state' and validate it is an expected value
        try:
            state_plain = RSAUtils.decrypt_state(state, self._rsa_private_key)
        except Exception:
            # If state is not encrypted or can't be decrypted, fallback to raw value
            state_plain = state
        if state_plain.upper() not in {"SUCCESS", "FAIL"}:
            return False, f"Invalid state value: {state_plain}"
        return True, "OK"

    @staticmethod
    def parse_bitget_redirect_params(query_params: dict[str, str]) -> dict[str, str]:
        """
        Extract and return Bitget redirect callback parameters.

        Args:
            query_params: dict from URL query string
                (e.g., request.args or urllib.parse.parse_qs)
        Returns:
            Dict with 'sign', 'clientUserId', 'state' keys and their string values.
        """
        return {
            "sign": query_params.get("sign", ""),
            "clientUserId": query_params.get("clientUserId", ""),
            "state": query_params.get("state", ""),
        }
