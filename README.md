# aiobybit

Async Bybit API client for Python.

## Installation

This is a private package. Install using Poetry with GitLab link:

```bash
poetry add aiobybit
```

## Quick Start

```python
from aiobybit import BybitClient

client = BybitClient(api_key="your_api_key", api_secret="your_api_secret")

# Use the client for trading operations
```

## Client Caching

The package includes a built-in client cache for efficient HTTP client management:

```python
from aiobybit import BybitClientCache

# Get or create cached client
client = BybitClientCache.get_or_create(
    api_key="your_api_key",
    api_secret="your_api_secret",
    testnet=True,
    demo=False
)

# Cache is automatic - same parameters return the same client instance
```

Cache features:

- Automatic client reuse by API credentials
- Configurable lifetime (default 10 minutes)
- Background cleanup task for expired entries
- Singleton pattern - shared across the application

## Features

- Async/await support
- HTTP client caching with automatic management
- Accounts management
- Market data access
- Order management
- Positions handling

## Requirements

- Python >= 3.12
