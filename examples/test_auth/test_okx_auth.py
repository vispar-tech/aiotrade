"""Tests for OKX API authentication and wallet balance."""

import asyncio
import json
import os
from typing import Any

from aiotrade import OkxClient
from aiotrade.types.okx import PlaceOrderParams

# Set this to True to actually place a test order in the real API test
PLACE_ORDER = False


async def print_wallet_balance(client: OkxClient) -> None:
    """Fetch and print OKX wallet balance summary."""
    print("\n📊 Fetching OKX wallet balance...")
    try:
        result = await client.get_balance()
        print("✅ Wallet balance retrieved successfully!")
        try:
            pretty_resp = json.dumps(result, indent=2, ensure_ascii=False)
            print(f"Full response:\n{pretty_resp}\n")
        except Exception:
            print(f"Full response:\n{result}\n")

        data: list[dict[str, Any]] | None = result.get("data")
        if data is None:
            print(
                "⚠️ Warning: Unexpected data value -- expected a list but got:",
                type(data),
            )
            return

        if not data:
            print("No account info found in response.")
            return

        print(f"Found {len(data)} account entries")
        for entry in data[:3]:
            total_eq = entry.get("totalEq", "0")
            iso_eq = entry.get("isoEq", "0")
            u_time = entry.get("uTime", "-")
            print(
                f"   account: totalEq = {total_eq}, "
                f"isoEq = {iso_eq}, updated = {u_time}"
            )

            details: list[dict[str, Any]] | None = entry.get("details")
            if details is None:
                print(
                    "      ⚠️ Warning: Unexpected details value -- "
                    "expected a list but got:",
                    type(details),
                )
                continue

            if not details:
                print("      No coin details found in response.")
            if details:
                print("      Coins:")
                for coin in details[:3]:
                    coin_ccy = coin.get("ccy", "???")
                    avail_bal = coin.get("availBal", "0")
                    eq = coin.get("eq", "0")
                    frozen_bal = coin.get("frozenBal", "0")
                    print(
                        f"         {coin_ccy}: availBal={avail_bal}, "
                        f"eq={eq}, frozenBal={frozen_bal}"
                    )

    except Exception as e:
        print(f"❌ Error retrieving wallet balance: {e}")


async def print_open_positions(client: OkxClient) -> None:  # noqa: PLR0912
    """Fetch and print OKX open positions summary."""
    print("\n📈 Fetching open positions...")
    try:
        resp = await client.get_positions(inst_type="SWAP")
        print("✅ Open positions retrieved successfully!")
        try:
            pretty_resp = json.dumps(resp, indent=2, ensure_ascii=False)
            print(f"Full positions response:\n{pretty_resp}\n")
        except Exception:
            print(f"Full positions response:\n{resp}\n")

        positions = resp.get("data", [])
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
            inst_id = pos.get("instId", "???")
            pos.get("posMode", "").lower()  # net/cross, etc.
            inst_type = pos.get("instType", "")
            pos_sz_str = pos.get("pos", pos.get("posSz", "0"))
            try:
                pos_sz = float(pos_sz_str)
            except Exception:
                pos_sz = 0.0

            # net mode
            if inst_type in ("FUTURES", "SWAP", "OPTION"):
                if pos_sz > 0:
                    real_side = "long"
                elif pos_sz < 0:
                    real_side = "short"
                else:
                    real_side = "flat"
            elif inst_type == "MARGIN":
                # For MARGIN, pos is always positive,
                # posCcy being base means long, quote means short
                pos_ccy = pos.get("posCcy", "?")
                base_ccy = (
                    pos.get("instId", ":").split("-")[0] if "instId" in pos else "?"
                )
                real_side = "long" if pos_ccy == base_ccy else "short"
            else:
                # Fallback to unknown
                real_side = "unknown"

            avg_px = pos.get("avgPx", "0")
            upl = pos.get("upl", "N/A")

            # Display both original posSide (if available), real_side, and size (abs)
            print(
                f"   {inst_id}: raw_posSide={pos.get('posSide', '-')}, "
                f"net_side={real_side}, "
                f"size={abs(pos_sz)}, avgPx={avg_px}, UPL={upl}"
            )
    except AttributeError:
        print("❌ OkxClient does not have the expected method.")
    except Exception as e:
        print(f"❌ Error retrieving open positions: {e}")


async def test_okx_wallet_and_positions() -> None:
    """Test OKX wallet balance and open positions using environment variables."""
    api_key = os.getenv("OKX_API_KEY")
    api_secret = os.getenv("OKX_API_SECRET")
    passphrase = os.getenv("OKX_API_PASSPHRASE")

    if not api_key or not api_secret or not passphrase:
        print(
            "❌ Missing OKX_API_KEY, OKX_API_SECRET, "
            "or OKX_API_PASSPHRASE env variables."
        )
        print("Skipping real API test - this is expected in CI/test environments")
        return

    demo = os.getenv("OKX_DEMO", "false").lower() == "true"

    print("🔑 Creating Okx client...")
    print(f"   API Key: {api_key[:8]}...")
    print(f"   Demo: {demo}")

    client = OkxClient(
        api_key=api_key,
        api_secret=api_secret,
        passphrase=passphrase,
        demo=demo,
    )

    await print_wallet_balance(client)
    await print_open_positions(client)

    if PLACE_ORDER:
        try:
            # spot order
            result = await client.batch_place_order(
                orders=[
                    PlaceOrderParams(
                        instId="BTC-USDT-SWAP",
                        tdMode="isolated",
                        side="buy",
                        ordType="market",
                        tradeQuoteCcy="USDT",
                        sz=0.01,
                    ),
                    PlaceOrderParams(
                        instId="BTC-USDT-SWAP",
                        tdMode="isolated",
                        side="buy",
                        ordType="limit",
                        tradeQuoteCcy="USDT",
                        sz=0.01,
                        # px=65000,
                    ),
                ]
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
    print("Real OKX API authentication test")
    print(
        "Note: This test makes real API calls and "
        "requires OKX_API_KEY/OKX_API_SECRET/OKX_API_PASSPHRASE env vars"
    )
    asyncio.run(test_okx_wallet_and_positions())
