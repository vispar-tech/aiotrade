r"""Tests for BINANCE API authentication, spot, and futures wallet balance."""

import asyncio
import json
import logging
import os
import sys
from typing import Any

from aiotrade import BinanceClient
from aiotrade.types.binance import (
    TrailingStopMarketAlgorithmOrderParams,
)

# Set this to True to actually place a test order in the real API test
PLACE_ORDER = False

logging.basicConfig(stream=sys.stdout, level="DEBUG")


async def print_futures_wallet_balance(client: BinanceClient) -> None:
    """Fetch and print BINANCE futures wallet balance summary."""
    print("\n📊 Fetching BINANCE futures wallet balance...")
    try:
        response = await client.get_account_balance()
        print("✅ Futures wallet balance retrieved successfully!")
        try:
            pretty_resp = json.dumps(response, indent=2, ensure_ascii=False)
            print(f"Full response:\n{pretty_resp}\n")
        except Exception:
            print(f"Full response:\n{response}\n")

        balances: list[dict[str, Any]] = response.get("result", {}).get("list", [])

        if not balances:
            print("No account info found in response.")
            return

        print(f"Found {len(balances)} asset entr{'y' if len(balances) == 1 else 'ies'}")
        for entry in balances:
            asset = entry.get("asset", "???")
            balance = entry.get("balance", "?")
            cross_wallet_balance = entry.get("crossWalletBalance", "?")
            available_balance = entry.get("availableBalance", "?")
            unrealized_pnl = entry.get("crossUnPnl", "?")
            print(
                f"   asset: {asset}, balance: {balance}, "
                f"crossWalletBalance: {cross_wallet_balance}, "
                f"availableBalance: {available_balance}, "
                f"unrealizedPnL: {unrealized_pnl}"
            )
    except Exception as e:
        print(f"❌ Error retrieving futures wallet balance: {e}")


async def print_spot_wallet_balance(client: BinanceClient) -> None:
    """Fetch and print BINANCE spot wallet balance summary."""
    print("\n💰 Fetching BINANCE spot wallet balance...")
    try:
        response = await client.get_spot_account_info()
        balances = response.get("result", {}).get("balances", [])
        print("✅ Spot wallet balance retrieved successfully!")
        try:
            pretty_resp = json.dumps(balances, indent=2, ensure_ascii=False)
            print(f"Full response:\n{pretty_resp}\n")
        except Exception:
            print(f"Full response:\n{balances}\n")

        if not balances:
            print("No spot asset info found in response.")
            return

        print(
            f"Found {len(balances)} spot asset "
            f"entr{'y' if len(balances) == 1 else 'ies'}"
        )
        # Show up to 3 assets for brevity
        for entry in balances[:3]:
            asset = entry.get("asset", "???")
            free = entry.get("free", "?")
            locked = entry.get("locked", "?")
            print(f"   asset: {asset}, free: {free}, locked: {locked}")
    except Exception as e:
        print(f"❌ Error retrieving spot wallet balance: {e}")


async def print_open_positions(client: BinanceClient) -> None:
    """Print open positions (Binance USDT-margined futures)."""
    print("\n📈 Fetching open positions (USDT-margined futures)...")
    try:
        response = await client.get_position_info()
        print("✅ Open positions retrieved successfully!")
        try:
            pretty_resp = json.dumps(response, indent=2, ensure_ascii=False)
            print(f"Full positions response:\n{pretty_resp}\n")
        except Exception:
            print(f"Full positions response:\n{response}\n")

        # Only show non-zero positions
        open_positions = response.get("result", {}).get("list", [])

        if not open_positions:
            print("No open positions found in response.")
            return

        print(
            f"Found {len(open_positions)} "
            f"open position{'s' if len(open_positions) != 1 else ''}"
        )

        # Show up to 3 positions for brevity
        for pos in open_positions[:3]:
            symbol = pos.get("symbol", "???")
            position_side = pos.get("positionSide", "BOTH")
            position_amt = pos.get("positionAmt", "0")
            entry_price = pos.get("entryPrice", "0")
            mark_price = pos.get("markPrice", "?")
            unrealized_pnl = pos.get("unRealizedProfit", "0")
            liquidation_price = pos.get("liquidationPrice", "?")
            margin_asset = pos.get("marginAsset", "?")
            update_time = pos.get("updateTime", "?")

            print(
                f"   {symbol}: positionSide={position_side}, qty={position_amt}, "
                f"entry={entry_price}, mark={mark_price}, "
                f"unrealizedPnL={unrealized_pnl}, liqPx={liquidation_price}, "
                f"marginAsset={margin_asset}, updateTime={update_time}"
            )
    except AttributeError:
        print("❌ BinanceClient does not have the expected method.")
    except Exception as e:
        print(f"❌ Error retrieving open positions: {e}")


async def test_binance_wallet_and_positions() -> None:
    """Test BINANCE wallet balance (spot and futures) and open positions."""
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")

    if not api_key or not api_secret:
        print("❌ Missing BINANCE_API_KEY or BINANCE_API_SECRET env variables.")
        print("Skipping real API test - this is expected in CI/test environments")
        return

    demo = os.getenv("BINANCE_DEMO", "false").lower() == "true"

    print("🔑 Creating Binance client...")
    print(f"   API Key: {api_key[:8]}...")
    print(f"   Demo: {demo}...")
    print(api_key, api_secret)
    client = BinanceClient(api_key=api_key, api_secret=api_secret, demo=demo)
    client.set_verbose(True)

    await print_futures_wallet_balance(client)
    await print_spot_wallet_balance(client)
    await print_open_positions(client)

    if True:
        try:
            # resp = await client.create_batch_orders(
            #     params=[
            #         CreateOrderParams(
            #             symbol="BTCUSDT",
            #             side="BUY",
            #             type="MARKET",
            #             quantity=0.003,
            #         )
            #     ]
            # )

            # print("✅ Futures order placed successfully:")
            # try:
            #     pretty_data = json.dumps(resp, indent=2, ensure_ascii=False)
            #     print(pretty_data)
            # except Exception:
            #     print(resp)

            resp = await client.create_algo_order(
                params=TrailingStopMarketAlgorithmOrderParams(
                    algoType="CONDITIONAL",
                    symbol="BTCUSDT",
                    side="SELL",
                    type="TRAILING_STOP_MARKET",
                    quantity=0.018,
                    reduceOnly="true",
                    activatePrice=70_000,
                    callbackRate=0.5,
                )
            )

            # # place tp
            # resp = await client.create_algo_order(
            #     params=StopTakeProfitAlgorithmOrderParams(
            #         algoType="CONDITIONAL",
            #         symbol="BTCUSDT",
            #         side="SELL",
            #         type="TAKE_PROFIT_MARKET",
            #         closePosition="true",
            #         triggerPrice=75000,
            #     )
            # )

            print("✅ Futures order placed successfully:")
            try:
                pretty_data = json.dumps(resp, indent=2, ensure_ascii=False)
                print(pretty_data)
            except Exception:
                print(resp)
            try:
                pretty_data = json.dumps(
                    await client.get_open_algo_orders(), indent=2, ensure_ascii=False
                )
                print(pretty_data)
            except Exception:
                print("Exc algo orders")
        except Exception as err:
            print(f"❌ Error placing futures order: {err}")
    else:
        print("💡 Skipping order placement (PLACE_ORDER=False)")

    await client.close()


if __name__ == "__main__":
    print("Real BINANCE API authentication test")
    print(
        "Note: This test makes real API calls and "
        "requires BINANCE_API_KEY/BINANCE_API_SECRET env vars"
    )
    asyncio.run(test_binance_wallet_and_positions())
