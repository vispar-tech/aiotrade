"""Benchmark test for market data endpoints."""

import asyncio
import time
from typing import Any, Dict, List, Tuple

from aiotrade import BybitClient

NUM_REQUESTS = 10  # Number of requests to perform


async def main() -> None:
    """Benchmark test: make NUM_REQUESTS requests to get server time."""
    # Create client for testnet (no authentication required for this endpoint)
    client = BybitClient(
        api_key="",
        api_secret="",
        testnet=True,
    )

    print(f"Starting benchmark: {NUM_REQUESTS} requests to get server time...")

    start_time = time.time()
    results: List[Dict[str, Any]] = []

    async with client:
        # Create tasks for parallel execution
        tasks: List[Tuple[int, asyncio.Task[Dict[str, Any]]]] = []
        for i in range(NUM_REQUESTS):
            task = asyncio.create_task(client.get_server_time())
            tasks.append((i, task))

        # Wait for all tasks to complete
        for i, task in tasks:
            try:
                response = await task
                results.append(response)
                print(f"Request {i + 1}/{NUM_REQUESTS}: OK")
            except Exception as e:
                print(f"Request {i + 1}/{NUM_REQUESTS}: ERROR - {e}")

    end_time = time.time()
    elapsed = end_time - start_time

    print("\nBenchmark completed:")
    print(f"Total requests: {len(results)}")
    print(f"Total time: {elapsed:.2f} seconds")
    print(f"Average per request: {elapsed / NUM_REQUESTS:.4f} seconds")
    print(f"Requests per second: {NUM_REQUESTS / elapsed:.4f}")

    if results:
        # Show sample response
        print("\nSample response:")
        print(f"retCode: {results[0]['retCode']}")
        print(f"timeSecond: {results[0]['result']['timeSecond']}")
        print(f"timeNano: {results[0]['result']['timeNano']}")


if __name__ == "__main__":
    asyncio.run(main())
