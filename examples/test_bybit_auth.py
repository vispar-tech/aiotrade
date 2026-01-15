"""Tests for Bybit API authentication and wallet balance."""

import asyncio
import os
from typing import Any, Dict

from aiotrade import BybitClient
from aiotrade.types.bybit import AccountType, PlaceOrderParams


async def print_wallet_balance(client: BybitClient) -> Dict[str, Any] | None:
    """Fetch and print wallet balance summary."""
    print("\n📊 Fetching wallet balance...")
    try:
        account_type: AccountType = "UNIFIED"
        result = await client.get_wallet_balance(account_type=account_type, coin="USDT")
        print("✅ Wallet balance retrieved successfully!")
        print(f"Full response:\n{result}")

        result_obj = result.get("result", {})
        accounts = result_obj.get("list", [])
        print(f"Found {len(accounts)} account types")
        for account in accounts[:3]:
            account_type = account.get("accountType", "Unknown")
            total_wallet_balance = account.get("totalWalletBalance", "0")
            print(f"   {account_type}: wallet = {total_wallet_balance}")
            coins = account.get("coin", [])
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
        return result
    except Exception as e:
        print(f"❌ Error retrieving wallet balance: {e}")
        return None


async def print_open_positions(client: BybitClient) -> None:
    """Fetch and print open positions summary."""
    print("\n📈 Fetching open positions...")
    try:
        positions_resp = await client.get_position_info(
            category="linear",
            settle_coin="USDT",
            limit=200,
        )
        print("✅ Open positions retrieved successfully!")
        print(f"Full positions response:\n{positions_resp}")

        pos_result_obj = positions_resp.get("result", {})
        pos_list = pos_result_obj.get("list", [])
        print(f"Found {len(pos_list)} open positions")
        for pos in pos_list[:3]:
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


async def test_wallet_balance_and_positions() -> None:
    """Test wallet balance and open positions retrieval using environment variables."""
    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")

    if not api_key or not api_secret:
        print("❌ Missing BYBIT_API_KEY or BYBIT_API_SECRET environment variables")
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

    try:
        await print_wallet_balance(client)
        await print_open_positions(client)

        await client.batch_place_order(
            "linear",
            [
                PlaceOrderParams(
                    symbol="BTCUSDT",
                    side="Buy",
                    # is_leverage=1,
                    order_type="Market",
                    # tpsl_mode="Full",
                    qty=0.016,
                    # take_profit=99139.95,
                    # stop_loss=93820.24,
                    # order_link_id="js_baa926e2e507480d865c",
                )
            ],
        )

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_wallet_balance_and_positions())
