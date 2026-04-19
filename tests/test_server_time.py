"""Test get_server_time endpoint for BybitClient, BingxClient, and others."""

import logging

import pytest

from aiotrade.clients import (  # Add imports for other clients as available
    BingxClient,
    BybitClient,
    KuCoinClient,
    OkxClient,
)


@pytest.mark.external
async def test_bybit_get_server_time() -> None:
    """Test retrieving Bybit server time and validate its structure."""
    async with BybitClient() as client:
        server_time = await client.get_server_time()
        logging.info("Bybit server time response: %r", server_time)

        assert isinstance(server_time, dict), (
            "Server time response should be a dictionary"
        )

        assert server_time.get("retCode") == 0
        assert server_time.get("retMsg") == "OK"
        assert isinstance(server_time.get("result"), dict)
        result = server_time["result"]
        assert "timeSecond" in result and isinstance(result["timeSecond"], str)
        assert "timeNano" in result and isinstance(result["timeNano"], str)
        assert isinstance(server_time.get("retExtInfo"), dict)
        assert isinstance(server_time.get("time"), int)


@pytest.mark.external
async def test_bingx_get_server_time() -> None:
    """Test retrieving BingX server time and validate its structure."""
    async with BingxClient() as client:
        server_time = await client.get_server_time()
        logging.info("BingX server time response: %r", server_time)

        assert isinstance(server_time, dict), (
            "BingX server time response should be a dictionary"
        )

        assert server_time.get("code") == 0
        assert server_time.get("msg", "") == ""
        assert isinstance(server_time.get("data"), dict)
        assert "serverTime" in server_time["data"]
        assert isinstance(server_time["data"]["serverTime"], int)


@pytest.mark.external
async def test_okx_get_server_time() -> None:
    """Test retrieving OKX server time and validate its structure."""
    async with OkxClient() as client:
        server_time = await client.get_server_time()
        logging.info("OKX server time response: %r", server_time)

        assert isinstance(server_time, dict), (
            "OKX server time response should be a dictionary"
        )
        assert server_time.get("code") == "0"
        assert server_time.get("msg", "") == ""
        assert isinstance(server_time.get("data"), list)
        assert len(server_time["data"]) > 0
        ts = server_time["data"][0].get("ts")
        assert ts is not None
        assert isinstance(ts, str)
        assert ts.isdigit()


@pytest.mark.external
async def test_kucoin_get_server_time() -> None:
    """Test retrieving KuCoin server time and validate its structure."""
    async with KuCoinClient() as client:
        server_time = await client.get_server_time()
        logging.info("KuCoin server time response: %r", server_time)

        assert isinstance(server_time, dict), (
            "KuCoin server time response should be a dictionary"
        )

        # Example KuCoin response: {'code': '200000', 'data': server_time_int}
        assert server_time.get("code") == "200000"
        assert "data" in server_time
        assert isinstance(server_time["data"], int)
