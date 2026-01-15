"""Tests for BingX API authentication and spot account assets."""

import asyncio
import os
from typing import Any, Dict

from aiotrade import BingxClient
from aiotrade.types.bingx import PlaceSwapOrderParams, TpSlStruct


async def print_spot_account_assets(client: BingxClient) -> Dict[str, Any] | None:
    """Fetch and print BingX spot account assets."""
    print("\n📊 Fetching BingX spot account assets...")
    try:
        result = await client.get_spot_account_assets()
        print("✅ Spot account assets retrieved successfully!")
        print(f"Full response:\n{result}\n")

        balances = result.get("data", {}).get("balances", [])

        if not balances:
            print("No asset balances found in response.")
            return result

        print(f"Found {len(balances)} asset balances:")
        for asset in balances[:5]:
            asset_name = asset.get("asset", "???")
            free = asset.get("free", "0")
            locked = asset.get("locked", "0")
            print(f"   {asset_name}: free={free}, locked={locked}")
        return result
    except Exception as e:
        print(f"❌ Error retrieving spot account assets: {e}")
        return None


async def print_server_time(client: BingxClient) -> None:
    """Fetch and print BingX server time."""
    print("\n⏰ Fetching BingX server time...")
    try:
        result = await client.get_server_time()
        print("✅ Server time retrieved successfully!")
        print(f"Server time response: {result}")
    except Exception as e:
        print(f"❌ Error retrieving server time: {e}")


async def test_bingx_spot_assets_and_time() -> None:
    """Test BingX spot account assets and server time using environment variables."""
    api_key = os.getenv("BINGX_API_KEY")
    api_secret = os.getenv("BINGX_API_SECRET")

    if not api_key or not api_secret:
        print("❌ Missing BINGX_API_KEY or BINGX_API_SECRET environment variables.")
        return

    demo = os.getenv("BINGX_DEMO", "false").lower() == "true"

    print("🔑 Creating BingX client...")
    print(f"   API Key: {api_key[:8]}...")
    print(f"   Demo: {demo}")

    client = BingxClient(
        api_key=api_key,
        api_secret=api_secret,
        demo=demo,
    )

    try:
        await print_spot_account_assets(client)
        await print_server_time(client)
        await client.place_swap_order(
            PlaceSwapOrderParams(
                symbol="BTC-USDT",
                side="BUY",
                position_side="BOTH",
                order_type="MARKET",
                quantity=0.005,
                take_profit=TpSlStruct(
                    order_type="TAKE_PROFIT_MARKET",
                    price=100_000,
                    stop_price=100_000,
                    working_type="MARK_PRICE",
                ),
            )
        )

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_bingx_spot_assets_and_time())
