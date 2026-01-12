"""High-performance cache for BybitHttpClient instances."""

import asyncio
import logging
import time
from typing import ClassVar, Dict, Optional

from .http import BybitHttpClient

logger = logging.getLogger(__name__)

_Key = tuple[str, str, bool, bool]
_Val = tuple[BybitHttpClient, float]  # (client, expires_at)


class BybitClientCache:
    """Ultra-fast singleton cache for BybitHttpClient.

    Stores BybitHttpClient instances with TTL to prevent memory leaks.
    Lock-free for maximum performance.
    """

    _cache: ClassVar[Dict[_Key, _Val]] = {}
    _lifetime_seconds: ClassVar[int] = 600  # 10 minutes default

    @classmethod
    def configure(cls, lifetime_seconds: int = 600) -> None:
        """Set expiration lifetime (in seconds) for cache entries."""
        cls._lifetime_seconds = lifetime_seconds

    @classmethod
    def _make_key(
        cls,
        api_key: str,
        api_secret: str,
        demo: bool,
        testnet: bool,
    ) -> _Key:
        """Create a unique tuple for API credentials and configuration."""
        return (api_key, api_secret, demo, testnet)

    @classmethod
    def get(
        cls,
        api_key: str,
        api_secret: str,
        demo: bool = False,
        testnet: bool = False,
    ) -> Optional[BybitHttpClient]:
        """Get cached BybitHttpClient instance or None."""
        key = cls._make_key(api_key, api_secret, demo, testnet)
        entry = cls._cache.get(key)
        if entry is not None:
            return entry[0]
        return None

    @classmethod
    def add(
        cls,
        client: BybitHttpClient,
        api_key: str,
        api_secret: str,
        demo: bool = False,
        testnet: bool = False,
    ) -> None:
        """Cache a BybitHttpClient, overwriting any existing for key."""
        key = cls._make_key(api_key, api_secret, demo, testnet)
        expires_at = time.monotonic() + cls._lifetime_seconds
        cls._cache[key] = (client, expires_at)

    @classmethod
    def get_or_create(
        cls,
        api_key: str,
        api_secret: str,
        testnet: bool = False,
        demo: bool = False,
        recv_window: int = 5000,
        referral_id: str | None = None,
    ) -> BybitHttpClient:
        """
        Get BybitHttpClient from cache or create/cache it.

        Returns:
            Cached instance (possibly new).
        """
        key = cls._make_key(api_key, api_secret, demo, testnet)
        entry = cls._cache.get(key)
        if entry is not None:
            return entry[0]

        client = BybitHttpClient(
            api_key=api_key,
            api_secret=api_secret,
            testnet=testnet,
            demo=demo,
            recv_window=recv_window,
            referral_id=referral_id,
        )

        cls._cache[key] = (
            client,
            time.monotonic(),
        )
        return client

    @classmethod
    def cleanup_expired(cls) -> int:
        """
        Remove all expired clients from the cache.

        Returns:
            Number of entries removed.
        """
        now = time.monotonic()
        expired_keys = [
            k
            for k, (_, exp) in cls._cache.items()
            if exp + cls._lifetime_seconds <= now
        ]
        for k in expired_keys:
            del cls._cache[k]
        return len(expired_keys)

    @classmethod
    def size(cls) -> int:
        """Return the current number of entries in the cache."""
        return len(cls._cache)

    @classmethod
    def clear(cls) -> None:
        """Clear all entries from cache."""
        cls._cache.clear()

    @classmethod
    def create_cleanup_task(
        cls,
        interval_seconds: int = 60,
    ) -> asyncio.Task[None]:
        """Background task: periodically clean up expired entries."""

        async def worker() -> None:
            while True:
                await asyncio.sleep(interval_seconds)
                removed = cls.cleanup_expired()
                if removed:
                    logger.info("BybitClientCache: cleaned %d entries", removed)

        return asyncio.create_task(worker())
