"""Tests for Bybit API authentication and wallet balance."""

import asyncio
import json
import os
from pprint import pprint
from typing import Any

from aiotrade import BybitClient
from aiotrade.types.bybit import PlaceOrderParams

# Set this to True to actually place a test order in the real API test
PLACE_ORDER = False


async def print_wallet_balance(client: BybitClient) -> None:
    """Fetch and print Bybit wallet balance summary."""
    print("\n📊 Fetching Bybit wallet balance...")
    try:
        result = await client.get_wallet_balance(account_type="UNIFIED", coin="USDT")
        print("✅ Wallet balance retrieved successfully!")
        try:
            pretty_resp = json.dumps(result, indent=2, ensure_ascii=False)
            print(f"Full response:\n{pretty_resp}\n")
        except Exception:
            print(f"Full response:\n{result}\n")

        accounts: list[dict[str, Any]] | None = result.get("result", {}).get(
            "list", None
        )
        if accounts is None:
            print(
                "⚠️ Warning: Unexpected accounts value -- expected a list but got:",
                type(accounts),
            )
            return

        if not accounts:
            print("No account types found in response.")
            return

        print(f"Found {len(accounts)} account types")
        for account in accounts[:3]:
            account_type = account.get("accountType", "Unknown")
            total_wallet_balance = account.get("totalWalletBalance", "0")
            print(f"   {account_type}: wallet = {total_wallet_balance}")

            coins: list[dict[str, Any]] | None = account.get("coin", None)
            if coins is None:
                print(
                    "      ⚠️ Warning: Unexpected coins value -- "
                    "expected a list but got:",
                    type(coins),
                )
                continue

            if not coins:
                print("      No coins found in response.")
            if coins:
                print("      Coins:")
                for coin in coins[:3]:
                    coin_name = coin.get("coin", "???")
                    coin_balance = coin.get("walletBalance", "0")
                    coin_equity = coin.get("equity", "0")
                    print(
                        f"         {coin_name}: wallet_balance={coin_balance}, "
                        f"equity={coin_equity}"
                    )

    except Exception as e:
        print(f"❌ Error retrieving wallet balance: {e}")


async def print_open_positions(client: BybitClient) -> None:
    """Fetch and print Bybit open positions summary."""
    print("\n📈 Fetching open positions...")
    try:
        resp = await client.get_position_info(
            category="linear", settle_coin="USDT", limit=200
        )
        print("✅ Open positions retrieved successfully!")
        try:
            pretty_resp = json.dumps(resp.get("result"), indent=2, ensure_ascii=False)
            print(f"Full positions response:\n{pretty_resp}\n")
        except Exception:
            print(f"Full positions response:\n{resp}\n")

        positions = resp.get("result", {}).get("list", None)
        if positions is None:
            print(
                "⚠️ Warning: No open positions found in the response "
                "(positions is None)."
            )
            return

        if len(positions) == 0:
            print("No open positions found in response.")
            return

        print(f"Found {len(positions)} open positions")
        for pos in positions[:3]:
            symbol = pos.get("symbol", "???")
            side = pos.get("side", "?")
            size = pos.get("size", pos.get("positionSize", "0"))
            entry_price = pos.get("avgEntryPrice", pos.get("entryPrice", "0"))
            unrealized_pnl = pos.get("unrealisedPnl", pos.get("unrealizedPnl", "0"))
            print(
                f"   {symbol}: side={side}, size={size}, entry={entry_price}, "
                f"unrealized_pnl={unrealized_pnl}"
            )
    except AttributeError:
        print("❌ BybitClient does not have a get_position_info method.")
    except Exception as e:
        print(f"❌ Error retrieving open positions: {e}")


async def test_bybit_wallet_and_positions() -> None:
    """Test Bybit wallet balance and open positions using environment variables."""
    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")

    if not api_key or not api_secret:
        print("❌ Missing BYBIT_API_KEY or BYBIT_API_SECRET environment variables.")
        print("Skipping real API test - this is expected in CI/test environments")
        return

    demo = os.getenv("BYBIT_DEMO", "false").lower() == "true"
    testnet = os.getenv("BYBIT_TESTNET", "false").lower() == "true"

    print("🔑 Creating Bybit client...")
    print(f"   API Key: {api_key[:8]}...")
    print(f"   Demo: {demo}")
    print(f"   Testnet: {testnet}")

    client = BybitClient(
        api_key=api_key,
        api_secret=api_secret,
        demo=demo,
        testnet=testnet,
    )

    await print_wallet_balance(client)
    await print_open_positions(client)
    pprint(await client.get_open_and_closed_orders("linear", settle_coin="USDT"))

    if PLACE_ORDER:
        try:
            result = await client.batch_place_order(
                "linear",
                [
                    PlaceOrderParams(
                        symbol="BTCUSDT",
                        side="Buy",
                        order_type="Market",
                        qty=0.001,
                    )
                ],
            )
            print("✅ Order placed successfully:")
            try:
                pretty_data = json.dumps(result, indent=2, ensure_ascii=False)
                print(pretty_data)
            except Exception:
                print(result)
        except Exception as e:
            print(f"❌ Error placing order: {e}")
    else:
        print("💡 Skipping order placement (PLACE_ORDER=False)")

    await client.close()


if __name__ == "__main__":
    print("Real Bybit API authentication test")
    print(
        "Note: This test makes real API calls and "
        "requires BYBIT_API_KEY/BYBIT_API_SECRET env vars"
    )
    asyncio.run(test_bybit_wallet_and_positions())
