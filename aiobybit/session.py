"""Session management module for Bybit API clients.

Usage:
    # At application startup
    BybitSessionManager.setup(max_connections=2000)

    # Use clients normally - they will share the session
    client1 = BybitHttpClient(api_key="...", api_secret="...")
    client2 = BybitHttpClient(api_key="...", api_secret="...")

    # At application shutdown
    await BybitSessionManager.close()
"""

import logging

import aiohttp

logger = logging.getLogger(__name__)


class BybitSessionManager:
    """Manager for shared aiohttp session with high-performance connection pool."""

    _session: aiohttp.ClientSession | None = None
    _max_connections: int = 2000

    @classmethod
    def setup(cls, max_connections: int = 2000) -> None:
        """Initialize shared session with high-performance connection pool.

        Call this once at application startup.

        Args:
            max_connections: Maximum number of connections in pool (default 2000)
        """
        if cls._session is not None and not cls._session.closed:
            logger.warning("Session already initialized - skipping setup")
            return

        logger.info(
            f"Initializing Bybit session with {max_connections} max connections"
        )
        cls._max_connections = max_connections
        connector = aiohttp.TCPConnector(
            limit=max_connections,
            limit_per_host=max_connections // 2,  # Distribute connections per host
            ttl_dns_cache=300,  # DNS cache 5 minutes
            use_dns_cache=True,
            keepalive_timeout=60,  # Keep-alive 60 seconds
            enable_cleanup_closed=True,
        )

        cls._session = aiohttp.ClientSession(
            connector=connector,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

    @classmethod
    def is_initialized(cls) -> bool:
        """Check if shared session is initialized and active."""
        return cls._session is not None and not cls._session.closed

    @classmethod
    def get_session(cls) -> aiohttp.ClientSession:
        """Get shared session. Setup must be called first."""
        if not cls.is_initialized():
            raise RuntimeError(
                "Session not initialized. Call BybitSessionManager.setup() first."
            )
        return cls._session  # type: ignore[return-value]

    @classmethod
    async def close(cls) -> None:
        """Close the shared session. Call this at application shutdown."""
        if cls._session and not cls._session.closed:
            logger.info("Closing Bybit shared session")
            await cls._session.close()
            cls._session = None
        else:
            logger.debug("Session already closed or not initialized")
