"""Tests for BingX API authentication and spot account assets."""

import asyncio
import json
import os
from typing import Any

from aiotrade import BingxClient
from aiotrade.types.bingx import (
    PlaceSwapOrderParams,
    TpSlStruct,
)

# Set this to True to actually place a swap order in the real API test
PLACE_ORDER = False


async def print_spot_account_assets(client: BingxClient) -> None:
    """Fetch and print BingX spot account assets."""
    print("\n📊 Fetching BingX spot account assets...")
    try:
        result = await client.get_spot_account_assets()
        print("✅ Spot account assets retrieved successfully!")
        try:
            # Pretty-print only the "data" section if possible
            pretty_resp = json.dumps(result.get("data"), indent=2, ensure_ascii=False)
            print(f"Full response:\n{pretty_resp}\n")
        except Exception:
            print(f"Full response:\n{result}\n")

        balances: list[dict[str, Any]] | None = result.get("data", {}).get(
            "balances", None
        )
        if balances is None:
            print(
                "⚠️ Warning: Unexpected balances value -- expected a list but got:",
                type(balances),
            )
            return

        if len(balances) == 0:
            print("No asset balances found in response.")
            return

        print(f"Found {len(balances)} asset balances:")
        for asset in balances[:5]:
            asset_name = asset.get("asset", "???")
            free = asset.get("free", "0")
            locked = asset.get("locked", "0")
            print(f"   {asset_name}: free={free}, locked={locked}")

    except Exception as e:
        print(f"❌ Error retrieving spot account assets: {e}")


async def print_swap_positions(client: BingxClient) -> None:  # noqa: C901, PLR0912, PLR0915
    """Fetch and print BingX open swap positions summary."""
    print("\n📈 Fetching BingX swap open positions...")

    try:
        # Fetch open orders and print them
        open_orders_resp = await client.get_swap_open_orders()
        open_orders = open_orders_resp.get("data", {}).get("orders", [])
        print("✅ Open swap orders retrieved successfully!")
        try:
            pretty_orders_resp = json.dumps(open_orders, indent=2, ensure_ascii=False)
            print(f"Full open orders response:\n{pretty_orders_resp}\n")
        except Exception:
            print(f"Full open orders response:\n{open_orders_resp}\n")

        # Fetch open positions and print them
        resp = await client.get_swap_positions()
        print("✅ Open swap positions retrieved successfully!")
        try:
            pretty_resp = json.dumps(resp.get("data"), indent=2, ensure_ascii=False)
            print(f"Full positions response:\n{pretty_resp}\n")
        except Exception:
            print(f"Full positions response:\n{resp}\n")

        positions: list[dict[str, Any]] | None = resp.get("data")
        if positions is None:
            print(
                "⚠️ Warning: No open positions found in the response "
                "(positions is None)."
            )
            return

        if len(positions) == 0:
            print("No open swap positions found in response.")
            return

        print(f"Found {len(positions)} open swap positions")
        for pos in positions[:3]:
            position_id = pos.get("positionId", "???")
            symbol = pos.get("symbol", "???")
            position_side = pos.get("positionSide", "?")

            size = pos.get("positionAmt", pos.get("positionAmount", "0"))
            entry_price = pos.get("avgEntryPrice", pos.get("entryPrice", "0"))
            unrealized_pnl = pos.get("unRealizedProfit", pos.get("unrealizedPnl", "0"))

            print(
                f"   {symbol}: position_side={position_side}, "
                f"size={size}, entry={entry_price}, unrealized_pnl={unrealized_pnl}"
            )

            # Try to find open stop loss or take profit orders matching this position
            matching_tp: list[dict[str, Any]] = []
            matching_sl: list[dict[str, Any]] = []
            matching_trailing: list[dict[str, Any]] = []

            for order in open_orders:
                order_position_id = order.get("positionID")
                order_type = order.get("type")
                order_position_side = order.get("positionSide")
                if (
                    str(order_position_id) == str(position_id)
                    and position_side == order_position_side
                ):
                    if order_type == "TAKE_PROFIT_MARKET":
                        matching_tp.append(order)
                    if order_type == "STOP_MARKET":
                        matching_sl.append(order)
                    if order_type == "TRAILING_TP_SL":
                        matching_trailing.append(order)

            if matching_tp:
                print(f"      🎯 Matching TP orders ({len(matching_tp)}):")
                for tp_order in matching_tp:
                    tp_id = tp_order.get("orderId")
                    tp_price = tp_order.get("stopPrice")
                    tp_type = tp_order.get("type", "")
                    print(f"         id={tp_id}, type={tp_type}, price={tp_price}")
            else:
                print("      No matching TP orders found.")

            if matching_sl:
                print(f"      🛑 Matching SL orders ({len(matching_sl)}):")
                for sl_order in matching_sl:
                    sl_id = sl_order.get("orderId")
                    sl_price = sl_order.get("stopPrice")
                    sl_type = sl_order.get("type", "")
                    print(f"         id={sl_id}, type={sl_type}, price={sl_price}")
            else:
                print("      No matching SL orders found.")

            if matching_trailing:
                print(
                    f"      🌀 Matching Trailing TP/SL orders "
                    f"({len(matching_trailing)}):"
                )
                for trailing_order in matching_trailing:
                    trail_id = trailing_order.get("orderId")
                    trail_price_rate = trailing_order.get("priceRate")
                    trail_price = trailing_order.get("price")
                    trail_act_price = trailing_order.get("actPrice")
                    trail_type = trailing_order.get("type", "")

                    if trail_price_rate not in [None, ""]:
                        try:
                            percent = float(trail_price_rate) * 100  # type: ignore
                            price_info = f"priceRate={percent:.2f}%"
                        except Exception:
                            price_info = (
                                f"priceRate={trail_price_rate} (ошибка преобразования)"
                            )
                    elif trail_price is not None:
                        price_info = f"price={trail_price}"
                    else:
                        price_info = "no priceRate/price"

                    print(
                        f"         id={trail_id}, type={trail_type}, "
                        f"{price_info}, actPrice={trail_act_price}"
                    )
            else:
                print("      No matching Trailing TP/SL orders found.")

    except Exception as e:
        print(f"❌ Error retrieving open swap positions: {e}")


async def test_bingx_spot_assets_and_positions() -> None:
    """Test BingX spot account assets and swap open positions."""
    api_key = os.getenv("BINGX_API_KEY")
    api_secret = os.getenv("BINGX_API_SECRET")

    if not api_key or not api_secret:
        print("❌ Missing BINGX_API_KEY or BINGX_API_SECRET environment variables.")
        print("Skipping real API test - this is expected in CI/test environments")
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

    await print_spot_account_assets(client)
    await print_swap_positions(client)

    if PLACE_ORDER:
        try:
            result = await client.place_swap_order(
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
            print("✅ Swap order placed successfully:")
            try:
                pretty_data = json.dumps(
                    result.get("data"), indent=2, ensure_ascii=False
                )
                print(pretty_data)
            except Exception:
                print(result)
        except Exception as e:
            print(f"❌ Error placing swap order: {e}")
    else:
        print("💡 Skipping swap order placement (PLACE_ORDER=False)")

    await client.close()


if __name__ == "__main__":
    print("Real BingX API authentication test")
    print(
        "Note: This test makes real API calls and "
        "requires BINGX_API_KEY/BINGX_API_SECRET env vars"
    )
    asyncio.run(test_bingx_spot_assets_and_positions())
