"""Benchmark test for multiple clients."""

import asyncio
import time
from typing import Any, Dict, List, Tuple

from aiotrade import BybitClient

# Constants for clients and requests per client
NUM_CLIENTS = 10
REQUESTS_PER_CLIENT = 3


async def main() -> None:
    """
    Benchmark test: create NUM_CLIENTS clients
    each making REQUESTS_PER_CLIENT requests to get server time.
    """
    print(
        f"Starting multiclient benchmark: {NUM_CLIENTS} clients "
        f"making {REQUESTS_PER_CLIENT} requests each..."
    )

    # Create NUM_CLIENTS clients for testnet (no authentication required)
    clients: List[BybitClient] = []
    for _ in range(NUM_CLIENTS):
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
                for request_idx in range(REQUESTS_PER_CLIENT):
                    task = asyncio.create_task(client.get_server_time())
                    client_tasks.append((request_idx, task))

                # Wait for the completion of all requests for this client
                for request_idx, task in client_tasks:
                    try:
                        response = await task
                        results.append(response)
                        print(
                            f"Client {client_idx + 1}/{NUM_CLIENTS}, "
                            f"Request {request_idx + 1}/{REQUESTS_PER_CLIENT}: OK"
                        )
                    except Exception as e:
                        print(
                            f"Client {client_idx + 1}/{NUM_CLIENTS}, "
                            f"Request {request_idx + 1}/{REQUESTS_PER_CLIENT}: "
                            f"ERROR - {e}"
                        )

        task = asyncio.create_task(make_requests(client_idx, client))
        tasks.append(task)

    # Wait for completion of all client tasks
    await asyncio.gather(*tasks)

    end_time = time.time()
    elapsed = end_time - start_time
    total_requests = NUM_CLIENTS * REQUESTS_PER_CLIENT

    print("\nMulticlient benchmark completed:")
    print(f"Total requests: {len(results)}")
    print(f"Total time: {elapsed:.2f} seconds")
    print(f"Average per request: {elapsed / total_requests:.4f} seconds")
    print(f"Requests per second: {total_requests / elapsed:.4f}")

    if results:
        # Show sample response
        print("\nSample response:")
        print(f"retCode: {results[0]['retCode']}")
        print(f"timeSecond: {results[0]['result']['timeSecond']}")
        print(f"timeNano: {results[0]['result']['timeNano']}")


if __name__ == "__main__":
    asyncio.run(main())
