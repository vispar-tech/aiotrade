"""High-performance cache for BybitClient instances."""

from typing import ClassVar, Dict, Tuple

from aiotrade.clients import BybitClient

from ._base import BaseClientsCache

_Key = tuple[str, str, bool, bool]


class BybitClientsCache(BaseClientsCache[_Key, BybitClient]):
    """Ultra-fast singleton cache for BybitClient."""

    _cache: ClassVar[Dict[_Key, Tuple[BybitClient, float]]] = {}

    @classmethod
    def _make_key(
        cls,
        api_key: str,
        api_secret: str,
        demo: bool = False,
        testnet: bool = False,
    ) -> _Key:
        """
        Create a unique tuple for API credentials/configuration.

        demo/testnet must be consistent with all uses!
        """
        return (api_key, api_secret, demo, testnet)

    @classmethod
    def get_or_create(
        cls,
        api_key: str,
        api_secret: str,
        testnet: bool = False,
        demo: bool = False,
        recv_window: int = 5000,
        referral_id: str | None = None,
    ) -> BybitClient:
        """
        Get BybitClient from cache or create/cache it.

        Returns:
            Cached instance (possibly new).
        """
        key = cls._make_key(api_key, api_secret, demo, testnet)
        entry = cls._cache.get(key)
        if entry is not None:
            return entry[0]

        client = BybitClient(
            api_key=api_key,
            api_secret=api_secret,
            testnet=testnet,
            demo=demo,
            recv_window=recv_window,
            referral_id=referral_id,
        )
        cls.add(client, api_key, api_secret, demo=demo, testnet=testnet)
        return client
