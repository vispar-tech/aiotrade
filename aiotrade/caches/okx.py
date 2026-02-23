"""High-performance cache for OkxClient instances."""

from typing import ClassVar

from aiotrade.clients import OkxClient

from ._base import BaseClientsCache

_Key = tuple[str, str, bool]


class OkxClientsCache(BaseClientsCache[_Key, OkxClient]):
    """Ultra-fast singleton cache for OkxClient."""

    _cache: ClassVar[dict[_Key, tuple[OkxClient, float]]] = {}

    @classmethod
    def _make_key(
        cls,
        api_key: str,
        api_secret: str,
        demo: bool = False,
    ) -> _Key:
        """
        Create a unique tuple for OKX API credentials/configuration.

        demo must be consistent with all uses!
        """
        return (api_key, api_secret, demo)

    @classmethod
    def get_or_create(
        cls,
        api_key: str,
        api_secret: str,
        passphrase: str,
        demo: bool = False,
        recv_window: int = 5000,
    ) -> OkxClient:
        """
        Get OkxClient from cache or create/cache it.

        Returns:
            Cached instance (possibly new).
        """
        key = cls._make_key(api_key, api_secret, demo)
        entry = cls._cache.get(key)
        if entry is not None:
            return entry[0]

        client = OkxClient(
            api_key=api_key,
            api_secret=api_secret,
            passphrase=passphrase,
            demo=demo,
            recv_window=recv_window,
        )
        cls.add(client, api_key, api_secret, demo=demo)
        return client
