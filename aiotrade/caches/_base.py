"""Base high-performance client cache (ABC for exchange client caches)."""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import (
    Any,
    ClassVar,
    Dict,
    Generic,
    Optional,
    Tuple,
    TypeVar,
)

from aiotrade._http import HttpClient

logger = logging.getLogger(__name__)

_Client = TypeVar("_Client", bound=HttpClient)
_Key = TypeVar("_Key")


class BaseClientsCache(ABC, Generic[_Key, _Client]):
    """Abstract base class for ultra-fast singleton exchange client caches."""

    # NOTE: use any cause classvar can't contain typevars
    # NOTE: need to overwrite by parent
    _cache: ClassVar[Dict[Any, Tuple[Any, float]]] = {}
    _lifetime_seconds: ClassVar[int] = 600  # 10 minutes default

    @classmethod
    def configure(cls, lifetime_seconds: int = 600) -> None:
        """Set expiration lifetime (in seconds) for cache entries."""
        cls._lifetime_seconds = lifetime_seconds

    @classmethod
    @abstractmethod
    def _make_key(cls, *args: Any, **kwargs: Any) -> _Key:
        """Create a unique tuple for API credentials/configuration."""
        ...

    @classmethod
    def get(cls, *args: Any, **kwargs: Any) -> Optional[_Client]:
        """Get cached client instance or None."""
        key = cls._make_key(*args, **kwargs)
        entry = cls._cache.get(key)
        if entry is not None:
            return entry[0]  # type: ignore[no-any-return]
        return None

    @classmethod
    def add(cls, client: _Client, *args: Any, **kwargs: Any) -> None:
        """Cache a client, overwriting any existing for key."""
        key = cls._make_key(*args, **kwargs)
        expires_at = time.monotonic() + cls._lifetime_seconds
        cls._cache[key] = (client, expires_at)

    @classmethod
    @abstractmethod
    def get_or_create(cls, *args: Any, **kwargs: Any) -> _Client:
        """Get client from cache or create/cache it if absent."""
        ...

    @classmethod
    def cleanup_expired(cls) -> int:
        """
        Remove all expired clients from the cache.

        Returns:
            Number of entries removed.
        """
        now = time.monotonic()
        expired_keys = [k for k, (_, exp) in cls._cache.items() if exp <= now]
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
                    logger.info("%s: cleaned %d entries", cls.__name__, removed)

        return asyncio.create_task(worker())
