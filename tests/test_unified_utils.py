"""Unit tests for aiotrade.unified.utils with proper type annotations."""

import logging
from collections.abc import Iterator, Sequence
from typing import Any, TypeAliasType, cast, get_args

import pytest

from aiotrade import ExchangeLiteral
from aiotrade.unified.utils import (
    extract_quote_asset,
    extract_symbol_asset,
    to_exchange_symbol,
)


def _get_literal_vals(alias: TypeAliasType) -> frozenset[Any]:
    def val(alias: TypeAliasType) -> Any:
        return alias.__value__

    def args(alias: TypeAliasType) -> tuple[Any, ...]:
        return get_args(val(alias))

    def resolve(
        alias: TypeAliasType | tuple[Any, ...] | Any,
    ) -> Iterator[Any]:
        if isinstance(alias, TypeAliasType):
            yield from resolve(args(alias))
            return
        if isinstance(alias, tuple):
            t_seq = cast(Sequence[Any], alias)
            for element in t_seq:
                yield from resolve(element)
            return
        yield alias

    return frozenset(resolve(alias))


def _get_all_exchange_literals() -> frozenset[ExchangeLiteral]:
    """Return all literal (string) values of the ExchangeLiteral type."""
    return _get_literal_vals(ExchangeLiteral)


@pytest.mark.parametrize(
    "symbol,expected",
    [
        ("BTCUSDT", "BTC"),
        ("ETH_USDT", "ETH"),
        ("BTC-USDT-SWAP", "BTC"),
        ("BTCUSDTM", "BTC"),
        ("ETHUSDC", "ETH"),
        ("BTCUSDUSD", "BTC"),
        ("BTC-USDC", "BTC"),
        ("XRP-USD", "XRP"),
        ("BTCUSDC", "BTC"),
        ("BTC-USDT", "BTC"),
        ("ETHUSDTM", "ETH"),
        ("BTCUSD", "BTC"),
        ("BTC", "BTC"),
        ("FOO-BAR-USD", "FOO-BAR"),
        ("TEST_PAIR", "TEST"),
        ("ABC_XYZ", "ABC"),
        ("DOGEUSD", "DOGE"),
        ("SOL-USDT", "SOL"),
        ("DOGE", "DOGE"),
        ("LTC__USDT", "LTC"),
        ("BNB_USDT", "BNB"),
        ("BNBUSDT", "BNB"),
        ("ADAUSDC", "ADA"),
        ("XRP_USDUSD", "XRP"),
        ("LTC-USDUSD", "LTC"),
        ("TRX-USD", "TRX"),
    ],
)
def test_extract_symbol_asset(symbol: str, expected: str) -> None:
    """Test extraction of the base asset from a symbol string."""
    assert extract_symbol_asset(symbol) == expected


@pytest.mark.parametrize(
    "symbol,expected",
    [
        ("BTCUSDT", "USDT"),
        ("ETH_USDT", "USDT"),
        ("BTC-USDT-SWAP", "USDT"),
        ("BTCUSDTM", "USDT"),
        ("ETHUSDC", "USDC"),
        ("BTCUSDUSD", "USD"),
        ("BTC-USDC", "USDC"),
        ("XRP-USD", "USD"),
        ("BTCUSDC", "USDC"),
        ("BTC-USDT", "USDT"),
        ("ETHUSDTM", "USDT"),
        ("BTCUSD", "USD"),
        ("BTC", "USD"),
        ("FOO-BAR-USD", "USD"),
        ("ADAUSDC", "USDC"),
        ("XRP_USDUSD", "USD"),
        ("LTC-USDUSD", "USD"),
        ("TRX-USD", "USD"),
        ("DOGE", "USD"),
        ("ETHXYZ", "USD"),
    ],
)
def test_extract_quote_asset(symbol: str, expected: str) -> None:
    """Test extraction of the quote asset from a symbol string."""
    assert extract_quote_asset(symbol) == expected


@pytest.mark.parametrize(
    "exchange,symbol,expected",
    [
        ("bingx", "BTCUSDT", "BTC-USDT"),
        ("bingx", "ETH_USDT", "ETH-USDT"),
        ("bingx", "ETHUSDC", "ETH-USDT"),
        ("bingx", "BTC-USDT-SWAP", "BTC-USDT"),
        ("bybit", "BTCUSDT", "BTCUSDT"),
        ("bybit", "ETHUSDTM", "ETHUSDT"),
        ("bitget", "BTCUSDC", "BTCUSDT"),
        ("binance", "BTC-USDT", "BTCUSDT"),
        ("okx", "BTCUSDT", "BTC-USDT-SWAP"),
        ("okx", "BTCUSDTM", "BTC-USDT-SWAP"),
        ("okx", "BTCUSD", "BTC-USDT-SWAP"),
        ("kucoin", "BTCUSDT", "XBTUSDTM"),
        ("kucoin", "ETHUSDT", "ETHUSDTM"),
        ("kucoin", "DOGEUSDT", "DOGEUSDTM"),
        ("gate", "BTCUSDT", "BTC_USDT"),
        ("gate", "ETH-USDT-SWAP", "ETH_USDT"),
    ],
)
def test_to_exchange_symbol(
    exchange: ExchangeLiteral, symbol: str, expected: str
) -> None:
    """Test conversion of symbol into exchange-specific format."""
    # Remove spaces from exchange param (shouldn't have them, defensive)
    result = to_exchange_symbol(exchange, symbol)
    assert result == expected


def test_extract_symbol_asset_edge_cases() -> None:
    """Test edge cases for extract_symbol_asset."""
    # symbol that is just a quote asset
    assert extract_symbol_asset("USDT") == "USDT"
    # empty string
    assert extract_symbol_asset("") == ""
    # symbol with trailing separator
    assert extract_symbol_asset("FOO-USD-") == "FOO"
    # symbol with leading separator
    assert extract_symbol_asset("-BTCUSDT") == "-BTC"


def test_extract_quote_asset_defaults() -> None:
    """Test extract_quote_asset falls back to 'USD' as default."""
    # Should fallback to "USD" if no match
    assert extract_quote_asset("FOO123") == "USD"
    assert extract_quote_asset("") == "USD"


def test_to_exchange_symbol_covers_all_exchange_types() -> None:
    """Test that to_exchange_symbol supports all possible Exchange values."""
    test_symbol = "BTCUSDT"
    exchanges = _get_all_exchange_literals()
    logging.info("All exchanges: %s", exchanges)
    assert len(exchanges) > 0
    for exchange in exchanges:
        result = to_exchange_symbol(exchange, test_symbol)
        assert isinstance(result, str)
        assert result  # should not return an empty string
