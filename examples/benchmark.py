"""Simple performance benchmark for BybitClientsCache and SharedSessionManager."""

import asyncio
import time
from collections import OrderedDict
from typing import Dict, Tuple

from aiotrade import BybitClient, BybitClientsCache, SharedSessionManager

CLIENTS_COUNT = 10_000


def make_credentials(i: int, prefix: str = "client") -> Tuple[str, str]:
    """Generate unique API credentials for testing."""
    return f"{prefix}_key_{i:04d}", f"{prefix}_secret_{i:04d}"


def start_timer() -> float:
    return time.perf_counter()


def elapsed_ms(start: float) -> float:
    return (time.perf_counter() - start) * 1000.0


class CacheBenchmarks:
    @staticmethod
    async def direct_creation() -> float:
        """Time direct client creation without cache (sequential), fetch https://example.com."""
        clients: list[BybitClient] = []
        start = start_timer()
        for i in range(CLIENTS_COUNT):
            api_key, api_secret = make_credentials(i, "direct")
            client = BybitClient(api_key=api_key, api_secret=api_secret, testnet=True)
            clients.append(client)
        elapsed = elapsed_ms(start)
        for client in clients:
            await client.close()
        return elapsed

    @staticmethod
    async def direct_creation_gather() -> float:
        """Time direct client creation without cache (parallel with gather), fetch https://example.com."""

        async def create_aenter_and_fetch(i: int) -> BybitClient:
            api_key, api_secret = make_credentials(i, "direct_gather")
            return BybitClient(api_key=api_key, api_secret=api_secret, testnet=True)

        start = start_timer()
        clients = await asyncio.gather(
            *(create_aenter_and_fetch(i) for i in range(CLIENTS_COUNT))
        )
        elapsed = elapsed_ms(start)
        for client in clients:
            await client.close()
        return elapsed

    @staticmethod
    async def cache_get_or_create() -> float:
        """Time cache get_or_create (cold cache, sequential), fetch https://example.com."""
        BybitClientsCache.clear()
        clients: list[BybitClient] = []
        start = start_timer()
        for i in range(CLIENTS_COUNT):
            api_key, api_secret = make_credentials(i, "cache_cold")
            client = BybitClientsCache.get_or_create(
                api_key=api_key, api_secret=api_secret, testnet=True
            )

            clients.append(client)
        elapsed = elapsed_ms(start)
        for client in clients:
            await client.close()
        return elapsed

    @staticmethod
    async def cache_get_or_create_gather() -> float:
        """Time cache get_or_create (cold cache, parallel with gather), fetch https://example.com."""
        BybitClientsCache.clear()

        async def get_or_create_aenter_and_fetch(i: int) -> BybitClient:
            api_key, api_secret = make_credentials(i, "cache_cold_gather")
            return BybitClientsCache.get_or_create(
                api_key=api_key, api_secret=api_secret, testnet=True
            )

        start = start_timer()
        clients = await asyncio.gather(
            *(get_or_create_aenter_and_fetch(i) for i in range(CLIENTS_COUNT))
        )
        elapsed = elapsed_ms(start)
        for client in clients:
            await client.close()
        return elapsed

    @staticmethod
    async def cache_get() -> float:
        """Time cache get (warm cache, sequential), fetch https://example.com."""
        BybitClientsCache.clear()
        # Pre-populate cache
        for i in range(CLIENTS_COUNT):
            api_key, api_secret = make_credentials(i, "cache_warm")
            BybitClientsCache.get_or_create(
                api_key=api_key, api_secret=api_secret, testnet=True
            )
        clients: list[BybitClient] = []
        start = start_timer()
        for i in range(CLIENTS_COUNT):
            api_key, api_secret = make_credentials(i, "cache_warm")
            client = BybitClientsCache.get(
                api_key=api_key, api_secret=api_secret, testnet=True
            )
            if client is None:
                raise AssertionError(f"Cache miss for client {i}")

            clients.append(client)
        elapsed = elapsed_ms(start)
        for client in clients:
            await client.close()
        return elapsed

    @staticmethod
    async def cache_get_gather() -> float:
        """Time cache get (warm cache, parallel with gather), fetch https://example.com."""
        BybitClientsCache.clear()
        # Pre-populate cache
        for i in range(CLIENTS_COUNT):
            api_key, api_secret = make_credentials(i, "cache_warm_gather")
            BybitClientsCache.get_or_create(
                api_key=api_key, api_secret=api_secret, testnet=True
            )

        async def get_aenter_and_fetch(i: int) -> BybitClient:
            api_key, api_secret = make_credentials(i, "cache_warm_gather")
            client = BybitClientsCache.get(
                api_key=api_key, api_secret=api_secret, testnet=True
            )
            if client is None:
                raise AssertionError(f"Cache miss for client {i}")

            return client

        start = start_timer()
        clients = await asyncio.gather(
            *(get_aenter_and_fetch(i) for i in range(CLIENTS_COUNT))
        )
        elapsed = elapsed_ms(start)
        for client in clients:
            await client.close()
        return elapsed


class BenchmarkResultSummary:
    @staticmethod
    def print(results: Dict[str, float]) -> None:
        """Print summary sorted by best (fastest) timings, with ms/client."""
        print()
        print("```text")
        print(
            "Scenario                                          |"
            "     Time (ms) |   ms per client"
        )
        print("-" * 70)
        sorted_items = sorted(results.items(), key=lambda x: x[1])
        for scenario, time_ms in sorted_items:
            per_client = time_ms / CLIENTS_COUNT
            print(f"{scenario:<47} | {time_ms:12.2f} | {per_client:18.8f}")
        print("```")


async def run_benchmarks_without_session_manager() -> Dict[str, float]:
    print(f"\nBenchmarking {CLIENTS_COUNT} clients WITHOUT SharedSessionManager ...\n")
    results: OrderedDict[str, float] = OrderedDict()
    results["direct_creation"] = await CacheBenchmarks.direct_creation()
    results["direct_creation_gather"] = await CacheBenchmarks.direct_creation_gather()
    results["cache_get_or_create"] = await CacheBenchmarks.cache_get_or_create()
    results[
        "cache_get_or_create_gather"
    ] = await CacheBenchmarks.cache_get_or_create_gather()
    results["cache_get"] = await CacheBenchmarks.cache_get()
    results["cache_get_gather"] = await CacheBenchmarks.cache_get_gather()
    return results


async def run_benchmarks_with_session_manager() -> Dict[str, float]:
    print(f"\nBenchmarking {CLIENTS_COUNT} clients WITH SharedSessionManager ...\n")
    results: OrderedDict[str, float] = OrderedDict()
    # Setup SharedSessionManager before all scenarios
    SharedSessionManager.setup(2000)
    results[
        "direct_creation_with_session_manager"
    ] = await CacheBenchmarks.direct_creation()
    results[
        "direct_creation_gather_with_session_manager"
    ] = await CacheBenchmarks.direct_creation_gather()
    results[
        "cache_get_or_create_with_session_manager"
    ] = await CacheBenchmarks.cache_get_or_create()
    results[
        "cache_get_or_create_gather_with_session_manager"
    ] = await CacheBenchmarks.cache_get_or_create_gather()
    results["cache_get_with_session_manager"] = await CacheBenchmarks.cache_get()
    results[
        "cache_get_gather_with_session_manager"
    ] = await CacheBenchmarks.cache_get_gather()
    return results


async def main() -> None:
    print("BybitClientsCache and SharedSessionManager Performance Benchmark")
    print("=" * 60)
    # Phase 1: WITHOUT SharedSessionManager
    results_without = await run_benchmarks_without_session_manager()
    BenchmarkResultSummary.print(results_without)

    # Cleanup: clear cache and close SharedSessionManager (if needed)
    BybitClientsCache.clear()
    await SharedSessionManager.close()
    await asyncio.sleep(0.1)

    # Phase 2: WITH SharedSessionManager
    results_with = await run_benchmarks_with_session_manager()
    BenchmarkResultSummary.print(results_with)

    # Final cleanup (as in Rust)
    BybitClientsCache.clear()
    await SharedSessionManager.close()


if __name__ == "__main__":
    asyncio.run(main())
