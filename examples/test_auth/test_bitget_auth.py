"""Tests for BITGET API authentication, spot, and futures wallet balance."""

import asyncio
import json
import os
from typing import Any

from aiotrade import BitgetClient
from aiotrade.types.bitget import (
    BatchPlaceOrderItemParams,
)

# Set this to True to actually place a test order in the real API test
PLACE_ORDER = False


async def print_futures_wallet_balance(client: BitgetClient) -> None:
    """Fetch and print BITGET futures wallet balance summary."""
    print("\n📊 Fetching BITGET futures wallet balance...")
    try:
        result = await client.get_account_list("USDT-FUTURES")
        print("✅ Futures wallet balance retrieved successfully!")
        try:
            pretty_resp = json.dumps(result, indent=2, ensure_ascii=False)
            print(f"Full response:\n{pretty_resp}\n")
        except Exception:
            print(f"Full response:\n{result}\n")

        data: list[dict[str, Any]] = result.get("data", [])

        if not data:
            print("No account info found in response.")
            return

        print(f"Found {len(data)} account entr{'y' if len(data) == 1 else 'ies'}")
        for entry in data[:3]:  # Only display up to 3 for brevity
            margin_coin = entry.get("marginCoin", "???")
            locked = entry.get("locked", "?")
            available = entry.get("available", "?")
            account_equity = entry.get("accountEquity", "?")
            usdt_equity = entry.get("usdtEquity", "?")
            btc_equity = entry.get("btcEquity", "?")
            unrealized_pl = entry.get("unrealizedPL", "?")
            print(
                f"   marginCoin: {margin_coin}, locked: {locked}, "
                f"available: {available}, accountEquity: {account_equity}, "
                f"usdtEquity: {usdt_equity}, btcEquity: {btc_equity}, "
                f"unrealizedPL: {unrealized_pl}"
            )
            crossed_risk_rate = entry.get("crossedRiskRate")
            if crossed_risk_rate is not None:
                print(f"      crossedRiskRate: {crossed_risk_rate}")

            # assetList might be present but usually empty for USDT-FUTURES
            asset_list = entry.get("assetList", [])
            if asset_list:
                print("      assetList:")
                for asset in asset_list[:3]:  # Show up to 3 assetList items
                    a_margin_coin = asset.get("marginCoin", "???")
                    a_balance = asset.get("balance", "?")
                    print(
                        f"         asset marginCoin: {a_margin_coin}, "
                        f"balance: {a_balance}"
                    )
            else:
                print("      assetList: []")

    except Exception as e:
        print(f"❌ Error retrieving futures wallet balance: {e}")


async def print_spot_wallet_balance(client: BitgetClient) -> None:
    """Fetch and print BITGET spot wallet balance summary."""
    print("\n💰 Fetching BITGET spot wallet balance...")
    try:
        result = await client.get_account_assets()
        print("✅ Spot wallet balance retrieved successfully!")
        try:
            pretty_resp = json.dumps(result, indent=2, ensure_ascii=False)
            print(f"Full response:\n{pretty_resp}\n")
        except Exception:
            print(f"Full response:\n{result}\n")

        data: list[dict[str, Any]] = result.get("data", [])
        if not data:
            print("No spot asset info found in response.")
            return

        print(f"Found {len(data)} spot asset entr{'y' if len(data) == 1 else 'ies'}")
        # Show up to 3 assets for brevity
        for entry in data[:3]:
            coin = entry.get("coin", "???")
            available = entry.get("available", "?")
            frozen = entry.get("frozen", "?")
            locked = entry.get("locked", "?")
            u_time = entry.get("uTime", "?")
            print(
                f"   coin: {coin}, available: {available}, "
                f"frozen: {frozen}, locked: {locked}, updateTime: {u_time}"
            )
    except Exception as e:
        print(f"❌ Error retrieving spot wallet balance: {e}")


async def print_open_positions(client: BitgetClient) -> None:
    """Print open positions (Bitget)."""
    print("\n📈 Fetching open positions...")
    try:
        resp = await client.get_all_positions("USDT-FUTURES")
        print("✅ Open positions retrieved successfully!")
        try:
            pretty_resp = json.dumps(resp.get("data", []), indent=2, ensure_ascii=False)
            print(f"Full positions response:\n{pretty_resp}\n")
        except Exception:
            print(f"Full positions response:\n{resp}\n")

        positions = resp.get("data", [])
        if not positions:
            print("No open positions found in response.")
            return

        print(
            f"Found {len(positions)} open position{'s' if len(positions) != 1 else ''}"
        )

        # Show up to 3 positions for brevity, also display take profit and stop loss
        for pos in positions[:3]:
            symbol = pos.get("symbol", "???")
            margin_coin = pos.get("marginCoin", "???")
            hold_side = pos.get("holdSide", "?")
            size = pos.get("total", pos.get("marginSize", "0"))
            entry_price = pos.get("openPriceAvg", pos.get("avgOpenPrice", "0"))
            unrealized_pnl = pos.get("unrealizedPL", "0")

            # Use proper keys per API for takeProfit/takeProfitId/stopLoss/stopLossId
            take_profit = pos.get("takeProfit", "-")
            stop_loss = pos.get("stopLoss", "-")
            take_profit_id = pos.get("takeProfitId", "-")
            stop_loss_id = pos.get("stopLossId", "-")

            print(
                f"   {symbol}: side={hold_side}, marginCoin={margin_coin}, "
                f"size={size}, entry={entry_price}, "
                f"unrealizedPnL={unrealized_pnl}, takeProfit={take_profit}, "
                f"takeProfitId={take_profit_id}, "
                f"stopLoss={stop_loss}, stopLossId={stop_loss_id}"
            )
    except AttributeError:
        print("❌ BitgetClient does not have the expected method.")
    except Exception as e:
        print(f"❌ Error retrieving open positions: {e}")


async def test_bitget_wallet_and_positions() -> None:
    """Test BITGET wallet balance (spot and futures) and open positions."""
    api_key = os.getenv("BITGET_API_KEY")
    api_secret = os.getenv("BITGET_API_SECRET")
    passphrase = os.getenv("BITGET_API_PASSPHRASE")

    if not api_key or not api_secret or not passphrase:
        print(
            "❌ Missing BITGET_API_KEY, BITGET_API_SECRET, "
            "or BITGET_API_PASSPHRASE env variables."
        )
        print("Skipping real API test - this is expected in CI/test environments")
        return

    demo = os.getenv("BITGET_DEMO", "false").lower() == "true"

    print("🔑 Creating Bitget client...")
    print(f"   API Key: {api_key[:8]}...")
    print(f"   Demo: {demo}")

    client = BitgetClient(
        api_key=api_key,
        api_secret=api_secret,
        passphrase=passphrase,
        demo=demo,
    )

    await print_futures_wallet_balance(client)
    await print_spot_wallet_balance(client)
    await print_open_positions(client)

    if PLACE_ORDER:
        try:
            # spot order
            # await client.cancel_trigger_orders(
            #     product_type="USDT-FUTURES",
            #     symbol="BTCUSDT",
            #     plan_type="moving_plan",
            #     margin_coin="USDT",
            #     order_id_list=[CancelTriggerOrderItem(orderId="1409871544033230848")],
            # )
            # result_order = await client.place_futures_order(
            #     PlaceOrderParams(
            #         productType="USDT-FUTURES",
            #         symbol="BTCUSDT",
            #         marginMode="isolated",
            #         size=0.01,
            #         side="buy",
            #         orderType="market",
            #         # tradeSide="open",
            #         marginCoin="USDT",
            #         # side="buy",
            #         # posSide="net",
            #         # ordType="market",
            #         # sz=0.01,
            #         # tdMode="isolated",
            #     ),
            # )
            # pprint(result_order)
            # result = await client.place_tpsl_plan_order(
            #     params=PlaceTpslPlanOrderParams(
            #         productType="USDT-FUTURES",
            #         symbol="BTCUSDT",
            #         planType="moving_plan",
            #         triggerPrice=73000,
            #         triggerType="mark_price",
            #         holdSide="buy",
            #         size=0.0200,
            #         marginCoin="USDT",
            #         rangeRate=3,
            #         # planType="track_plan",
            #         # marginMode="crossed",
            #         # marginCoin="USDT",
            #         # size=30,
            #         # side="sell",
            #         # tradeSide="close",
            #         # orderType="market",
            #         # reduceOnly="no",
            #         # triggerType="mark_price",
            #         # triggerPrice=67_000,
            #         # callbackRatio=0.05,
            #     ),
            #     channel_api_code="testing",
            # )
            result = await client.batch_place_futures_orders(
                symbol="BTCUSDT",
                product_type="USDT-FUTURES",
                margin_mode="isolated",
                margin_coin="USDT",
                order_list=[
                    BatchPlaceOrderItemParams(
                        size=0.001,
                        side="buy",
                        orderType="market",
                    ),
                    BatchPlaceOrderItemParams(
                        size=5, side="buy", orderType="limit", price=67000
                    ),
                ],
            )
            # futures order
            # result = await client.batch_place_order(
            #     orders=[
            #         PlaceOrderParams(
            #             instId="BTC-USDT-SWAP",
            #             side="buy",
            #             posSide="net",
            #             ordType="market",
            #             sz=0.01,
            #             tdMode="isolated",
            #             attachAlgoOrds=[
            #                 AttachAlgorithmOrderParams(
            #                     tpTriggerPx=100_000,
            #                     tpOrdPx=-1,
            #                     tpTriggerPxType="mark",
            #                     tpOrdKind="condition",
            #                     # Optionally, add SL as well:
            #                     # "slTriggerPx": ...,
            #                     # "slOrdPx": ...,
            #                     # "slTriggerPxType": ...,
            #                 )
            #             ],
            #         ),
            #     ]
            # )
            print("✅ Swap order placed successfully:")
            try:
                pretty_data = json.dumps(result, indent=2, ensure_ascii=False)
                print(pretty_data)
            except Exception:
                print(result)
        except Exception as err:
            print(f"❌ Error placing swap order: {err}")
    else:
        print("💡 Skipping order placement (PLACE_ORDER=False)")

    await client.close()


if __name__ == "__main__":
    print("Real BITGET API authentication test")
    print(
        "Note: This test makes real API calls and "
        "requires BITGET_API_KEY/BITGET_API_SECRET/BITGET_API_PASSPHRASE env vars"
    )
    asyncio.run(test_bitget_wallet_and_positions())
