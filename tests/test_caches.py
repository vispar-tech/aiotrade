"""Tests for the BingxClientsCache implementation."""

import time

from aiotrade.caches._bingx import BingxClientsCache
from aiotrade.clients import BingxClient


async def test_bingx_cache_add_and_get_same_instance() -> None:
    """Test that adding and getting the same key returns the original instance."""
    BingxClientsCache.clear()
    api_key = "dummy_key"
    api_secret = "dummy_secret"  # noqa: S105
    demo = True
    recv_window = 1000

    client1 = BingxClient(
        api_key=api_key,
        api_secret=api_secret,
        demo=demo,
        recv_window=recv_window,
    )
    BingxClientsCache.add(client1, api_key, api_secret, demo=demo)
    client2 = BingxClientsCache.get(api_key, api_secret, demo)
    assert client2 is client1
    await client1.close()


def test_bingx_cache_get_none_if_absent() -> None:
    """Test that get returns None for missing entries."""
    BingxClientsCache.clear()
    api_key = "nope"
    api_secret = "none"  # noqa: S105
    demo = False
    result = BingxClientsCache.get(api_key, api_secret, demo)
    assert result is None


async def test_bingx_cache_get_or_create_returns_same_instance() -> None:
    """Test that get_or_create returns the same instance for the same key."""
    BingxClientsCache.clear()
    api_key = "the_key"
    api_secret = "the_secret"  # noqa: S105
    demo = False
    recv_window = 2500

    client1 = BingxClientsCache.get_or_create(
        api_key=api_key,
        api_secret=api_secret,
        demo=demo,
        recv_window=recv_window,
    )
    client2 = BingxClientsCache.get_or_create(
        api_key=api_key,
        api_secret=api_secret,
        demo=demo,
        recv_window=recv_window,
    )
    assert client1 is client2
    await client1.close()


async def test_bingx_cache_cleanup_expired_removes_old_entry() -> None:
    """Test that cleanup_expired removes old entries correctly."""
    BingxClientsCache.clear()
    api_key = "x"
    api_secret = "y"  # noqa: S105
    demo = True
    recv_window = 77

    BingxClientsCache.configure(lifetime_seconds=1)
    client = BingxClientsCache.get_or_create(
        api_key=api_key,
        api_secret=api_secret,
        demo=demo,
        recv_window=recv_window,
    )
    assert BingxClientsCache.size() == 1
    time.sleep(1.2)
    removed = BingxClientsCache.cleanup_expired()
    assert removed == 1
    assert BingxClientsCache.size() == 0
    await client.close()


async def test_bingx_cache_clear_removes_all() -> None:
    """Test that clear removes all cached instances."""
    BingxClientsCache.clear()
    a1, s1, d1, w1 = "a1", "s1", True, 111
    a2, s2, d2, w2 = "a2", "s2", False, 222
    c1 = BingxClientsCache.get_or_create(
        api_key=a1,
        api_secret=s1,
        demo=d1,
        recv_window=w1,
    )
    c2 = BingxClientsCache.get_or_create(
        api_key=a2,
        api_secret=s2,
        demo=d2,
        recv_window=w2,
    )
    assert BingxClientsCache.size() == 2
    BingxClientsCache.clear()
    assert BingxClientsCache.size() == 0
    await c1.close()
    await c2.close()


async def test_bingx_make_key_unique_for_demo_variants() -> None:
    """Test that cache keys are unique for 'demo' variants."""
    BingxClientsCache.clear()
    api_key = "keyy"
    api_secret = "secrr"  # noqa: S105
    recv_window = 1001

    c1 = BingxClientsCache.get_or_create(
        api_key=api_key,
        api_secret=api_secret,
        demo=True,
        recv_window=recv_window,
    )
    c2 = BingxClientsCache.get_or_create(
        api_key=api_key,
        api_secret=api_secret,
        demo=False,
        recv_window=recv_window,
    )
    assert c1 is not c2
    assert BingxClientsCache.size() == 2
    await c1.close()
    await c2.close()


def test_bingx_configure_lifetime_applies() -> None:
    """Test that configuring cache lifetime applies correctly."""
    BingxClientsCache.clear()
    new_lifetime = 123
    BingxClientsCache.configure(lifetime_seconds=new_lifetime)
    # Instead of accessing the private member, use a public interface if available.
    # If not, ensure this is allowed or ignore SLF001 for this line.
    lifetime = getattr(BingxClientsCache, "_lifetime_seconds", None)
    assert lifetime == new_lifetime
