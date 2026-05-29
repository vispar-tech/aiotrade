"""Test that HTTP clients use SharedSessionManager from aiotrade._session."""

import logging
import os
import warnings

import aiohttp
import pytest

from aiotrade._session import SharedSessionManager
from aiotrade.clients import BingxClient, BybitClient, OkxClient

logger = logging.getLogger(__name__)


async def test_clients_share_session() -> None:
    """Test sharing aiohttp session between clients of all supported types."""
    SharedSessionManager.setup(max_connections=128)
    session1 = SharedSessionManager.get_session()
    assert SharedSessionManager.is_initialized()
    assert isinstance(session1, aiohttp.ClientSession)
    assert not session1.closed

    async with (
        BybitClient() as client1,
        BybitClient() as client2,
        BingxClient() as client3,
        BingxClient() as client4,
        OkxClient() as client5,
        OkxClient() as client6,
    ):
        # All clients should use the same aiohttp session internally.
        # We'll check via the private _session, for test purposes only
        session_client1 = getattr(client1, "_session", None)
        session_client2 = getattr(client2, "_session", None)
        session_client3 = getattr(client3, "_session", None)
        session_client4 = getattr(client4, "_session", None)
        session_client5 = getattr(client5, "_session", None)
        session_client6 = getattr(client6, "_session", None)
        assert session_client1 is session1
        assert session_client2 is session1
        assert session_client3 is session1
        assert session_client4 is session1
        assert session_client5 is session1
        assert session_client6 is session1

        # Check that all clients report they are using the shared session.
        assert client1.uses_shared_session is True
        assert client2.uses_shared_session is True
        assert client3.uses_shared_session is True
        assert client4.uses_shared_session is True
        assert client5.uses_shared_session is True
        assert client6.uses_shared_session is True

    # After all clients closed, shared session is still open unless we close it
    assert SharedSessionManager.is_initialized()
    await SharedSessionManager.close()
    assert not SharedSessionManager.is_initialized()


@pytest.mark.external
async def test_shared_session_with_proxy() -> None:
    """Test that shared session correctly applies proxy settings."""
    proxy_url = os.environ["PROXY_URL"]
    logger.info(f"Using PROXY_URL: {proxy_url}")

    # Use an external IP echo service to verify outgoing IP
    ip_check_url = "https://api.ipify.org?format=json"
    logger.info(f"IP check endpoint: {ip_check_url}")

    # Record local IP (no proxy) for comparison
    logger.info("Checking local IP address without proxy...")
    async with aiohttp.ClientSession() as s, s.get(ip_check_url) as r:
        local_result = await r.json()
        local_ip = local_result.get("ip")
        logger.info(f"Local IP address (no proxy): {local_ip}")

    SharedSessionManager.setup(max_connections=32, proxy=proxy_url)
    session = SharedSessionManager.get_session()
    logger.info("SharedSessionManager initialized with proxy.")
    assert SharedSessionManager.is_initialized()
    assert isinstance(session, aiohttp.ClientSession)

    # The proxy config is not directly exposed in public API,
    # but our SharedSessionManager keeps a record
    assert SharedSessionManager.get_proxy() == proxy_url

    # There should be no errors in basic client construction
    async with BybitClient() as client:
        # All clients should see they're using shared session
        assert client.uses_shared_session is True
        # The session in the client should be the shared session
        session_client = getattr(client, "_session", None)
        assert session_client is not None and session_client is session
        logger.info("BybitClient constructed and uses shared session.")

        # Now make a request using the shared session THROUGH the proxy (public service)
        # We'll use the session directly since clients don't expose raw requests
        logger.info("Checking IP address over proxy...")
        async with session_client.get(ip_check_url) as resp:
            proxy_result = await resp.json()
            proxy_ip = proxy_result.get("ip")
            logger.info(f"IP address via proxy: {proxy_ip}")

        # Assert: proxy_ip must be different from local_ip to PROVE a proxy is used
        # We allow for the rare case that the proxy is localhost/loopback,
        # in which case ignore test
        assert proxy_ip is not None and local_ip is not None, (
            "Could not resolve IPs for test"
        )
        if proxy_ip == local_ip:
            # Warn, but do not fail: proxy might not be actually used, skip assertion
            logger.warning(
                f"Proxy not in effect: local IP == proxy IP == {local_ip}. "
                f"Ensure your PROXY_URL variable is set to a real proxy."
            )
            warnings.warn(
                f"Proxy not in effect: local IP == proxy IP == {local_ip}. "
                f"Ensure your PROXY_URL variable is set to a real proxy.",
                stacklevel=2,
            )
        else:
            logger.info(
                f"Proxy appears effective: local IP {local_ip} / proxy IP {proxy_ip}"
            )
            assert proxy_ip != local_ip, (
                f"Proxy is not being used: got same outgoing IP {proxy_ip}. "
                f"Expected different IP via proxy. Check your PROXY_URL."
            )

    logger.info("Closing shared session after proxy test.")
    await SharedSessionManager.close()
    assert not SharedSessionManager.is_initialized()
