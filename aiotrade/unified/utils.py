"""
Utility functions for symbol and asset handling in aiotrade unified module.

This module provides helper utilities to parse trading symbols and extract base assets,
primarily used for matching standardized symbol formats across different exchanges.

Exports:
    QUOTE_ASSETS_SORTED: List of known quote assets,
        sorted by decreasing length for matching.
    extract_symbol_asset(symbol: str) -> str: Extracts the base
        asset from an exchange symbol.
"""

from aiotrade import ExchangeLiteral

# Sorted list of quote assets (longest first for matching suffix)
QUOTE_ASSETS_SORTED = sorted(
    [
        "-USDT-SWAP",
        "-USDUSD",
        "-USDT",
        "-USDC",
        "-USD",
        "USDTM",
        "USDT",
        "USDC",
        "USDUSD",
        "USD",
    ],
    key=len,
    reverse=True,
)


def extract_symbol_asset(symbol: str) -> str:
    """
    Extract the base asset from a trading symbol.

    Examples:
        'BTCUSDT'          -> 'BTC'
        'ETH_USDT'         -> 'ETH'
        'BTC-USDT-SWAP'    -> 'BTC'
        'BTCUSDTM'         -> 'BTC'
        'ETHUSDC'          -> 'ETH'
        'BTCUSDUSD'        -> 'BTC'
        'BTC-USDC'         -> 'BTC'
        'XRP-USD'          -> 'XRP'
        'BTCUSDC'          -> 'BTC'
        'BTC-USDT'         -> 'BTC'
        'ETHUSDTM'         -> 'ETH'
        'BTCUSD'           -> 'BTC'
        'USDT'             -> 'USDT'
    """
    # If symbol is empty, or only whitespace, return as-is (after strip).
    symbol = symbol.strip()
    if not symbol:
        return symbol

    # If symbol is exactly a known quote asset, return as is
    if symbol in QUOTE_ASSETS_SORTED:
        return symbol

    # Look for matching suffix from the sorted list above
    for asset in QUOTE_ASSETS_SORTED:
        if symbol.endswith(asset):
            base = symbol[: -len(asset)]
            return base.rstrip("-_")  # remove trailing separator if present

    # If symbol contains '_' or '-', take left-part as base
    for sep in ("_", "-"):
        if sep in symbol:
            return symbol.split(sep)[0].rstrip("-_")

    # Fallback: just strip any trailing separators and return as is
    return symbol.rstrip("-_").lstrip()


def extract_quote_asset(symbol: str) -> str:
    """Extract the quote asset from a trading symbol.

    Args:
        symbol: The trading symbol to parse (e.g., "BTCUSDT", "ETH-USDC").

    Returns:
        The quote asset found in the symbol (USDT, USDC, or USD).
        Defaults to "USD" if no known quote asset is found.
    """
    for asset in ["USDT", "USDC", "USD"]:
        if asset in symbol:
            return asset
    return "USD"


def to_exchange_symbol(exchange: ExchangeLiteral, symbol: str) -> str:
    """Convert a symbol to the exchange-specific format."""
    asset = extract_symbol_asset(symbol)
    match exchange:
        case "bingx":
            return asset + "-USDT"
        case "bybit" | "bitget" | "binance":
            return asset + "USDT"
        case "okx":
            return asset + "-USDT-SWAP"
        case "kucoin":
            if asset == "BTC":
                return "XBTUSDTM"
            return asset + "USDTM"
        case "gate":
            return f"{asset}_USDT"
        case _:
            raise ValueError(f"Unsupported exchange: {exchange}")
