import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiotrade import (
    BinanceClient,
    BingxClient,
    BitgetClient,
    BybitClient,
    ExchangeLiteral,
    GateClient,
    KuCoinClient,
    OkxClient,
)
from aiotrade.unified.utils import to_exchange_symbol

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_EXCHANGES: dict[
    ExchangeLiteral,
    tuple[
        type,
        Callable[[Any], Awaitable[Any]],
        Callable[[dict[str, Any]], list[dict[str, Any]]],
        str,
        str,
    ],
] = {
    "bybit": (
        BybitClient,
        lambda c: c.get_tickers("linear"),
        lambda r: r.get("result", {}).get("list", []),
        "symbol",
        "lastPrice",
    ),
    "binance": (
        BinanceClient,
        lambda c: c.get_24hr_ticker(),
        lambda r: r.get("result", {}).get("list", []),
        "symbol",
        "lastPrice",
    ),
    "bingx": (
        BingxClient,
        lambda c: c.get_swap_24hr_ticker(),
        lambda r: r.get("data", []),
        "symbol",
        "lastPrice",
    ),
    "bitget": (
        BitgetClient,
        lambda c: c.get_tickers("USDT-FUTURES"),
        lambda r: r.get("data", []),
        "symbol",
        "lastPr",
    ),
    "gate": (
        GateClient,
        lambda c: c.list_futures_tickers("usdt"),
        lambda r: r.get("result", {}).get("list", []),
        "contract",
        "last",
    ),
    "kucoin": (
        KuCoinClient,
        lambda c: c.get_all_tickers(),
        lambda r: r.get("data", []),
        "symbol",
        "price",
    ),
    "okx": (
        OkxClient,
        lambda c: c.get_index_tickers(quote_ccy="USDT"),
        lambda r: r.get("data", []),
        "instId",
        "idxPx",
    ),
}


async def fetch_prices(exchange: ExchangeLiteral) -> dict[str, Any]:
    client_cls, method, get_list, symbol_key, price_key = _EXCHANGES[exchange]
    async with client_cls() as client:
        try:
            resp = await method(client)
            items: list[dict[str, Any]] = []
            for item in get_list(resp):
                symbol = item.get(symbol_key)
                price = item.get(price_key)
                if symbol is not None and price is not None:
                    items.append({"symbol": str(symbol), "price": float(price)})
            logger.info("[%s] %d tickers", exchange.capitalize(), len(items))
            return {"client": exchange, "prices": items, "response": resp}
        except Exception as e:
            logger.error("[%s] ERROR - %s", exchange.capitalize(), e)
            return {"client": exchange, "prices": [], "error": str(e)}


async def main() -> None:
    client_names: set[ExchangeLiteral] = set(_EXCHANGES.keys())
    results = await asyncio.gather(*(fetch_prices(name) for name in client_names))
    total = sum(len(r.get("prices", [])) for r in results)
    logger.info("Received %d combined tickers from all exchanges.", total)
    if results:
        logger.info("Sample from each exchange (if available):")
        for r in results:
            client = r.get("client")
            if not client:
                logger.error("No client name found for result!")
                continue
            btc_symbol = to_exchange_symbol(client, "BTCUSDT")
            if client == "okx" and btc_symbol.endswith("-SWAP"):
                btc_symbol = btc_symbol[:-5]
            prices = r.get("prices", [])
            if prices:
                btcusdt_price = next(
                    (item for item in prices if item.get("symbol") == btc_symbol), None
                )
                if btcusdt_price is not None:
                    logger.info("%s ticker: %s", client, btcusdt_price)
                else:
                    logger.info("%s first ticker: %s", client, prices[0])
            else:
                logger.info("%s: no tickers received.", client)


if __name__ == "__main__":
    asyncio.run(main())
