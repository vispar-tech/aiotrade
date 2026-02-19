"""Tests for BingX and Bybit API spot and swap account/portfolio balances."""

import asyncio
import os
from decimal import Decimal

from aiotrade import BingxClient, BybitClient


def _format_number(val: float) -> str:
    d = Decimal(str(val))
    return format(d, "f").rstrip("0").rstrip(".") if "." in format(d, "f") else str(d)


def _tab(level: int) -> str:
    return "    " * level


async def print_bingx_spot_balances(client: BingxClient, *, demo: bool) -> None:
    """Fetch and print BingX spot account balances."""
    print(f"\n🔵 Fetching BingX spot account balances... (demo={demo})")
    try:
        result = await client.get_spot_account_assets()
        assets = [
            entry.get("asset") for entry in result.get("data", {}).get("balances", [])
        ]
        if assets:
            print(_tab(1) + "Asset".ljust(12) + "Wallet Balance")
            print(_tab(1) + "-" * 30)
        else:
            print(_tab(1) + "No assets found.")

        for asset in assets:
            wallet_balance = client.helpers.extract_spot_wallet_balance(
                result, asset=asset
            )
            if wallet_balance is None:
                print(_tab(1) + f"{asset.ljust(12)}" + "No wallet balance found")
            else:
                print(
                    _tab(1) + f"{asset.ljust(12)}" + f"{_format_number(wallet_balance)}"
                )

    except Exception as e:
        print(_tab(1) + f"❌ Error retrieving BingX spot account assets: {e}")


async def print_bingx_swap_balances(client: BingxClient, *, demo: bool) -> None:
    """Fetch and print BingX swap (derivatives) account balances."""
    print(f"\n🟣 Fetching BingX swap account balances... (demo={demo})")
    try:
        result = await client.get_swap_account_balance()
        assets = [entry.get("asset") for entry in result.get("data", [])]

        if assets:
            print(_tab(1) + "Asset".ljust(12) + "Swap Wallet Balance")
            print(_tab(1) + "-" * 33)
        else:
            print(_tab(1) + "No swap assets found.")

        for asset in assets:
            wallet_balance = client.helpers.extract_swap_wallet_balance(
                result, asset=asset
            )
            if wallet_balance is None:
                print(_tab(1) + f"{asset.ljust(12)}" + "No wallet balance found")
            else:
                print(
                    _tab(1) + f"{asset.ljust(12)}" + f"{_format_number(wallet_balance)}"
                )

    except Exception as e:
        print(_tab(1) + f"❌ Error retrieving BingX swap account balance: {e}")


async def print_bybit_balances(client: BybitClient) -> None:
    """Fetch and print Bybit wallet balance summary."""
    print("\n🟡 Fetching Bybit wallet balance...")
    try:
        result = await client.get_wallet_balance(account_type="UNIFIED")
        assets = [
            coin.get("coin")
            for account in (result.get("result", {}).get("list"))
            for coin in account.get("coin", [])
            if coin.get("coin") is not None
        ]
        if assets:
            print(_tab(1) + "Asset".ljust(12) + "Wallet Balance")
            print(_tab(1) + "-" * 30)
        else:
            print(_tab(1) + "No assets found.")

        for asset in assets:
            wallet_balance = client.helpers.extract_wallet_balance(result, asset=asset)
            if wallet_balance is None:
                print(_tab(1) + f"{asset.ljust(12)}" + "No wallet balance found")
            else:
                print(
                    _tab(1) + f"{asset.ljust(12)}" + f"{_format_number(wallet_balance)}"
                )

    except Exception as e:
        print(_tab(1) + f"❌ Error retrieving Bybit wallet balance: {e}")


async def test_get_balances() -> None:
    """Test retrieving balances for both BingX (spot/swap) and Bybit using env vars."""

    # --- BingX ---
    bx_key = os.getenv("BINGX_API_KEY")
    bx_secret = os.getenv("BINGX_API_SECRET")
    if bx_key and bx_secret:
        print(f"🔑 Using BingX API Key: {bx_key[:8]}... (Testing demo and real modes)")

        # Always test both demo=False and demo=True (same keys and secrets)
        for bx_demo in [False, True]:
            mode = "Demo" if bx_demo else "Real"
            print("\n" + "_" * 80)
            print(f"\n--- BingX {mode} Mode (SPOT) ---")
            client = BingxClient(api_key=bx_key, api_secret=bx_secret, demo=bx_demo)
            await print_bingx_spot_balances(client, demo=bx_demo)
            await client.close()

            print("\n" + "_" * 80)
            print(f"\n--- BingX {mode} Mode (SWAP) ---")
            client = BingxClient(api_key=bx_key, api_secret=bx_secret, demo=bx_demo)
            await print_bingx_swap_balances(client, demo=bx_demo)
            await client.close()
    else:
        print("\n" + "_" * 80)
        print("\n==================== BingX ====================")
        print(
            _tab(1) + "❌ Missing BINGX_API_KEY or BINGX_API_SECRET env vars. "
            "Skipping BingX test."
        )

    # --- Bybit ---
    byb_real_key = os.getenv("BYBIT_API_KEY")
    byb_real_secret = os.getenv("BYBIT_API_SECRET")
    byb_demo_key = os.getenv("BYBIT_DEMO_API_KEY")
    byb_demo_secret = os.getenv("BYBIT_DEMO_API_SECRET")

    real_keys_available = byb_real_key and byb_real_secret
    demo_keys_available = byb_demo_key and byb_demo_secret

    if real_keys_available or demo_keys_available:
        # Real mode: demo=False, testnet=False
        if byb_real_key and byb_real_secret:
            print("\n" + "_" * 80)
            print("\n--- Bybit Real Mode (demo=False, testnet=False) ---")
            print(f"🔑 Using Bybit Real API Key: {byb_real_key[:8]}...")
            bybit_real_client = BybitClient(
                api_key=byb_real_key,
                api_secret=byb_real_secret,
                demo=False,
                testnet=False,
            )
            await print_bybit_balances(bybit_real_client)
            await bybit_real_client.close()
        else:
            print(
                _tab(1) + "❌ Missing BYBIT_API_KEY or BYBIT_API_SECRET env vars for "
                "real Bybit account. Skipping Bybit real mode test."
            )

        # Demo mode: demo=True, testnet=False
        if byb_demo_key and byb_demo_secret:
            print("\n" + "_" * 80)
            print("\n--- Bybit Demo Mode (demo=True, testnet=False) ---")
            print(f"🔑 Using Bybit Demo API Key: {byb_demo_key[:8]}...")
            bybit_demo_client = BybitClient(
                api_key=byb_demo_key,
                api_secret=byb_demo_secret,
                demo=True,
                testnet=False,
            )
            await print_bybit_balances(bybit_demo_client)
            await bybit_demo_client.close()
        else:
            print(
                _tab(1)
                + "❌ Missing BYBIT_DEMO_API_KEY or BYBIT_DEMO_API_SECRET env vars for "
                "Bybit demo account. Skipping Bybit demo mode test."
            )
    else:
        print("\n" + "_" * 80)
        print("\n==================== Bybit ====================")
        print(
            _tab(1) + "❌ Missing BYBIT_API_KEY/BYBIT_API_SECRET and "
            "BYBIT_DEMO_API_KEY/BYBIT_DEMO_API_SECRET env vars. Skipping Bybit test."
        )


if __name__ == "__main__":
    print("\n" + "_" * 80)
    print("==== Get balances for BingX (spot/swap) and Bybit ====")
    print(
        "Note: These tests require BINGX_API_KEY/BINGX_API_SECRET and/or "
        "BYBIT_API_KEY/BYBIT_API_SECRET env vars set."
    )
    asyncio.run(test_get_balances())
