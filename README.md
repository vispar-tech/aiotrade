# aiotrade

[![PyPI version](https://badge.fury.io/py/aiotrade-sdk.svg)](https://pypi.org/project/aiotrade-sdk/) [![Python versions](https://img.shields.io/pypi/pyversions/aiotrade-sdk.svg)](https://pypi.org/project/aiotrade-sdk/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[![BingX](https://img.shields.io/badge/BingX-supported-blue?logo=bingx)](https://bingx.com) [![Bybit](https://img.shields.io/badge/Bybit-supported-gold?logo=bybit)](https://bybit.com) [![OKX](https://img.shields.io/badge/OKX-supported-black?logo=okx)](https://okx.com) [![Bitget](https://img.shields.io/badge/Bitget-supported-teal?logo=bitget)](https://www.bitget.com/) [![Binance](https://img.shields.io/badge/Binance-supported-yellow?logo=binance)](https://www.binance.com/) [![KuCoin](https://img.shields.io/badge/KuCoin-supported-lightgreen?logo=kucoin)](https://www.kucoin.com/)

High-performance async trading API client for Python supporting BingX, Bybit, OKX, Bitget, Binance and Kucoin exchanges with intelligent session and cache management.

## Architecture

The library uses a sophisticated architecture for optimal performance:

### Session Management

- **Shared Session**: `SharedSessionManager` creates a single aiohttp session with high-performance connection pooling
- **Individual Sessions**: Clients automatically create individual sessions if shared session isn't initialized
- **Connection Pooling**: Up to 2000 concurrent connections with smart distribution per host

### Client Caching

- **TTL Cache**: `BingxClientsCache`, `BybitClientsCache` and etc. cache client instances with 10-minute lifetime
- **Lock-Free**: No blocking operations for maximum performance
- **Lazy Cleanup**: Expired entries removed on access, not proactively

#### Implemented methods

1. **Use Shared Session** for applications creating many clients
2. **Enable Caching** for repeated API credential usage
3. **Configure Connection Limits** based on your throughput needs
4. **Use Background Cleanup** for long-running applications

```text
BybitClient methods (42):
 batch_cancel_order                     get_server_time
 batch_place_order                      get_smp_group_id
 batch_set_collateral_coin              get_trade_behaviour_setting
 cancel_all_orders                      get_transaction_log
 cancel_order                           get_transferable_amount
 get_account_info                       get_wallet_balance
 get_account_instruments_info           manual_borrow
 get_api_key_info                       manual_repay
 get_borrow_history                     manual_repay_without_asset_conversion
 get_closed_pnl                         place_order
 get_coin_greeks                        repay_liability
 get_collateral_info                    reset_mmp
 get_dcp_info                           set_collateral_coin
 get_fee_rate                           set_leverage
 get_instruments_info                   set_limit_price_behaviour
 get_kline                              set_margin_mode
 get_mmp_state                          set_mmp
 get_open_and_closed_orders             set_spot_hedging
 get_order_history                      set_trading_stop
 get_position_info                      switch_position_mode
 get_risk_limit                         upgrade_to_unified_account_pro

BingxClient methods (47):
 cancel_all_spot_open_orders                get_spot_profit_overview
 cancel_all_swap_open_orders                get_spot_symbols
 cancel_spot_batch_orders                   get_spot_trade_details
 cancel_swap_batch_orders                   get_swap_account_balance
 change_swap_margin_type                    get_swap_contracts
 close_perpetual_trader_position_by_order   get_swap_full_orders
 close_swap_position                        get_swap_klines
 get_account_asset_overview                 get_swap_leverage_and_available_positions
 get_account_uid                            get_swap_margin_type
 get_api_permissions                        get_swap_open_orders
 get_perpetual_copy_trading_pairs           get_swap_order_details
 get_perpetual_current_trader_order         get_swap_order_history
 get_perpetual_personal_trading_overview    get_swap_position_history
 get_perpetual_profit_details               get_swap_position_mode
 get_perpetual_profit_overview              get_swap_positions
 get_server_time                            place_spot_order
 get_spot_account_assets                    place_swap_batch_orders
 get_spot_history_orders                    place_swap_order
 get_spot_klines                            sell_spot_asset_by_order
 get_spot_open_orders                       set_perpetual_commission_rate
 get_spot_order_details                     set_perpetual_trader_tpsl_by_order
 get_spot_order_history                     set_swap_leverage
 get_spot_personal_trading_overview         set_swap_position_mode
 get_spot_profit_details

OkxClient methods (22):
 batch_place_order        get_leverage_info
 cancel_algo_orders       get_order
 cancel_batch_orders      get_orders_history
 close_position           get_orders_pending
 get_account_config       get_position_tiers
 get_algo_order           get_positions
 get_algo_orders_history  get_positions_history
 get_algo_orders_pending  place_algo_order
 get_balance              set_isolated_mode
 get_funding_balance      set_leverage
 get_instruments          set_position_mode

BitgetClient methods (34):
 batch_cancel_futures_orders  get_order_detail
 batch_cancel_spot_orders     get_pending_orders
 batch_place_futures_orders   get_pending_trigger_orders
 batch_place_spot_orders      get_server_time
 cancel_all_futures_orders    get_single_account
 cancel_order                 get_spot_history_orders
 cancel_order_by_symbol       get_symbol_info
 cancel_trigger_orders        get_trade_rate
 flash_close_position         get_unfilled_orders
 get_account_assets           place_futures_order
 get_account_info             place_spot_order
 get_account_list             place_tpsl_plan_order
 get_all_positions            place_trigger_order
 get_contract_config          set_asset_mode
 get_futures_history_orders   set_leverage
 get_historical_position      set_margin_mode
 get_isolated_symbols         set_position_mode

BinanceClient methods (34):
 cancel_algo_order            get_all_orders
 cancel_all_algo_open_orders  get_api_key_permissions
 cancel_all_open_orders       get_exchange_info
 cancel_batch_orders          get_income_history
 cancel_order                 get_klines
 change_leverage              get_multi_assets_mode
 change_margin_type           get_open_algo_orders
 change_multi_assets_mode     get_open_order
 change_position_mode         get_open_orders
 create_algo_order            get_order
 create_batch_orders          get_position_info
 create_order                 get_position_info_v3
 get_account_balance          get_position_mode
 get_account_config           get_spot_account_info
 get_account_info             get_spot_all_orders
 get_algo_order               get_spot_open_orders
 get_all_algo_orders          get_symbol_config

KuCoinClient methods (32):
 add_order                       get_margin_mode
 add_order_test                  get_order_by_client_oid
 add_tp_sl_order                 get_order_by_order_id
 batch_add_orders                get_order_list
 batch_cancel_orders             get_position_details
 batch_switch_margin_mode        get_position_mode
 cancel_all_orders               get_positions
 cancel_all_stop_orders          get_positions_history
 cancel_order_by_client_oid      get_recent_closed_orders
 cancel_order_by_id              get_recent_trade_history
 get_all_symbols                 get_server_time
 get_all_tickers                 get_service_status
 get_api_key_info                get_stop_orders
 get_futures_account             get_trade_history
 get_isolated_margin_risk_limit  switch_margin_mode
 get_klines                      switch_position_mode
```

## Installation

```bash
poetry add aiotrade-sdk
```

## Quick Start

### Option 1: Shared Session (Recommended for Production)

```python
from aiotrade import SharedSessionManager, BybitClient

# Initialize shared session at startup (once per application)
SharedSessionManager.setup(max_connections=2000)

# Create Bybit client - will use the shared session
bybit_client = BybitClient(api_key="bybit_key", api_secret="bybit_secret", testnet=True)

try:
    # Use client for API calls
    bybit_tickers = await bybit_client.get_tickers(category="spot")
finally:
    # Close shared session at shutdown
    await SharedSessionManager.close()
```

### Option 2: Individual Bybit Session

```python
from aiotrade import BybitClient

# Bybit client with individual session
async with BybitClient(api_key="your_key", api_secret="your_secret", testnet=True) as client:
    tickers = await client.get_tickers(category="spot")
    print(f"Bybit tickers: {tickers}")
```

### Option 3: Cached Bybit Client

```python
from aiotrade import BybitClientsCache

# Get cached Bybit client (creates new if doesn't exist)
bybit_client = BybitClientsCache.get_or_create(
    api_key="your_key",
    api_secret="your_secret",
    testnet=True
)

# Use cached client (session management is automatic)
async with bybit_client:
    tickers = await bybit_client.get_tickers(category="spot")

# Same parameters return the same cached instance
cached_bybit = BybitClientsCache.get_or_create(
    api_key="your_key",
    api_secret="your_secret",
    testnet=True
)
assert bybit_client is cached_bybit  # True
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
OkxClientsCache.configure(lifetime_seconds=1800)    # 30 minutes
BitgetClientsCache.configure(lifetime_seconds=1800) # 30 minutes

# Start background cleanup
bingx_cleanup = BingxClientsCache.create_cleanup_task(interval_seconds=300)
bybit_cleanup = BybitClientsCache.create_cleanup_task(interval_seconds=300)
okx_cleanup = OkxClientsCache.create_cleanup_task(interval_seconds=300)
bitget_cleanup = BitgetClientsCache.create_cleanup_task(interval_seconds=300)

# Manual cleanup
bingx_removed = BingxClientsCache.cleanup_expired()
bybit_removed = BybitClientsCache.cleanup_expired()
okx_removed = OkxClientsCache.cleanup_expired()
bitget_removed = BitgetClientsCache.cleanup_expired()
```

## Requirements

- Python >= 3.12
- aiohttp
- High-performance connection pooling for production use
