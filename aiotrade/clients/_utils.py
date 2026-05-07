import base64
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, overload

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.asymmetric.padding import MGF1, OAEP


def _float_to_str(val: float, use_exp: bool) -> str:
    if use_exp:
        return str(val)
    # Use repr to avoid rounding (almost full machine precision as str)
    s = repr(val)
    # Only switch to non-scientific if present, else leave as-is
    if "e" in s or "E" in s:
        # Convert to decimal with max double precision, avoid scientific
        # 17 digits are usually the max guaranteed precision for a double
        s = format(val, ".17f").rstrip("0").rstrip(".")
        if s == "":
            s = "0"
        elif "." in s and s[-1] == ".":
            s += "0"
    return s


@overload
def to_str_fields(
    d: Mapping[str, Any], fields: Iterable[str], use_exp: bool = False
) -> dict[str, Any]: ...
@overload
def to_str_fields(
    d: Sequence[Mapping[str, Any]], fields: Iterable[str], use_exp: bool = False
) -> list[dict[str, Any]]: ...


def to_str_fields(
    d: Mapping[str, Any] | Sequence[Mapping[str, Any]],
    fields: Iterable[str],
    use_exp: bool = False,
) -> dict[str, Any] | list[dict[str, Any]]:
    """
    Convert specified fields to string in a params.

    Args:
        d: The original dict, TypedDict, or sequence thereof (not mutated).
        fields: Iterable of field names to be converted.
        use_exp: If True, allow string conversion of floats to use
            scientific notation when needed.
            If False (default), force decimal string with no scientific notation.

    Returns:
        A new dict with specified fields converted to strings,
        or a list of such dicts if given a sequence.
    """
    str_fields = set(fields)

    def convert_dict(obj: Mapping[str, Any]) -> dict[str, Any]:
        res: dict[str, Any] = {}
        for k, v in obj.items():
            if isinstance(v, Mapping):
                res[k] = convert_dict(v)  # pyright: ignore[reportUnknownArgumentType]
            elif isinstance(v, Sequence) and not isinstance(v, (str, bytes)):
                # If value is a sequence of mappings, recursively remap each
                res[k] = [convert_dict(item) for item in v]  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
            if k in str_fields and isinstance(v, float):
                res[k] = _float_to_str(v, use_exp)
            elif k in str_fields and isinstance(v, int):
                res[k] = str(v)
            else:
                res[k] = v
        return res

    if isinstance(d, Mapping):
        return convert_dict(d)
    return [convert_dict(item) for item in d]


@overload
def remap(d: Mapping[str, Any], mapping: Mapping[str, str]) -> dict[str, Any]: ...
@overload
def remap(
    d: Sequence[Mapping[str, Any]], mapping: Mapping[str, str]
) -> list[dict[str, Any]]: ...


def remap(
    d: Mapping[str, Any] | Sequence[Mapping[str, Any]],
    mapping: Mapping[str, str],
) -> dict[str, Any] | list[dict[str, Any]]:
    """
    Recursively remap fields in dict(s) according to a mapping.

    For each {src: dst} in mapping, move value
    from src to dst in the dict if src exists.
    If a value is itself a mapping, recursively apply remap with the same mapping.

    Args:
        d: The original dict, TypedDict, or sequence thereof (not mutated).
        mapping: Mapping of source fields to target fields.

    Returns:
        A new dict with remapped keys,
        or a list of such dicts if given a sequence.
    """

    def remap_dict(obj: Mapping[str, Any]) -> dict[str, Any]:
        res: dict[str, Any] = {}
        # First pass: recursive descend into sub-mappings
        for k, v in obj.items():
            # Only recursively remap if v is a mapping (but not a string)
            if isinstance(v, Mapping):
                res[k] = remap_dict(v)  # pyright: ignore[reportUnknownArgumentType]
            elif isinstance(v, Sequence) and not isinstance(v, (str, bytes)):
                # If value is a sequence of mappings, recursively remap each
                res[k] = [remap_dict(item) for item in v]  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
            else:
                res[k] = v
        # Second pass: rename according to mapping
        for src, dst in mapping.items():
            if src in res:
                res[dst] = res.pop(src)
        return res

    if isinstance(d, Mapping):
        return remap_dict(d)
    return [remap_dict(item) for item in d]


def join_iterable_field(val: str | Iterable[str]) -> str:
    """
    Join an iterable values.

    Args:
        val: A string or any iterable of values.

    Returns:
        Comma-separated string of values, or the original
            string if a single string was provided.
    """
    if isinstance(val, str):
        return val
    return ",".join(str(v) for v in val)


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
