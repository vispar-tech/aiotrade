"""Shared session management for trading API clients.

Example:
    # Initialize at application startup
    SharedSessionManager.setup(max_connections=2000)

    # Or, with global proxy:
    SharedSessionManager.setup(max_connections=2000, proxy="http://localhost:7890")

    # Create trading clients; all share the same session
    client1 = HttpClient(api_key="...", api_secret="...")
    client2 = HttpClient(api_key="...", api_secret="...")

    # Cleanup at shutdown
    await SharedSessionManager.close()
"""

import logging
from urllib.parse import urlparse

import aiohttp
from aiohttp_socks import ProxyConnector

logger = logging.getLogger("aiotrade.session")


def _mask_proxy_url(proxy: str | None) -> str | None:
    if not proxy:
        return None
    try:
        parsed = urlparse(proxy)
        netloc = parsed.hostname or ""
        if parsed.port:
            netloc += f":{parsed.port}"
        masked = f"{parsed.scheme}://"
        if parsed.username or parsed.password:
            masked += "****:****@"
        masked += netloc
        if parsed.path:
            masked += parsed.path
        if parsed.params:
            masked += f";{parsed.params}"
        if parsed.query:
            masked += f"?{parsed.query}"
        if parsed.fragment:
            masked += f"#{parsed.fragment}"
        return masked
    except Exception:
        return "****"


class SharedSessionManager:
    """Manages a shared aiohttp session with a connection pool."""

    _session: aiohttp.ClientSession | None = None
    _max_connections: int = 2000
    _proxy: str | None = None

    @classmethod
    def setup(cls, max_connections: int = 2000, proxy: str | None = None) -> None:
        """
        Initialize the shared aiohttp session and connection pool.

        Call this once at application startup.

        Args:
            max_connections: Maximum total connections in pool (default 2000).
            proxy: Optional. Proxy URL for all outgoing requests (http/https/socks).
        """
        if cls._session is not None and not cls._session.closed:
            logger.warning("Shared session already initialized - skipping setup")
            return

        masked_proxy = _mask_proxy_url(proxy)
        logger.info(
            "Initializing shared session (max connections: %d, proxy: %s)",
            max_connections,
            masked_proxy,
        )
        cls._max_connections = max_connections
        cls._proxy = proxy
        connector: aiohttp.BaseConnector

        if proxy is not None:
            connector = ProxyConnector.from_url(
                proxy,
                limit=max_connections,
                limit_per_host=max_connections // 2,
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=60,
                enable_cleanup_closed=True,
            )
        else:
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
            timeout=aiohttp.ClientTimeout(total=60),
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
    def get_proxy(cls) -> str | None:
        """Get the global proxy URL if set, otherwise None."""
        return cls._proxy

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
            cls._proxy = None
        else:
            logger.debug("Shared session already closed or not initialized")
