"""
aiobybit - Asynchronous Bybit trading API client.

This package provides:
- BybitClient: Main API client class supporting all Bybit endpoints.
- BybitClientCache: Utility class for caching BybitHttpClient
    instances for efficient reuse.

Usage example:

    from aiobybit import BybitClient, BybitClientCache

    # Create a new BybitClient
    client = BybitClient(api_key="xxx", api_secret="yyy", testnet=True)

    # Optionally, use the cache for managing clients
    cached_client = BybitClientCache.get_or_create(
        api_key="xxx",
        api_secret="yyy",
        testnet=True,
    )
"""

from .cache import BybitClientCache
from .client import BybitClient

__all__ = [
    "BybitClient",
    "BybitClientCache",
]
