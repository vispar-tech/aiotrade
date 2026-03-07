"""Tests for exchanges spot and swap account/portfolio balances."""

import asyncio
import logging
import os
import sys
from decimal import Decimal

from dotenv import load_dotenv

from aiotrade import (
    BinanceClient,
    BingxClient,
    BitgetClient,
    BybitClient,
    ExchangeLiteral,
    OkxClient,
)

load_dotenv()
PLACING_SYMBOL = "XRPUSDT"
PLACING_QTY = 100  # "QTY"
PLACING_LEVERAGE = 12
TAKE_PROFIT_PERCENT = 30
TRAILING_DELIVATION = 0.5
STOP_LOSS_PERCENT = 60

logging.basicConfig(stream=sys.stdout, level="CRITICAL")
logger = logging.getLogger(__name__)


def extract_symbol_asset(symbol: str) -> str:
    """
    Extracts the base asset from a trading symbol.

    E.g., 'BTCUSDT' -> 'BTC', 'ETH_USDT' -> 'ETH'.
    Removes any trailing '-' or '_' from the result.
    """
    quote_assets = ["-USDT", "USDT", "-USDC", "USDC", "-USDUSD"]
    for asset in quote_assets:
        pos = symbol.find(asset)
        if pos != -1:
            base = symbol[:pos]
            # Remove any trailing '-' or '_' before returning
            return base.rstrip("-_")
    # Fallback: handle symbols with an underscore, e.g. "BTC_USDT"
    base = symbol.split("_")[0] if "_" in symbol else symbol
    return base.rstrip("-_").lstrip()


def to_exchange_symbol(exchange: ExchangeLiteral, symbol: str) -> str:
    """Convert a symbol to the exchange-specific format."""
    asset = extract_symbol_asset(symbol)
    if exchange == "bingx":
        return asset + "-USDT"
    if exchange in ["bybit", "bitget", "binance"]:
        return asset + "USDT"
    if exchange == "okx":
        return asset + "-USDT-SWAP"
    raise NotImplementedError(f"Exchange {exchange} not implemented")


def _format_number(val: float | str) -> str:
    d = Decimal(str(val))
    return format(d, "f").rstrip("0").rstrip(".") if "." in format(d, "f") else str(d)


def check_env(required_vars: list[str]) -> tuple[bool, list[str]]:
    """Check presence of all given env vars."""
    values: list[str] = []
    missing: list[str] = []
    for var in required_vars:
        val = os.getenv(var)
        if val is None or val == "":
            missing.append(var)
        else:
            values.append(val)
    if missing:
        return False, missing
    return True, values


def get_tp_sl(price: float) -> tuple[float, float]:
    tp_tick = (TAKE_PROFIT_PERCENT / PLACING_LEVERAGE) / 100.0 * price
    # for long use plus
    raw_take_profit_price = price + tp_tick
    correct_take_profit_price = round(raw_take_profit_price, 4)
    # SL logic
    sl_tick = (STOP_LOSS_PERCENT / PLACING_LEVERAGE) / 100.0 * price
    # for long use minus
    raw_stop_loss_price = price - sl_tick
    correct_stop_loss_price = round(raw_stop_loss_price, 4)
    return correct_take_profit_price, correct_stop_loss_price


async def process_bingx(client: BingxClient) -> None:
    print("Process bingx")


async def process_bybit(client: BybitClient) -> None:
    print("Process bybit")


async def process_okx(client: OkxClient) -> None:
    print("Process okx")


async def process_bitget(client: BitgetClient) -> None:
    print("Process bitget")


async def process_binance(client: BinanceClient) -> None:
    print("Process binance")


async def main() -> None:  # noqa: PLR0912, PLR0915
    # Load enabled flags for each exchange
    bingx_enabled = os.getenv("BINGX_ENABLED", "false").lower() == "true"
    bybit_enabled = os.getenv("BYBIT_ENABLED", "false").lower() == "true"
    okx_enabled = os.getenv("OKX_ENABLED", "false").lower() == "true"
    bitget_enabled = os.getenv("BITGET_ENABLED", "false").lower() == "true"
    binance_enabled = os.getenv("BINANCE_ENABLED", "false").lower() == "true"

    # Process BingX
    bingx_ok, bingx_values = check_env(["BINGX_API_KEY", "BINGX_API_SECRET"])
    print("==================== BingX ====================")
    if bingx_enabled and bingx_ok:
        bingx_api_key, bingx_api_secret = bingx_values
        bingx_client = BingxClient(
            api_key=bingx_api_key, api_secret=bingx_api_secret, demo=True
        )
        await process_bingx(bingx_client)
        await bingx_client.close()
    elif not bingx_enabled:
        print("❌ Skipping BingX test. Disabled via BINGX_ENABLED env var.")
    else:
        missing = ", ".join(bingx_values)
        print(f"❌ Skipping BingX test. Missing env vars: {missing}")

    # Process Bybit (use BYBIT_DEMO_API_KEY / BYBIT_DEMO_API_SECRET)
    bybit_ok, bybit_values = check_env(["BYBIT_API_KEY", "BYBIT_API_SECRET"])
    print("\n==================== Bybit ====================")
    if bybit_enabled and bybit_ok:
        bybit_api_key, bybit_api_secret = bybit_values
        bybit_client = BybitClient(
            api_key=bybit_api_key, api_secret=bybit_api_secret, demo=True, testnet=False
        )
        await process_bybit(bybit_client)
        await bybit_client.close()
    elif not bybit_enabled:
        print("❌ Skipping Bybit test. Disabled via BYBIT_ENABLED env var.")
    else:
        missing = ", ".join(bybit_values)
        print(f"❌ Skipping Bybit test. Missing env vars: {missing}")

    # Process OKX
    okx_ok, okx_values = check_env(
        ["OKX_API_KEY", "OKX_API_SECRET", "OKX_API_PASSPHRASE"]
    )
    print("\n==================== OKX ====================")
    if okx_enabled and okx_ok:
        okx_api_key, okx_api_secret, okx_passphrase = okx_values
        okx_client = OkxClient(
            api_key=okx_api_key,
            api_secret=okx_api_secret,
            passphrase=okx_passphrase,
            demo=True,
        )
        await process_okx(okx_client)
        await okx_client.close()
    elif not okx_enabled:
        print("❌ Skipping OKX test. Disabled via OKX_ENABLED env var.")
    else:
        missing = ", ".join(okx_values)
        print(f"❌ Skipping OKX test. Missing env vars: {missing}")

    # Process Bitget
    bitget_ok, bitget_values = check_env(
        ["BITGET_API_KEY", "BITGET_API_SECRET", "BITGET_API_PASSPHRASE"]
    )
    print("\n==================== Bitget ====================")
    if bitget_enabled and bitget_ok:
        bitget_api_key, bitget_api_secret, bitget_passphrase = bitget_values
        bitget_client = BitgetClient(
            api_key=bitget_api_key,
            api_secret=bitget_api_secret,
            passphrase=bitget_passphrase,
            demo=True,
        )
        await process_bitget(bitget_client)
        await bitget_client.close()
    elif not bitget_enabled:
        print("❌ Skipping Bitget test. Disabled via BITGET_ENABLED env var.")
    else:
        missing = ", ".join(bitget_values)
        print(f"❌ Skipping Bitget test. Missing env vars: {missing}")

    # Process Binance
    binance_ok, binance_values = check_env(["BINANCE_API_KEY", "BINANCE_API_SECRET"])
    print("\n==================== Binance ====================")
    if binance_enabled and binance_ok:
        binance_api_key, binance_api_secret = binance_values
        binance_client = BinanceClient(
            api_key=binance_api_key, api_secret=binance_api_secret, demo=True
        )
        await process_binance(binance_client)
        await binance_client.close()
    elif not binance_enabled:
        print("❌ Skipping Binance test. Disabled via BINANCE_ENABLED env var.")
    else:
        missing = ", ".join(binance_values)
        print(f"❌ Skipping Binance test. Missing env vars: {missing}")


if __name__ == "__main__":
    asyncio.run(main())
