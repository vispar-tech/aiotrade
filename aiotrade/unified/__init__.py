"""
Unified client interface for multiple cryptocurrency exchanges.

This package exposes a consistent async API for spot and futures trading,
providing normalized types and operations across supported exchanges.

Public API:
- ExchangeClient: Protocol specifying the unified client interface.
- Unified[Exchange]Client: Concrete implementations for each supported exchange.
  These clients implement ExchangeClient and provide normalized methods for trading,
  balance queries, and position management.

Available unified clients:
    - UnifiedBinanceClient
    - UnifiedBingxClient
    - UnifiedBitgetClient
    - UnifiedBybitClient
    - UnifiedKuCoinClient
    - UnifiedOkxClient

Example usage:
    from aiotrade.unified import UnifiedBinanceClient

    client = UnifiedBinanceClient(
        api_key="...",
        api_secret="...",
        log_name="Demo",
    )
    margin_mode = await client.get_margin_mode("BTCUSDT")

See class docstrings for per-exchange notes and required parameters.
"""

from ._clients.binance import UnifiedBinanceClient
from ._clients.bingx import UnifiedBingxClient
from ._clients.bitget import UnifiedBitgetClient
from ._clients.bybit import UnifiedBybitClient
from ._clients.kucoin import UnifiedKuCoinClient
from ._clients.okx import UnifiedOkxClient
from ._protocol import UnifiedClient

__all__ = [
    "UnifiedBinanceClient",
    "UnifiedBingxClient",
    "UnifiedBitgetClient",
    "UnifiedBybitClient",
    "UnifiedClient",
    "UnifiedKuCoinClient",
    "UnifiedOkxClient",
]
