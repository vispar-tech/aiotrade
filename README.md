# aiotrade

[![PyPI version](https://badge.fury.io/py/aiotrade-sdk.svg)](https://pypi.org/project/aiotrade-sdk/) [![Python versions](https://img.shields.io/pypi/pyversions/aiotrade-sdk.svg)](https://pypi.org/project/aiotrade-sdk/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[![CI](https://github.com/vispar-tech/aiotrade/actions/workflows/ci.yml/badge.svg)](https://github.com/vispar-tech/aiotrade/actions/workflows/ci.yml) [![Release](https://github.com/vispar-tech/aiotrade/actions/workflows/release.yml/badge.svg)](https://github.com/vispar-tech/aiotrade/actions/workflows/release.yml)

High-performance async trading API client for Python supporting BingX and Bybit exchanges with intelligent session and cache management.

## Architecture

The library uses a sophisticated architecture for optimal performance:

### Session Management

- **Shared Session**: `SharedSessionManager` creates a single aiohttp session with high-performance connection pooling
- **Individual Sessions**: Clients automatically create individual sessions if shared session isn't initialized
- **Connection Pooling**: Up to 2000 concurrent connections with smart distribution per host

### Client Caching

- **TTL Cache**: `BingxClientsCache` and `BybitClientsCache` cache client instances with 10-minute lifetime
- **Lock-Free**: No blocking operations for maximum performance
- **Lazy Cleanup**: Expired entries removed on access, not proactively

#### Implemented methods

```text
BybitClient methods (18):
    batch_cancel_order          get_order_history
    batch_place_order           get_position_info
    cancel_all_orders           get_server_time
    cancel_order                get_wallet_balance
    get_account_info            place_order
    get_closed_pnl              set_leverage
    get_instruments_info        set_margin_mode
    get_kline                   set_trading_stop
    get_open_and_closed_orders  switch_position_mode

BingxClient methods (30):
    cancel_all_spot_open_orders                get_spot_trade_details
    cancel_all_swap_open_orders                get_swap_account_balance
    cancel_spot_batch_orders                   get_swap_contracts
    cancel_swap_batch_orders                   get_swap_klines
    change_swap_margin_type                    get_swap_leverage_and_available_positions
    close_swap_position                        get_swap_margin_type
    get_account_asset_overview                 get_swap_open_orders
    get_api_permissions                        get_swap_order_details
    get_server_time                            get_swap_order_history
    get_spot_account_assets                    get_swap_position_history
    get_spot_klines                            get_swap_position_mode
    get_spot_open_orders                       get_swap_positions
    get_spot_order_details                     place_swap_order
    get_spot_order_history                     set_swap_leverage
    get_spot_symbols_like                      set_swap_position_mode
```

## Installation

```bash
poetry add aiotrade-sdk
```

## Quick Start

### Option 1: Shared Session (Recommended for Production)

```python
from aiotrade import SharedSessionManager, BingxClient, BybitClient

# Initialize shared session at startup (once per application)
SharedSessionManager.setup(max_connections=2000)

# Create clients for different exchanges - they automatically use the shared session
bingx_client = BingxClient(api_key="bingx_key", api_secret="bingx_secret", demo=True)
bybit_client = BybitClient(api_key="bybit_key", api_secret="bybit_secret", testnet=True)

try:
    # Use clients for API calls
    bingx_assets = await bingx_client.get_spot_account_assets()
    bybit_tickers = await bybit_client.get_tickers(category="spot")
finally:
    # Close shared session at shutdown
    await SharedSessionManager.close()
```

### Option 2: Individual Sessions

```python
from aiotrade import BingxClient, BybitClient

# BingX client with individual session
async with BingxClient(api_key="your_key", api_secret="your_secret", demo=True) as client:
    assets = await client.get_spot_account_assets()
    print(f"BingX assets: {assets}")

# Bybit client with individual session
async with BybitClient(api_key="your_key", api_secret="your_secret", testnet=True) as client:
    tickers = await client.get_tickers(category="spot")
    print(f"Bybit tickers: {tickers}")
```

### Option 3: Cached Clients

```python
from aiotrade import BingxClientsCache, BybitClientsCache

# Get cached BingX client (creates new if doesn't exist)
bingx_client = BingxClientsCache.get_or_create(
    api_key="your_key",
    api_secret="your_secret",
    demo=True
)

# Get cached Bybit client
bybit_client = BybitClientsCache.get_or_create(
    api_key="your_key",
    api_secret="your_secret",
    testnet=True
)

# Use clients (session management is automatic)
async with bingx_client:
    assets = await bingx_client.get_spot_account_assets()

async with bybit_client:
    tickers = await bybit_client.get_tickers(category="spot")

# Same parameters return the same cached instance
cached_bingx = BingxClientsCache.get_or_create(
    api_key="your_key",
    api_secret="your_secret",
    demo=True
)
assert bingx_client is cached_bingx  # True
```

## Session Behavior

| Scenario                              | Session Type              | When Used              |
| ------------------------------------- | ------------------------- | ---------------------- |
| `SharedSessionManager.setup()` called | Shared session            | All clients            |
| No shared session initialized         | Individual session        | Each client            |
| Cached clients                        | Depends on initialization | Cached per credentials |

## Cache Features

- **Automatic TTL**: 10 minutes default, configurable
- **Memory Safe**: Prevents client accumulation
- **High Performance**: Lock-free operations
- **Background Cleanup**: Optional periodic cleanup task

```python
# Configure cache lifetime for each exchange
BingxClientsCache.configure(lifetime_seconds=1800)  # 30 minutes
BybitClientsCache.configure(lifetime_seconds=1800)  # 30 minutes

# Start background cleanup
bingx_cleanup = BingxClientsCache.create_cleanup_task(interval_seconds=300)
bybit_cleanup = BybitClientsCache.create_cleanup_task(interval_seconds=300)

# Manual cleanup
bingx_removed = BingxClientsCache.cleanup_expired()
bybit_removed = BybitClientsCache.cleanup_expired()
```

## API Methods

### BingX Client Methods

```python
from aiotrade import BingxClient

client = BingxClient(api_key="your_key", api_secret="your_secret", demo=True)

# Market data
server_time = await client.get_server_time()

# Spot trading
assets = await client.get_spot_account_assets()
tickers = await client.get_spot_tickers()

# Swap trading (perpetual futures)
await client.place_swap_order({
    "symbol": "BTC-USDT",
    "side": "BUY",
    "positionSide": "BOTH",
    "type": "MARKET",
    "quantity": 0.001
})
```

### Bybit Client Methods

```python
from aiotrade import BybitClient

client = BybitClient(api_key="your_key", api_secret="your_secret", testnet=True)

# Market data
server_time = await client.get_server_time()
tickers = await client.get_tickers(category="spot")
klines = await client.get_kline("BTCUSDT", "1h", category="linear")

# Trading
await client.place_order({
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
