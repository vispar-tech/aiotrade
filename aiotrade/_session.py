"""Shared session management for trading API clients.

Example:
    # Initialize at application startup
    SharedSessionManager.setup(max_connections=2000)

    # Create trading clients; all share the same session
    client1 = HttpClient(api_key="...", api_secret="...")
    client2 = HttpClient(api_key="...", api_secret="...")

    # Cleanup at shutdown
    await SharedSessionManager.close()
"""

import logging

import aiohttp

logger = logging.getLogger("aiotrade.session")


class SharedSessionManager:
    """Manages a shared aiohttp session with a connection pool."""

    _session: aiohttp.ClientSession | None = None
    _max_connections: int = 2000

    @classmethod
    def setup(cls, max_connections: int = 2000) -> None:
        """
        Initialize the shared aiohttp session and connection pool.

        Call this once at application startup.

        Args:
            max_connections: Maximum total connections in pool (default 2000).
        """
        if cls._session is not None and not cls._session.closed:
            logger.warning("Shared session already initialized - skipping setup")
            return

        logger.info(
            "Initializing shared session (max connections: %d)", max_connections
        )
        cls._max_connections = max_connections

        connector = aiohttp.TCPConnector(
            limit=max_connections,
            limit_per_host=max_connections // 2,
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=60,
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
        """Return True if shared session is initialized and open."""
        return cls._session is not None and not cls._session.closed

    @classmethod
    def get_session(cls) -> aiohttp.ClientSession:
        """Return the active shared session; raise if not initialized."""
        if not cls.is_initialized():
            raise RuntimeError("SharedSessionManager.setup() must be called first.")
        return cls._session  # type: ignore[return-value]

    @classmethod
    async def close(cls) -> None:
        """
        Gracefully close the shared session.

        Call this at application shutdown.
        """
        if cls._session and not cls._session.closed:
            logger.info("Closing shared aiohttp session")
            await cls._session.close()
            cls._session = None
        else:
            logger.debug("Shared session already closed or not initialized")
