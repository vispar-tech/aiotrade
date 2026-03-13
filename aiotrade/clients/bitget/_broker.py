import base64
import json
import time
import urllib.parse
from types import TracebackType
from typing import Any, Self

import aiohttp
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.asymmetric.padding import MGF1, OAEP


class RSAUtils:
    """Minimal RSA helper (cryptography primitives)."""

    @staticmethod
    def get_public_key(key: str) -> rsa.RSAPublicKey:
        try:
            pubkey = serialization.load_pem_public_key(key.encode("utf-8"))
            if not isinstance(pubkey, rsa.RSAPublicKey):
                raise ValueError("Not an RSA public key")
            return pubkey
        except Exception as exc:
            raise ValueError(f"Invalid public key: {exc}") from exc

    @staticmethod
    def get_private_key(key: str) -> rsa.RSAPrivateKey:
        try:
            privkey = serialization.load_pem_private_key(
                key.encode("utf-8"), password=None
            )
            if not isinstance(privkey, rsa.RSAPrivateKey):
                raise ValueError("Not an RSA private key")
            return privkey
        except Exception as exc:
            raise ValueError(f"Invalid private key: {exc}") from exc

    @staticmethod
    def sign(data: str, private_key_str: str) -> str:
        """Sign (RSA PKCS1v15 MD5), return base64."""
        priv_key = RSAUtils.get_private_key(private_key_str.strip())
        signature = priv_key.sign(
            data.encode("utf-8"),
            padding.PKCS1v15(),
            hashes.MD5(),  # noqa: S303
        )
        return base64.b64encode(signature).decode("utf-8")

    @staticmethod
    def encrypt_rsa(plaintext: str, public_key_str: str) -> str:
        pub_key = RSAUtils.get_public_key(public_key_str)
        encrypted = pub_key.encrypt(
            plaintext.encode("utf-8"),
            OAEP(
                mgf=MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        return base64.b64encode(encrypted).decode("utf-8")

    @staticmethod
    def decrypt_rsa(encrypted_b64: str, private_key_str: str) -> str:
        priv_key = RSAUtils.get_private_key(private_key_str.strip())
        ciphertext = base64.b64decode(encrypted_b64)
        try:
            decrypted = priv_key.decrypt(
                ciphertext,
                padding.PKCS1v15(),
            )
            return decrypted.decode("utf-8")
        except UnicodeDecodeError:
            return base64.b64encode(decrypted).decode("ascii")
        except Exception as e:
            raise ValueError("Decrypt error: bad key/data/padding") from e

    @staticmethod
    def get_sign_data(params: dict[str, str]) -> str:
        """Sort keys and concat key+value for signing."""
        return "".join(f"{k}{params[k]}" for k in sorted(params))

    @staticmethod
    def encrypt_state(state: str, public_key_str: str) -> str:
        """Encrypt state with public key (OAEP-SHA256)."""
        return RSAUtils.encrypt_rsa(state, public_key_str)

    @staticmethod
    def decrypt_state(encrypted_state: str, private_key_str: str) -> str:
        """Decrypt state with private key (OAEP-SHA256)."""
        return RSAUtils.decrypt_rsa(encrypted_state, private_key_str)

    @staticmethod
    def encrypt_serial_no(serial_no: str, public_key_str: str) -> str:
        """Encrypt serialNo for Bitget API (OAEP-SHA256)."""
        return RSAUtils.encrypt_rsa(serial_no, public_key_str)

    @staticmethod
    def decrypt_sign(sign: str, private_key_str: str) -> str:
        """Decrypt Bitget 'sign' with private key (OAEP-SHA256)."""
        return RSAUtils.decrypt_rsa(sign, private_key_str)


class BrokerClient:
    """
    Bitget OAuth Broker Client for API Integration.

    Handles Bitget API credential delivery/callback as well.
    """

    AUTHORIZATION_URL = "https://www.bitget.com/account/oauth"

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
            3. Sign the string with rsa_private_key (simple RSA).
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
            "clientId": str(self.client_id),
            "clientUserId": str(self.client_user_id),
        }
        sign_data = RSAUtils.get_sign_data(sign_map)
        sign = RSAUtils.sign(sign_data, self._rsa_private_key)

        url_params = {
            "clientId": self.client_id,
            "clientUserId": self.client_user_id,
            "timestamp": timestamp,
            "redirectUrl": redirect_url,
            "serialNo": serial_no,
            "sign": sign,
        }
        return f"{self.AUTHORIZATION_URL}?{urllib.parse.urlencode(url_params)}"

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
