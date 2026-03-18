"""
aiotrade - Asynchronous trading API client.

This package provides:
- BingxClient: Main API client class supporting all BingX endpoints
    (Spot, Swap, Futures).
- BybitClient: Main API client class supporting all Bybit endpoints.
- BingxClientsCache & BybitClientsCache: Utility classes for caching trading client
    instances for efficient reuse.
- SharedSessionManager: Shared async HTTP session manager for all clients.

Usage example:

    from aiotrade import BingxClient, BybitClient, BingxClientsCache, \
        SharedSessionManager

    # At application startup, initialize the shared session (recommended)
    SharedSessionManager.setup(max_connections=2000)

    # Create clients for different exchanges
    bingx_client = BingxClient(api_key="xxx", api_secret="yyy", demo=True)
    bybit_client = BybitClient(api_key="xxx", api_secret="yyy", testnet=True)

    # Optionally, use the cache for managing clients
    cached_bingx = BingxClientsCache.get_or_create(
        api_key="xxx",
        api_secret="yyy",
        demo=True,
    )

    # At graceful shutdown
    await SharedSessionManager.close()
"""

from importlib.metadata import version as get_version

from ._errors import ExchangeResponseError
from ._session import SharedSessionManager
from ._types import Exchange as ExchangeLiteral
from .caches import (
    BinanceClientsCache,
    BingxClientsCache,
    BitgetClientsCache,
    BybitClientsCache,
    KuCoinClientsCache,
    OkxClientsCache,
)
from .clients import (
    BinanceClient,
    BingxClient,
    BitgetClient,
    BybitClient,
    KuCoinClient,
    OkxClient,
)

__all__ = [
    "BinanceClient",
    "BinanceClientsCache",
    "BingxClient",
    "BingxClientsCache",
    "BitgetClient",
    "BitgetClientsCache",
    "BybitClient",
    "BybitClientsCache",
    "ExchangeLiteral",
    "ExchangeResponseError",
    "KuCoinClient",
    "KuCoinClientsCache",
    "OkxClient",
    "OkxClientsCache",
    "SharedSessionManager",
]


__version__ = get_version("aiotrade-sdk")
