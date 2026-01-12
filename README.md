# aiobybit

High-performance async Bybit API client for Python with intelligent session and cache management.

## Architecture

The library uses a sophisticated architecture for optimal performance:

### Session Management

- **Shared Session**: `BybitSessionManager` creates a single aiohttp session with high-performance connection pooling
- **Individual Sessions**: Clients automatically create individual sessions if shared session isn't initialized
- **Connection Pooling**: Up to 2000 concurrent connections with smart distribution per host

### Client Caching

- **TTL Cache**: `BybitClientCache` caches client instances with 10-minute lifetime
- **Lock-Free**: No blocking operations for maximum performance
- **Lazy Cleanup**: Expired entries removed on access, not proactively

## Installation

```bash
poetry add aiobybit
```

## Quick Start

### Option 1: Shared Session (Recommended for Production)

```python
from aiobybit import BybitSessionManager, BybitHttpClient

# Initialize shared session at startup (once per application)
BybitSessionManager.setup(max_connections=2000)

# Create clients - they automatically use the shared session
client1 = BybitHttpClient(api_key="key1", api_secret="secret1")
client2 = BybitHttpClient(api_key="key2", api_secret="secret2")

try:
    # Use clients for API calls
    result1 = await client1.get("/v5/market/tickers", {"category": "spot"})
    result2 = await client2.get("/v5/market/tickers", {"category": "linear"})
finally:
    # Close shared session at shutdown
    await BybitSessionManager.close()
```

### Option 2: Individual Sessions

```python
from aiobybit import BybitHttpClient

# Client creates its own session automatically
async with BybitHttpClient(api_key="your_key", api_secret="your_secret") as client:
    result = await client.get("/v5/market/tickers", {"category": "spot"})
    print(result)
```

### Option 3: Cached Clients

```python
from aiobybit import BybitClientCache

# Get cached client (creates new if doesn't exist)
client = BybitClientCache.get_or_create(
    api_key="your_key",
    api_secret="your_secret",
    testnet=True
)

# Use client (session management is automatic)
async with client:
    result = await client.get("/v5/market/tickers", {"category": "spot"})

# Same parameters return the same cached instance
cached_client = BybitClientCache.get_or_create(
    api_key="your_key",
    api_secret="your_secret",
    testnet=True
)
assert client is cached_client  # True
```

## Session Behavior

| Scenario                             | Session Type              | When Used              |
| ------------------------------------ | ------------------------- | ---------------------- |
| `BybitSessionManager.setup()` called | Shared session            | All clients            |
| No shared session initialized        | Individual session        | Each client            |
| Cached clients                       | Depends on initialization | Cached per credentials |

## Cache Features

- **Automatic TTL**: 10 minutes default, configurable
- **Memory Safe**: Prevents client accumulation
- **High Performance**: Lock-free operations
- **Background Cleanup**: Optional periodic cleanup task

```python
# Configure cache lifetime
BybitClientCache.configure(lifetime_seconds=1800)  # 30 minutes

# Start background cleanup
cleanup_task = BybitClientCache.create_cleanup_task(interval_seconds=300)

# Manual cleanup
removed_count = BybitClientCache.cleanup_expired()
```

## API Methods

All HTTP methods supported with automatic authentication:

```python
# GET request
result = await client.get("/v5/market/tickers", {"category": "spot"})

# POST request
result = await client.post("/v5/order/create", {
    "category": "linear",
    "symbol": "BTCUSDT",
    "side": "Buy",
    "orderType": "Market",
    "qty": "0.001"
})
```

## Requirements

- Python >= 3.12
- aiohttp
- High-performance connection pooling for production use

## Performance Tips

1. **Use Shared Session** for applications creating many clients
2. **Enable Caching** for repeated API credential usage
3. **Configure Connection Limits** based on your throughput needs
4. **Use Background Cleanup** for long-running applications
