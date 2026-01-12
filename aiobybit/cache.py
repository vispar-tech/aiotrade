"""Cache module for BybitHttpClient instances."""

import asyncio
import hashlib
import logging
import time
from typing import ClassVar, Dict, Never, Optional, Tuple

from .http import BybitHttpClient

logger = logging.getLogger(__name__)


class BybitClientCache:
    """Singleton cache for BybitHttpClient instances with configurable lifetime."""

    _cache: ClassVar[Dict[str, Tuple[BybitHttpClient, float]]] = {}
    _lifetime_seconds: ClassVar[int] = 600  # 10 minutes default

    @classmethod
    def configure(cls, lifetime_seconds: int = 600) -> None:
        """Configure cache lifetime in seconds.

        Args:
            lifetime_seconds: How long to cache clients (default 600 = 10 minutes)
        """
        cls._lifetime_seconds = lifetime_seconds

    @classmethod
    def _make_key(
        cls,
        api_key: str,
        api_secret: str,
        demo: bool,
        testnet: bool,
    ) -> str:
        """Create cache key hash from client parameters."""
        key_data = f"{api_key}:{api_secret}:{demo}:{testnet}"
        return hashlib.sha256(key_data.encode()).hexdigest()

    @classmethod
    def _is_expired(cls, timestamp: float) -> bool:
        """Check if cache entry is expired."""
        return time.time() - timestamp > cls._lifetime_seconds

    @classmethod
    def get(
        cls,
        api_key: str,
        api_secret: str,
        demo: bool = False,
        testnet: bool = False,
    ) -> Optional[BybitHttpClient]:
        """Get cached client if exists and not expired."""
        key = cls._make_key(api_key, api_secret, demo, testnet)
        if key in cls._cache:
            client, timestamp = cls._cache[key]
            if not cls._is_expired(timestamp):
                return client
            # Remove expired entry
            del cls._cache[key]
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
        """Add or update client in cache."""
        key = cls._make_key(api_key, api_secret, demo, testnet)
        cls._cache[key] = (client, time.time())

    @classmethod
    def update(
        cls,
        client: BybitHttpClient,
        api_key: str,
        api_secret: str,
        demo: bool = False,
        testnet: bool = False,
    ) -> None:
        """Update existing client in cache (same as add)."""
        cls.add(client, api_key, api_secret, demo, testnet)

    @classmethod
    def remove(
        cls,
        api_key: str,
        api_secret: str,
        demo: bool = False,
        testnet: bool = False,
    ) -> bool:
        """Remove client from cache. Returns True if removed, False if not found."""
        key = cls._make_key(api_key, api_secret, demo, testnet)
        if key in cls._cache:
            del cls._cache[key]
            return True
        return False

    @classmethod
    def clear(cls) -> None:
        """Clear all cached clients."""
        cls._cache.clear()

    @classmethod
    def cleanup_expired(cls) -> int:
        """Remove all expired entries. Returns number of entries removed."""
        expired_keys = [
            key
            for key, (_, timestamp) in cls._cache.items()
            if cls._is_expired(timestamp)
        ]
        for key in expired_keys:
            del cls._cache[key]
        return len(expired_keys)

    @classmethod
    def size(cls) -> int:
        """Get current cache size."""
        return len(cls._cache)

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
        """Get cached client or create new one if doesn't exist.

        Args:
            api_key: Bybit API key
            api_secret: Bybit API secret
            testnet: Use testnet instead of mainnet
            domain: Domain name (default: "bybit")
            tld: Top level domain (default: "com")
            demo: Use demo trading
            rsa_authentication: Use RSA authentication
            base_url: Custom base URL
            recv_window: Receive window in milliseconds
            referral_id: Referral ID

        Returns:
            BybitHttpClient instance (cached or newly created)
        """
        # Try to get from cache first
        cached_client = cls.get(api_key, api_secret, demo, testnet)
        if cached_client is not None:
            return cached_client

        # Create new client and cache it
        new_client = BybitHttpClient(
            api_key=api_key,
            api_secret=api_secret,
            testnet=testnet,
            demo=demo,
            recv_window=recv_window,
            referral_id=referral_id,
        )

        cls.add(new_client, api_key, api_secret, demo, testnet)
        return new_client

    @classmethod
    def create_cleanup_task(
        cls,
        interval_seconds: int = 60,
    ) -> asyncio.Task[None]:
        """Create a background task that periodically cleans up expired entries.

        Args:
            interval_seconds: How often to run cleanup (default 60 seconds)

        Returns:
            asyncio.Task that can be cancelled to stop cleanup
        """

        async def cleanup_worker() -> Never:
            while True:
                await asyncio.sleep(interval_seconds)
                removed_count = cls.cleanup_expired()
                if removed_count > 0:
                    logger.info(f"Cleaned up {removed_count} expired cache entries")

        return asyncio.create_task(cleanup_worker())
