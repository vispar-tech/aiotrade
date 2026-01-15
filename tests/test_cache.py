"""Simple performance benchmark for BybitClientCache."""

import asyncio
import time
from typing import Dict

from aiobybit.cache import BybitClientCache
from aiobybit.http import BybitHttpClient


def make_credentials(i: int, prefix: str = "client") -> tuple[str, str]:
    """Generate unique API credentials for testing."""
    return f"{prefix}_key_{i:04d}", f"{prefix}_secret_{i:04d}"


async def benchmark_direct_creation(client_count: int) -> float:
    """Time direct client creation without cache (sequential)."""
    clients: list[BybitHttpClient] = []
    t0 = time.perf_counter()
    for i in range(client_count):
        api_key, api_secret = make_credentials(i, "direct")
        client = BybitHttpClient(api_key=api_key, api_secret=api_secret, testnet=True)
        clients.append(client)
        # Simulate minimal usage
        _ = client.api_key

    elapsed = (time.perf_counter() - t0) * 1000

    # Close all client sessions
    for client in clients:
        await client.close()

    return elapsed


async def benchmark_direct_creation_gather(client_count: int) -> float:
    """Time direct client creation without cache (parallel with gather)."""

    async def create_client(i: int) -> BybitHttpClient:
        api_key, api_secret = make_credentials(i, "direct_gather")
        client = BybitHttpClient(api_key=api_key, api_secret=api_secret, testnet=True)
        # Simulate minimal usage
        _ = client.api_key
        return client

    t0 = time.perf_counter()
    clients = await asyncio.gather(*(create_client(i) for i in range(client_count)))
    elapsed = (time.perf_counter() - t0) * 1000

    # Close all client sessions
    for client in clients:
        await client.close()

    return elapsed


async def benchmark_cache_get_or_create(client_count: int) -> float:
    """Time cache get_or_create (cold cache, sequential)."""
    BybitClientCache.clear()
    clients: list[BybitHttpClient] = []
    t0 = time.perf_counter()
    for i in range(client_count):
        api_key, api_secret = make_credentials(i, "cache_cold")
        client = BybitClientCache.get_or_create(
            api_key=api_key, api_secret=api_secret, testnet=True
        )
        clients.append(client)
        # Simulate minimal usage
        _ = client.api_key

    elapsed = (time.perf_counter() - t0) * 1000

    # Close all client sessions
    for client in clients:
        await client.close()

    return elapsed


async def benchmark_cache_get_or_create_gather(client_count: int) -> float:
    """Time cache get_or_create (cold cache, parallel with gather)."""
    BybitClientCache.clear()

    async def get_or_create_client(i: int) -> BybitHttpClient:
        api_key, api_secret = make_credentials(i, "cache_cold_gather")
        client = BybitClientCache.get_or_create(
            api_key=api_key, api_secret=api_secret, testnet=True
        )
        # Simulate minimal usage
        _ = client.api_key
        return client

    t0 = time.perf_counter()
    clients = await asyncio.gather(
        *(get_or_create_client(i) for i in range(client_count))
    )
    elapsed = (time.perf_counter() - t0) * 1000

    # Close all client sessions
    for client in clients:
        await client.close()

    return elapsed


async def benchmark_cache_get(client_count: int) -> float:
    """Time cache get (warm cache, sequential)."""
    BybitClientCache.clear()
    # Pre-populate cache
    for i in range(client_count):
        api_key, api_secret = make_credentials(i, "cache_warm")
        BybitClientCache.get_or_create(
            api_key=api_key, api_secret=api_secret, testnet=True
        )

    clients: list[BybitHttpClient] = []
    t0 = time.perf_counter()
    for i in range(client_count):
        api_key, api_secret = make_credentials(i, "cache_warm")
        client = BybitClientCache.get(
            api_key=api_key, api_secret=api_secret, testnet=True
        )
        if client is None:
            raise AssertionError(f"Cache miss for client {i}")
        clients.append(client)
        # Simulate minimal usage
        _ = client.api_key

    elapsed = (time.perf_counter() - t0) * 1000

    # Close all client sessions
    for client in clients:
        await client.close()

    return elapsed


async def benchmark_cache_get_gather(client_count: int) -> float:
    """Time cache get (warm cache, parallel with gather)."""
    BybitClientCache.clear()
    # Pre-populate cache
    for i in range(client_count):
        api_key, api_secret = make_credentials(i, "cache_warm_gather")
        BybitClientCache.get_or_create(
            api_key=api_key, api_secret=api_secret, testnet=True
        )

    async def get_client(i: int) -> BybitHttpClient:
        api_key, api_secret = make_credentials(i, "cache_warm_gather")
        client = BybitClientCache.get(
            api_key=api_key, api_secret=api_secret, testnet=True
        )
        if client is None:
            raise AssertionError(f"Cache miss for client {i}")
        # Simulate minimal usage
        _ = client.api_key
        return client

    t0 = time.perf_counter()
    clients = await asyncio.gather(*(get_client(i) for i in range(client_count)))
    elapsed = (time.perf_counter() - t0) * 1000

    # Close all client sessions
    for client in clients:
        await client.close()

    return elapsed


async def run_benchmarks(client_count: int = 10000) -> Dict[str, float]:
    """Run all benchmarks and return results."""
    print(f"\nBenchmarking {client_count} clients...\n")

    results: dict[str, float] = {}

    print("Testing direct creation (sequential)...")
    results["direct_creation"] = await benchmark_direct_creation(client_count)

    print("Testing direct creation (gather)...")
    results["direct_creation_gather"] = await benchmark_direct_creation_gather(
        client_count
    )

    print("Testing cache get_or_create (cold, sequential)...")
    results["cache_get_or_create"] = await benchmark_cache_get_or_create(client_count)

    print("Testing cache get_or_create (cold, gather)...")
    results["cache_get_or_create_gather"] = await benchmark_cache_get_or_create_gather(
        client_count
    )

    print("Testing cache get (warm, sequential)...")
    results["cache_get"] = await benchmark_cache_get(client_count)

    print("Testing cache get (warm, gather)...")
    results["cache_get_gather"] = await benchmark_cache_get_gather(client_count)

    return results


def print_best_summary(results: dict[str, float]) -> None:
    """Print summary sorted by best (fastest) timings."""
    print()
    print("```text")
    print("Scenario                                |    Time (ms)")
    print("-" * 55)
    sorted_items = sorted(results.items(), key=lambda x: x[1])
    for sc, t in sorted_items:
        print(f"{sc:<36} | {t:12.2f}")
    print("```")


async def main() -> None:
    """Run the main benchmark entry point."""
    client_count = 10_000

    print("BybitClientCache Performance Benchmark")
    print("=" * 40)

    results = await run_benchmarks(client_count)
    print_best_summary(results)

    # Cleanup
    BybitClientCache.clear()


if __name__ == "__main__":
    asyncio.run(main())
