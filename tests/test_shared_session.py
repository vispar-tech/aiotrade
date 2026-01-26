"""Test that HTTP clients use SharedSessionManager from aiotrade._session."""

import aiohttp

from aiotrade._session import SharedSessionManager
from aiotrade.clients import BingxClient, BybitClient


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
    ):
        # All clients should use the same aiohttp session internally.
        # We'll check via the private _session, for test purposes only
        session_client1 = getattr(client1, "_session", None)
        session_client2 = getattr(client2, "_session", None)
        session_client3 = getattr(client3, "_session", None)
        session_client4 = getattr(client4, "_session", None)
        assert session_client1 is session1
        assert session_client2 is session1
        assert session_client3 is session1
        assert session_client4 is session1

        # Check that all clients report they are using the shared session.
        assert client1.uses_shared_session is True
        assert client2.uses_shared_session is True
        assert client3.uses_shared_session is True
        assert client4.uses_shared_session is True

    # After all clients closed, shared session is still open unless we close it
    assert SharedSessionManager.is_initialized()
    await SharedSessionManager.close()
    assert not SharedSessionManager.is_initialized()
