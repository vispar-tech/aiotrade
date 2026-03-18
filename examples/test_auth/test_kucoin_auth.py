"""Tests for KUCOIN API authentication (minimal demo)."""

import asyncio
import json
import logging
import os
import sys
from typing import Any

from aiotrade import KuCoinClient

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

    def print_json_limited(data: dict[str, Any]) -> None:
        s = json.dumps(data, ensure_ascii=False, indent=2)
        if len(s) > 400:
            s = s[:390] + "...(truncated)"
        print(s)

    result = await client.get_futures_account()
    print_json_limited(result)
    result = await client.get_all_symbols()
    print_json_limited(result)
    result = await client.get_all_tickers()
    print_json_limited(result)
    result = await client.get_server_time()
    print_json_limited(result)
    result = await client.get_service_status()
    print_json_limited(result)
    await client.close()


if __name__ == "__main__":
    print("Minimal Kucoin API client test")
    asyncio.run(main())
