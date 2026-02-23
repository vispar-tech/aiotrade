"""Tests for BingX, Bybit, and OKX API spot and swap account/portfolio balances."""

import asyncio
import os
from decimal import Decimal

from aiotrade import BingxClient, BybitClient, OkxClient


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


async def print_okx_wallet_balances(client: OkxClient) -> None:
    """Fetch and print OKX wallet balances using get_balance."""
    print("\n🟢 Fetching OKX wallet balance...")
    try:
        # Get wallet balance for all coins
        result = await client.get_balance()

        assets: set[str] = set()
        for account in result.get("data", []):
            details = account.get("details", [])
            for detail in details:
                ccy = detail.get("ccy")
                if ccy:
                    assets.add(ccy)

        if assets:
            print(_tab(1) + "Asset".ljust(12) + "Wallet Balance")
            print(_tab(1) + "-" * 30)
        else:
            print(_tab(1) + "No assets found.")

        for asset in sorted(assets):
            wallet_balance = client.helpers.extract_wallet_balance(result, asset=asset)
            if wallet_balance is None:
                print(_tab(1) + f"{asset.ljust(12)}" + "No wallet balance found")
            else:
                print(
                    _tab(1) + f"{asset.ljust(12)}" + f"{_format_number(wallet_balance)}"
                )
    except Exception as e:
        print(_tab(1) + f"❌ Error retrieving OKX wallet balance: {e}")


def check_env(
    required_vars: list[str],
) -> tuple[bool, list[str]]:
    """Check presence of all given env vars.."""
    values: list[str] = []
    missing: list[str] = []
    for var in required_vars:
        val = os.getenv(var)
        if val is None or val == "":
            missing.append(var)
        else:
            values.append(val)
    if missing:
        return False, missing
    return True, values


async def test_get_balances() -> None:  # noqa: PLR0912, PLR0915
    """Test retrieving balances for BingX (spot/swap), Bybit, and OKX using env vars."""

    # --- BingX ---
    bx_ok, bx_vals = check_env(["BINGX_API_KEY", "BINGX_API_SECRET"])
    if bx_ok:
        bx_key, bx_secret = bx_vals
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
        missing = ", ".join(bx_vals)
        print(f"{_tab(1)}❌ Skipping BingX test. Missing env vars: {missing}")

    # --- Bybit ---
    bybit_real_ok, bybit_real_vals = check_env(["BYBIT_API_KEY", "BYBIT_API_SECRET"])
    bybit_demo_ok, bybit_demo_vals = check_env(
        ["BYBIT_DEMO_API_KEY", "BYBIT_DEMO_API_SECRET"]
    )

    got_real = bybit_real_ok
    got_demo = bybit_demo_ok

    if got_real or got_demo:
        # Real mode: demo=False, testnet=False
        if got_real:
            byb_real_key, byb_real_secret = bybit_real_vals
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
            print("\n" + "_" * 80)
            missing = ", ".join(bybit_real_vals)
            print(
                f"{_tab(1)}❌ Skipping Bybit real mode test. "
                f"Missing env vars: {missing}"
            )

        # Demo mode: demo=True, testnet=False
        if got_demo:
            byb_demo_key, byb_demo_secret = bybit_demo_vals
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
            print("\n" + "_" * 80)
            missing = ", ".join(bybit_demo_vals)
            print(
                f"{_tab(1)}❌ Skipping Bybit demo mode test. "
                f"Missing env vars: {missing}"
            )
    else:
        print("\n" + "_" * 80)
        print("\n==================== Bybit ====================")
        missing_combined: list[str | None] = []
        if not bybit_real_ok:
            missing_combined.extend(bybit_real_vals)
        if not bybit_demo_ok:
            missing_combined.extend(bybit_demo_vals)
        missing_combined_filtered = [m for m in missing_combined if m is not None]
        print(
            f"{_tab(1)}❌ Skipping Bybit test. "
            f"Missing env vars for real/demo: {', '.join(missing_combined_filtered)}"
        )

    # --- OKX ---
    okx_ok, okx_vals = check_env(
        ["OKX_API_KEY", "OKX_API_SECRET", "OKX_API_PASSPHRASE"]
    )
    if okx_ok:
        okx_key, okx_secret, okx_passphrase = okx_vals
        print("\n" + "_" * 80)
        print("\n==================== OKX ====================")
        print(f"🔑 Using OKX API Key: {okx_key[:8]}...")
        okx_client = OkxClient(
            api_key=okx_key,
            api_secret=okx_secret,
            passphrase=okx_passphrase,
            demo=True,
        )
        await print_okx_wallet_balances(okx_client)
        await okx_client.close()
    else:
        print("\n" + "_" * 80)
        print("\n==================== OKX ====================")
        missing = ", ".join(okx_vals)
        print(f"{_tab(1)}❌ Skipping OKX test. Missing env vars: {missing}")


if __name__ == "__main__":
    asyncio.run(test_get_balances())
