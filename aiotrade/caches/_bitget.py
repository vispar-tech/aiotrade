"""High-performance cache for BitgetClient instances."""

from typing import ClassVar

from aiotrade.clients import BitgetClient

from ._base import BaseClientsCache

_Key = tuple[str, str, bool]


class BitgetClientsCache(BaseClientsCache[_Key, BitgetClient]):
    """Ultra-fast singleton cache for BitgetClient."""

    _cache: ClassVar[dict[_Key, tuple[BitgetClient, float]]] = {}

    @classmethod
    def _make_key(
        cls,
        api_key: str,
        api_secret: str,
        demo: bool = False,
    ) -> _Key:
        """
        Create a unique tuple for BITGET API credentials/configuration.

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
    ) -> BitgetClient:
        """
        Get BitgetClient from cache or create/cache it.

        Returns:
            Cached instance (possibly new).
        """
        key = cls._make_key(api_key, api_secret, demo)
        entry = cls._cache.get(key)
        if entry is not None:
            return entry[0]

        client = BitgetClient(
            api_key=api_key,
            api_secret=api_secret,
            passphrase=passphrase,
            demo=demo,
            recv_window=recv_window,
        )
        cls.add(client, api_key, api_secret, demo=demo)
        return client
