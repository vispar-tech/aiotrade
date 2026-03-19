"""Tests for KUCOIN API authentication (minimal demo)."""

import asyncio
import json
import logging
import os
import sys
from typing import Any

from aiotrade import KuCoinClient
from aiotrade.types.kucoin import TakeProfitStopLossOrderParams

logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


async def main() -> None:
    api_key = os.getenv("KUCOIN_API_KEY")
    api_secret = os.getenv("KUCOIN_API_SECRET")
    passphrase = os.getenv("KUCOIN_API_PASSPHRASE")
    if not (api_key and api_secret and passphrase):
        print("❌ Missing KUCOIN_API_KEY, KUCOIN_API_SECRET, or KUCOIN_API_PASSPHRASE")
        return

    client = KuCoinClient(
        api_key=api_key,
        api_secret=api_secret,
        passphrase=passphrase,
    )
    client.set_verbose(True)

    def print_json(data: dict[str, Any]) -> None:
        s = json.dumps(data, ensure_ascii=False, indent=2)
        print(s)

    print_json(
        await client.add_tp_sl_order(
            # standart limit order
            # commented with tp/sl
            params=TakeProfitStopLossOrderParams(
                clientOid="123123213213",
                side="buy",
                symbol="PEPEUSDTM",
                leverage=3,
                type="limit",
                reduceOnly=False,
                marginMode="ISOLATED",
                positionSide="BOTH",
                price=0.0000032675,
                size=1,
                # timeInForce="GTC",
                # triggerStopUpPrice=0.0000036675,
                # triggerStopDownPrice=0.0000031675,
                # stopPriceType="TP",
            )
        )
    )
    # print_json(
    #     await client.batch_add_orders(
    #         orders=[
    #             PlaceOrderParams(
    #                 clientOid="testing",
    #                 symbol="PEPEUSDTM",
    #                 side="buy",
    #                 leverage=7,
    #                 type="market",
    #                 size=1,
    #             ),
    #             PlaceOrderParams(
    #                 symbol="PEPEUSDTM",
    #                 side="buy",
    #                 leverage=7,
    #                 type="limit",
    #                 price=0.0000036640,
    #                 size=1,
    #             ),
    #             PlaceOrderParams(
    #                 symbol="PEPEUSDTM",
    #                 side="buy",
    #                 leverage=7,
    #                 type="limit",
    #                 price=0.0000036640,
    #                 size=3,
    #             ),
    #         ]
    #     )
    # )
    await client.close()


if __name__ == "__main__":
    print("Minimal Kucoin API client test")
    asyncio.run(main())
