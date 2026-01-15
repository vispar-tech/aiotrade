"""Test get_server_time endpoint for BybitClient and BingxClient."""

import logging

from aiotrade.clients import BingxClient, BybitClient


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
