"""Benchmark test for multiple clients."""

import asyncio
import time
from typing import Any, Dict, List, Tuple

from aiobybit import BybitClient


async def main() -> None:
    """Benchmark test: create 10 clients, each making 3 requests to get server time."""
    print("Starting multiclient benchmark: 10 clients making 3 requests each...")

    # Create 10 clients for testnet (no authentication required for this endpoint)
    clients: List[BybitClient] = []
    for _ in range(10):
        client = BybitClient(
            api_key="",
            api_secret="",
            testnet=True,
        )
        clients.append(client)

    start_time = time.time()
    results: List[Dict[str, Any]] = []

    # Create tasks for parallel execution
    tasks: List[asyncio.Task[None]] = []

    for client_idx, client in enumerate(clients):

        async def make_requests(client_idx: int, client: BybitClient) -> None:
            async with client:
                # Create tasks for parallel execution of a single client's requests
                client_tasks: List[Tuple[int, asyncio.Task[Dict[str, Any]]]] = []
                for request_idx in range(3):
                    task = asyncio.create_task(client.get_server_time())
                    client_tasks.append((request_idx, task))

                # Wait for the completion of all requests for this client
                for request_idx, task in client_tasks:
                    try:
                        response = await task
                        results.append(response)
                        print(
                            f"Client {client_idx + 1}/10, "
                            f"Request {request_idx + 1}/3: OK"
                        )
                    except Exception as e:
                        print(
                            f"Client {client_idx + 1}/10, "
                            f"Request {request_idx + 1}/3: ERROR - {e}"
                        )

        task = asyncio.create_task(make_requests(client_idx, client))
        tasks.append(task)

    # Wait for completion of all client tasks
    await asyncio.gather(*tasks)

    end_time = time.time()
    elapsed = end_time - start_time

    print("\nMulticlient benchmark completed:")
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
