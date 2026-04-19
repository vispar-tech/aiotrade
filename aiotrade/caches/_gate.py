"""High-performance cache for GateClient instances."""

from typing import ClassVar

from aiotrade.clients import GateClient

from ._base import BaseClientsCache

_Key = tuple[str, str, bool]


class GateClientsCache(BaseClientsCache[_Key, GateClient]):
    """Ultra-fast singleton cache for GateClient."""

    _cache: ClassVar[dict[_Key, tuple[GateClient, float]]] = {}

    @classmethod
    def _make_key(
        cls,
        api_key: str,
        api_secret: str,
        demo: bool = False,
    ) -> _Key:
        """
        Create a unique tuple for API credentials/configuration.

        demo must be consistent with all uses!
        """
        return (api_key, api_secret, demo)

    @classmethod
    def get_or_create(
        cls,
        api_key: str,
        api_secret: str,
        demo: bool = False,
    ) -> GateClient:
        """
        Get GateClient from cache or create/cache it.

        Returns:
            Cached instance (possibly new).
        """
        key = cls._make_key(api_key, api_secret, demo)
        entry = cls._cache.get(key)
        if entry is not None:
            return entry[0]

        client = GateClient(
            api_key=api_key,
            api_secret=api_secret,
            demo=demo,
        )
        cls.add(client, api_key, api_secret, demo=demo)
        return client
