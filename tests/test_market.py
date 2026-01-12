"""Benchmark test for market data endpoints."""

import asyncio
import time
from typing import Any, Dict, List, Tuple

from aiobybit import BybitClient


async def main() -> None:
    """Benchmark test: make 30 requests to get server time."""
    # Create client for testnet (no authentication required for this endpoint)
    client = BybitClient(
        api_key="",
        api_secret="",
        testnet=True,
    )

    print("Starting benchmark: 30 requests to get server time...")

    start_time = time.time()
    results: List[Dict[str, Any]] = []

    async with client:
        # Create tasks for parallel execution
        tasks: List[Tuple[int, asyncio.Task[Dict[str, Any]]]] = []
        for i in range(30):
            task = asyncio.create_task(client.get_server_time())
            tasks.append((i, task))

        # Wait for all tasks to complete
        for i, task in tasks:
            try:
                response = await task
                results.append(response)
                print(f"Request {i + 1}/30: OK")
            except Exception as e:
                print(f"Request {i + 1}/30: ERROR - {e}")

    end_time = time.time()
    elapsed = end_time - start_time

    print("\nBenchmark completed:")
    print(f"Total requests: {len(results)}")
    print(f"Total time: {elapsed:.2f} seconds")
    print(f"Average per request: {elapsed / 30:.4f} seconds")
    print(f"Requests per second: {30 / elapsed:.4f}")

    if results:
        # Show sample response
        print("\nSample response:")
        print(f"retCode: {results[0]['retCode']}")
        print(f"timeSecond: {results[0]['result']['timeSecond']}")
        print(f"timeNano: {results[0]['result']['timeNano']}")


if __name__ == "__main__":
    asyncio.run(main())
