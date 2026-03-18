"""Simple tests for exchanges spot and swap account/portfolio balances."""

import asyncio
import logging
import os
import sys
from collections.abc import Callable
from pprint import pprint
from typing import Any

from dotenv import load_dotenv

from aiotrade import ExchangeLiteral, SharedSessionManager
from examples.unified import (
    ExchangeClient,
    UnifiedBinanceClient,
    UnifiedBingxClient,
    UnifiedBitgetClient,
    UnifiedBybitClient,
    UnifiedKuCoinClient,
    UnifiedOkxClient,
)
from examples.unified.helpers import to_exchange_symbol
from examples.unified.types import UnifiedSide

# --- Settings and constants ---

load_dotenv()
PLACING_SYMBOL: str = "PEPEUSDT"
PLACING_QTY: int = 100
PLACING_LEVERAGE: int = 12
TAKE_PROFIT_PERCENT: int = 30
TRAILING_DELIVATION: float = 0.5
STOP_LOSS_PERCENT: int = 60

logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


def check_env(required_vars: list[str]) -> tuple[bool, list[str]]:
    """Check presence of all given env vars."""
    values: list[str] = []
    missing: list[str] = []
    for var in required_vars:
        val = os.getenv(var)
        if not val:
            missing.append(var)
        else:
            values.append(val)
    if missing:
        return False, missing
    return True, values


async def process_exchange(
    client: ExchangeClient, display_name: str, exchange_literal: ExchangeLiteral
) -> None:
    print(f"Process {display_name}")

    exchange_coin = to_exchange_symbol(exchange_literal, PLACING_SYMBOL)
    print(f"Exchange coin symbol: {exchange_coin}")

    if exchange_literal == "kucoin":
        try:
            margin_mode = await client.get_margin_mode(exchange_coin)
            print(f"{display_name} margin_mode:", margin_mode)
        except Exception as e:
            print(f"{display_name} get_margin_mode({exchange_coin}) error:", e)

        try:
            hedge_mode = await client.get_hedge_mode(exchange_coin)
            print(f"{display_name} hedge_mode:", hedge_mode)
        except Exception as e:
            print(f"{display_name} get_hedge_mode({exchange_coin}) error:", e)

        try:
            asset_mode = await client.get_asset_mode()
            print(f"{display_name} asset_mode:", asset_mode)
        except Exception as e:
            print(f"{display_name} get_asset_mode() error:", e)

        try:
            usdt_available_balance = await client.get_usdt_available_balance()
            print(f"{display_name} USDT available balance:", usdt_available_balance)
        except Exception as e:
            print(f"{display_name} get_usdt_available_balance() error:", e)

        try:
            spot_usdt_balance = await client.get_spot_usdt_balance()
            print(f"{display_name} Spot USDT balance:", spot_usdt_balance)
        except Exception as e:
            print(f"{display_name} get_spot_usdt_balance() error:", e)

        try:
            position_info = await client.get_position_info()
            print(f"{display_name} position info:")
            position = position_info[0]
            pprint(position_info)
        except Exception as e:
            print(f"{display_name} get_position_info() error:", e)
        # try:
        #     placed_orders = await client.batch_place_order(
        #         has_existing_position=False,
        #         requests=[
        #             UnifiedPlaceOrderRequest(
        #                 symbol=exchange_coin,
        #                 side=UnifiedSide.LONG,
        #                 price=0.0000033594,
        #                 qty=520000,
        #                 leverage=10,
        #                 order_link_id="test-order-link-id",
        #                 order_type="Market",
        #                 take_profit=0.0000033594 * 1.2,
        #                 stop_loss=0.0000033594 * 0.8,
        #             )
        #         ],
        #     )
        #     print(f"{display_name} placed orders:")
        #     pprint(placed_orders)
        # except Exception as e:
        #     print(f"{display_name} get_position_info() error:", e)
        try:
            await client.set_trading_stop(
                symbol=exchange_coin,
                stop_loss=round(0.0000033594 * 0.8, 10),
                take_profit=round(0.0000033594 * 1.2, 10),
                side=UnifiedSide.LONG,
                position=position,
                # leverage=10,
            )
        except Exception as e:
            print(f"{display_name} set_trading_stop() error:", e)
        # try:
        #     position_info = await client.get_position_info()
        #     print(f"{display_name} position info:")
        #     pprint(position_info)
        # except Exception as e:
        #     print(f"{display_name} get_position_info() error:", e)

        # try:
        #     pending_orders = await client.get_pending_orders()
        #     print(f"{display_name} pending orders:")
        #     pprint(pending_orders)
        # except Exception as e:
        #     print(f"{display_name} get_pending_orders() error:", e)


class ExchangeConfig:
    name: str
    enabled_env: str
    required_env: list[str]
    client_cls: type[ExchangeClient]
    display: str
    param_fn: Callable[[list[str]], dict[str, Any]]
    exchange_literal: ExchangeLiteral

    def __init__(
        self,
        name: str,
        enabled_env: str,
        required_env: list[str],
        client_cls: type[ExchangeClient],
        display: str,
        param_fn: Callable[[list[str]], dict[str, Any]],
        exchange_literal: ExchangeLiteral,
    ) -> None:
        self.name = name
        self.enabled_env = enabled_env
        self.required_env = required_env
        self.client_cls = client_cls
        self.display = display
        self.param_fn = param_fn
        self.exchange_literal = exchange_literal


EXCHANGES: list[ExchangeConfig] = [
    ExchangeConfig(
        name="BingX",
        enabled_env="BINGX_ENABLED",
        required_env=["BINGX_API_KEY", "BINGX_API_SECRET"],
        client_cls=UnifiedBingxClient,
        display="bingx",
        param_fn=lambda values: {
            "account_display": "Testing bingx",
            "api_key": values[0],
            "api_secret": values[1],
            "demo": True,
        },
        exchange_literal="bingx",
    ),
    ExchangeConfig(
        name="Bybit",
        enabled_env="BYBIT_ENABLED",
        required_env=["BYBIT_API_KEY", "BYBIT_API_SECRET"],
        client_cls=UnifiedBybitClient,
        display="bybit",
        param_fn=lambda values: {
            "account_display": "Testing bybit",
            "api_key": values[0],
            "api_secret": values[1],
            "demo": True,
            "testnet": False,
        },
        exchange_literal="bybit",
    ),
    ExchangeConfig(
        name="OKX",
        enabled_env="OKX_ENABLED",
        required_env=["OKX_API_KEY", "OKX_API_SECRET", "OKX_API_PASSPHRASE"],
        client_cls=UnifiedOkxClient,
        display="okx",
        param_fn=lambda values: {
            "account_display": "Testing okx",
            "api_key": values[0],
            "api_secret": values[1],
            "passphrase": values[2],
            "demo": True,
        },
        exchange_literal="okx",
    ),
    ExchangeConfig(
        name="Bitget",
        enabled_env="BITGET_ENABLED",
        required_env=["BITGET_API_KEY", "BITGET_API_SECRET", "BITGET_API_PASSPHRASE"],
        client_cls=UnifiedBitgetClient,
        display="bitget",
        param_fn=lambda values: {
            "account_display": "Testing bitget",
            "api_key": values[0],
            "api_secret": values[1],
            "passphrase": values[2],
            "demo": True,
        },
        exchange_literal="bitget",
    ),
    ExchangeConfig(
        name="Binance",
        enabled_env="BINANCE_ENABLED",
        required_env=["BINANCE_API_KEY", "BINANCE_API_SECRET"],
        client_cls=UnifiedBinanceClient,
        display="binance",
        param_fn=lambda values: {
            "account_display": "Testing binance",
            "api_key": values[0],
            "api_secret": values[1],
            "demo": True,
        },
        exchange_literal="binance",
    ),
    ExchangeConfig(
        name="KuCoin",
        enabled_env="KUCOIN_ENABLED",
        required_env=["KUCOIN_API_KEY", "KUCOIN_API_SECRET", "KUCOIN_API_PASSPHRASE"],
        client_cls=UnifiedKuCoinClient,
        display="kucoin",
        param_fn=lambda values: {
            "account_display": "Testing kucoin",
            "api_key": values[0],
            "api_secret": values[1],
            "passphrase": values[2],
        },
        exchange_literal="kucoin",
    ),
]


async def main() -> None:
    SharedSessionManager.setup()

    for exch in EXCHANGES:
        enabled = os.getenv(exch.enabled_env, "false").lower() == "true"
        ok, values = check_env(exch.required_env)
        print(
            ("\n" if exch.name != "BingX" else "")
            + "=" * 20
            + f" {exch.name} "
            + "=" * 20
        )
        if enabled and ok:
            params = exch.param_fn(values)
            client: ExchangeClient = exch.client_cls(**params)
            await process_exchange(client, exch.display, exch.exchange_literal)
        elif not enabled:
            print(
                f"❌ Skipping {exch.name} test. "
                f"Disabled via {exch.enabled_env} env var."
            )
        else:
            missing = ", ".join(values)
            print(f"❌ Skipping {exch.name} test. Missing env vars: {missing}")

    await SharedSessionManager.close()


if __name__ == "__main__":
    asyncio.run(main())
