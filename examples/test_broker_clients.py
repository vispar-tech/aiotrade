"""Test broker clients for OKX, Bitget, and Bybit using broker/OAuth mode."""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import cast

from dotenv import load_dotenv

from aiotrade import (
    BitgetClient,
    BybitClient,
    OkxClient,
)

load_dotenv()

logging.basicConfig(stream=sys.stdout, level="DEBUG")
logger = logging.getLogger(__name__)


def parse_broker_env(
    service_name: str, id_var: str, secret_var: str, redirect_var: str
) -> tuple[None, None, None] | tuple[str | None, str | None, str | None]:
    """Parse client_id, client_secret, redirect_uri from env for a broker/OAuth."""
    client_id = os.getenv(id_var)
    client_secret = os.getenv(secret_var)
    redirect_uri = os.getenv(redirect_var)
    # Print the fetched environment variables for debugging
    print(
        f"[DEBUG] {service_name} env vars:\n"
        f"  {id_var} = {client_id}\n"
        f"  {secret_var} = {client_secret}\n"
        f"  {redirect_var} = {redirect_uri}"
    )
    if not all([client_id, client_secret, redirect_uri]):
        print(
            f"❌ Missing {service_name} broker CLIENT_ID, "
            "CLIENT_SECRET, or REDIRECT_URI in .env"
        )
        return None, None, None
    return client_id, client_secret, redirect_uri


def parse_bitget_client_info() -> tuple[str | None, str | None]:
    """Parse the Bitget broker CLIENT_ID and CLIENT_USER_ID from .env."""
    bitget_client_id = os.getenv("BITGET_CLIENT_ID")
    bitget_client_user_id = os.getenv("BITGET_CLIENT_USER_ID")
    print(f"[DEBUG] BITGET_CLIENT_ID: {bitget_client_id}")
    print(f"[DEBUG] BITGET_CLIENT_USER_ID: {bitget_client_user_id}")
    if not bitget_client_id or not bitget_client_user_id:
        print("❌ Missing BITGET_CLIENT_ID or BITGET_CLIENT_USER_ID in .env")
        return None, None
    return bitget_client_id, bitget_client_user_id


async def test_okx_broker() -> None:
    print("=== OKX Broker ===")
    okx_client_id, okx_client_secret, okx_redirect_uri = parse_broker_env(
        "OKX", "OKX_CLIENT_ID", "OKX_CLIENT_SECRET", "OKX_REDIRECT_URI"
    )
    # Print values for debugging
    print(f"[DEBUG] OKX_CLIENT_ID: {okx_client_id}")
    print(f"[DEBUG] OKX_CLIENT_SECRET: {okx_client_secret}")
    print(f"[DEBUG] OKX_REDIRECT_URI: {okx_redirect_uri}")
    if not all([okx_client_id, okx_client_secret, okx_redirect_uri]):
        return

    # Both variables are guaranteed to be str here (already checked above)
    async with OkxClient.broker(
        cast(str, okx_client_id), cast(str, okx_client_secret)
    ) as client:
        # Use build_authorization_url and print the result
        print(
            client.build_authorization_url(
                redirect_uri=cast(str, okx_redirect_uri),
                state="test_state",
            )
        )
    print("✅ OKX Broker test complete.\n")


async def test_bitget_broker() -> None:
    print("=== Bitget Broker ===")
    bitget_rsa_public_key_path = os.getenv("BITGET_RSA_PUBLIC_KEY")
    bitget_rsa_private_key_path = os.getenv("BITGET_RSA_PRIVATE_KEY")
    bitget_redirect_uri = os.getenv("BITGET_REDIRECT_URI")
    bitget_client_id, bybit_client_user_id = parse_bitget_client_info()
    # Print values for debugging
    print(f"[DEBUG] BITGET_RSA_PUBLIC_KEY: {bitget_rsa_public_key_path}")
    print(f"[DEBUG] BITGET_RSA_PRIVATE_KEY: {bitget_rsa_private_key_path}")
    print(f"[DEBUG] BITGET_REDIRECT_URI: {bitget_redirect_uri}")
    if not all(
        [
            bitget_client_id,
            bybit_client_user_id,
            bitget_rsa_public_key_path,
            bitget_rsa_private_key_path,
            bitget_redirect_uri,
        ]
    ):
        print(
            "❌ Missing Bitget broker CLIENT_ID, RSA public/private key, "
            "or REDIRECT_URI in .env"
        )
        return

    try:
        bitget_rsa_public_key = Path(cast(str, bitget_rsa_public_key_path)).read_text()
        bitget_rsa_private_key = Path(
            cast(str, bitget_rsa_private_key_path)
        ).read_text()
    except Exception as e:
        print(f"❌ Error reading Bitget RSA key files: {e}")
        return

    async with BitgetClient.broker(
        cast(str, bitget_client_id),
        cast(str, bybit_client_user_id),
        bitget_rsa_public_key,
        bitget_rsa_private_key,
    ) as client:
        # Use build_authorization_url and print the result
        print(
            client.build_authorization_url(
                redirect_url=cast(str, bitget_redirect_uri),
                serial_no=cast(str, bybit_client_user_id),
            )
        )
    print("✅ Bitget Broker test complete.\n")


async def test_bybit_broker() -> None:
    print("=== Bybit Broker ===")
    bybit_client_id, bybit_client_secret, bybit_redirect_uri = parse_broker_env(
        "Bybit", "BYBIT_CLIENT_ID", "BYBIT_CLIENT_SECRET", "BYBIT_REDIRECT_URI"
    )
    print(f"[DEBUG] BYBIT_CLIENT_ID: {bybit_client_id}")
    print(f"[DEBUG] BYBIT_CLIENT_SECRET: {bybit_client_secret}")
    print(f"[DEBUG] BYBIT_REDIRECT_URI: {bybit_redirect_uri}")
    if not all([bybit_client_id, bybit_client_secret, bybit_redirect_uri]):
        return

    async with BybitClient.broker(
        cast(str, bybit_client_id), cast(str, bybit_client_secret)
    ) as client:
        # Use build_authorization_url and print the result
        print(
            client.build_authorization_url(
                redirect_uri=cast(str, bybit_redirect_uri),
                state="test_state",
            )
        )
    print("✅ Bybit Broker test complete.\n")


async def main() -> None:
    await test_okx_broker()
    await test_bitget_broker()
    await test_bybit_broker()


if __name__ == "__main__":
    asyncio.run(main())
