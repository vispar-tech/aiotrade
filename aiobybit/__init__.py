"""
aiobybit - Asynchronous Bybit trading API client.

This package provides:
- BybitClient: Main API client class supporting all Bybit endpoints.
- BybitClientCache: Utility class for caching BybitHttpClient
    instances for efficient reuse.
- BybitSessionManager: Shared async HTTP session manager for all clients.

Usage example:

    from aiobybit import BybitClient, BybitClientCache, BybitSessionManager

    # At application startup, initialize the shared session (recommended)
    BybitSessionManager.setup(max_connections=2000)

    # Create a new BybitClient
    client = BybitClient(api_key="xxx", api_secret="yyy", testnet=True)

    # Optionally, use the cache for managing clients
    cached_client = BybitClientCache.get_or_create(
        api_key="xxx",
        api_secret="yyy",
        testnet=True,
    )

    # At graceful shutdown
    await BybitSessionManager.close()
"""

from .cache import BybitClientCache
from .client import BybitClient
from .session import BybitSessionManager

__all__ = [
    "BybitClient",
    "BybitClientCache",
    "BybitSessionManager",
]
