"""Tests for Gate API authentication and wallet balance."""

import asyncio
import json
import os

from aiotrade import GateClient

# Set this to True to actually place a test order in the real API test
PLACE_ORDER = False


async def print_wallet_balance(client: GateClient) -> None:
    """Fetch and print Gate wallet available balance (futures/USDT margin wallet)."""
    print("\n📊 Fetching Gate wallet available balance...")
    try:
        balance = await client.get_futures_account("usdt")
        print(f"✅ Available USDT wallet balance: {balance}")
    except Exception as e:
        print(f"❌ Error retrieving wallet balance: {e}")


async def print_open_positions(client: GateClient) -> None:
    """Fetch and print Gate open positions summary."""
    print("\n📈 Fetching open positions...")
    try:
        response = await client.list_positions("usdt", holding=True)
        print("✅ Open positions retrieved successfully!")
        try:
            pretty_response = json.dumps(response, indent=2, ensure_ascii=False)
            print(f"Full response:\n{pretty_response}\n")
        except Exception:
            print(f"Full response:\n{response}\n")

        positions = response.get("result", {}).get("list", [])

        if not positions:
            print("No open positions found in response.")
            return

        print(f"Found {len(positions)} open positions")
        for pos in positions:
            symbol = pos.get("contract", "???")
            side = "long" if pos["size"] > 0 else "short"
            size = pos.get("size")
            if size == 0:
                continue
            entry_price = pos.get("entry_price")
            unrealized_pnl = pos.get("unrealised_pnl")
            margin_mode = pos.get("pos_margin_mode")
            print(
                f"   {symbol}: side={side}, size={size}, entry={entry_price}, "
                f"margin_mode={margin_mode}, unrealized_pnl={unrealized_pnl}"
            )
    except AttributeError:
        print("❌ UnifiedGateClient does not have a get_position_info method.")
    except Exception as e:
        print(f"❌ Error retrieving open positions: {e}")


async def test_gate_wallet_and_positions() -> None:
    """Test Gate wallet balance and open positions using environment variables."""
    api_key = os.getenv("GATE_API_KEY")
    api_secret = os.getenv("GATE_API_SECRET")

    if not api_key or not api_secret:
        print("❌ Missing GATE_API_KEY or GATE_API_SECRET environment variables.")
        print("Skipping real API test - this is expected in CI/test environments")
        return

    demo = os.getenv("GATE_DEMO", "false").lower() == "true"

    print("🔑 Creating Gate client...")
    print(f"   API Key: {api_key[:8]}...")
    print(f"   Demo: {demo}")

    # Spot client (not used directly, but show it's possible)
    client = GateClient(
        api_key=api_key,
        api_secret=api_secret,
        demo=demo,
    )

    await print_wallet_balance(client)
    await print_open_positions(client)

    await client.close()


if __name__ == "__main__":
    print("Real Gate API authentication test")
    print(
        "Note: This test makes real API calls and "
        "requires GATE_API_KEY/GATE_API_SECRET env vars"
    )
    asyncio.run(test_gate_wallet_and_positions())
