"""High-performance cache for KuCoinClient instances."""

from typing import ClassVar

from aiotrade.clients import KuCoinClient

from ._base import BaseClientsCache

_Key = tuple[str, str]


class KuCoinClientsCache(BaseClientsCache[_Key, KuCoinClient]):
    """Ultra-fast singleton cache for KuCoinClient."""

    _cache: ClassVar[dict[_Key, tuple[KuCoinClient, float]]] = {}

    @classmethod
    def _make_key(
        cls,
        api_key: str,
        api_secret: str,
    ) -> _Key:
        """Create a unique tuple for KUCOIN API credentials/configuration."""
        return (api_key, api_secret)

    @classmethod
    def get_or_create(
        cls,
        api_key: str,
        api_secret: str,
        passphrase: str,
        recv_window: int = 5000,
    ) -> KuCoinClient:
        """
        Get KuCoinClient from cache or create/cache it.

        Returns:
            Cached instance (possibly new).
        """
        key = cls._make_key(api_key, api_secret)
        entry = cls._cache.get(key)
        if entry is not None:
            return entry[0]

        client = KuCoinClient(
            api_key=api_key,
            api_secret=api_secret,
            passphrase=passphrase,
            recv_window=recv_window,
        )
        cls.add(client, api_key, api_secret)
        return client
