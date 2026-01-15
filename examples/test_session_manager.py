"""Test session manager performance."""

import asyncio
import gc
import time
from typing import Dict, List

from aiotrade import BybitClient, SharedSessionManager


async def benchmark_session_manager_scenarios(
    client_count: int = 10000,
) -> Dict[str, float]:
    """Compare client creation with and without session manager.

    Args:
        client_count: Number of clients to create for each scenario

    Returns:
        Dictionary with timing results, in milliseconds
    """
    # Initialize results dictionary
    results: Dict[str, float] = {
        "individual_sessions_10000_clients": 0.0,
        "shared_session_10000_clients": 0.0,
    }

    print(f"Running session manager benchmark with {client_count} clients...")

    async def cleanup_between_scenarios() -> None:
        """Clean up resources between scenarios."""
        await SharedSessionManager.close()
        gc.collect()
        await asyncio.sleep(0.1)  # Brief pause for cleanup

    # Scenario 1: Create clients without session manager (individual sessions)
    print(f"Scenario 1: Creating {client_count} clients with individual sessions...")
    await cleanup_between_scenarios()

    start_time = time.perf_counter()

    clients_without_session: List[BybitClient] = []
    for i in range(client_count):
        client = BybitClient(
            api_key=f"individual_key_{i:04d}",
            api_secret=f"individual_secret_{i:04d}",
            testnet=True,
        )
        clients_without_session.append(client)

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    results["individual_sessions_10000_clients"] = elapsed_ms

    # Verify individual sessions
    individual_count = sum(
        1
        for client in clients_without_session
        if not getattr(client, "uses_shared_session", False)
    )
    print(
        f"Individual session verification: {individual_count}/{client_count} "
        "clients use individual sessions"
    )

    # Cleanup individual sessions
    for client in clients_without_session:
        if not client.uses_shared_session:
            await client._session.close()  # noqa: SLF001 # type: ignore

    clients_without_session.clear()

    # Scenario 2: Create clients with session manager (shared session)
    print(f"Scenario 2: Creating {client_count} clients with shared session...")
    await cleanup_between_scenarios()

    print("Setting up session manager...")
    SharedSessionManager.setup(max_connections=2000)

    start_time = time.perf_counter()

    clients_with_session: List[BybitClient] = []
    for i in range(client_count):
        client = BybitClient(
            api_key=f"shared_key_{i:04d}",
            api_secret=f"shared_secret_{i:04d}",
            testnet=True,
        )
        clients_with_session.append(client)

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    results["shared_session_10000_clients"] = elapsed_ms

    # Verify shared session usage
    shared_count = sum(
        1
        for client in clients_with_session
        if getattr(client, "uses_shared_session", False)
    )
    print(
        f"Shared session verification: {shared_count}/{client_count} "
        "clients use shared session"
    )

    # Final cleanup
    await cleanup_between_scenarios()

    return results


def print_session_manager_summary(results: Dict[str, float], client_count: int) -> None:
    """Print formatted session manager benchmark summary."""
    print("\n" + "=" * 80)
    print("SESSION MANAGER PERFORMANCE COMPARISON")
    print("=" * 80)

    individual_time_ms = results["individual_sessions_10000_clients"]
    shared_time_ms = results["shared_session_10000_clients"]

    # Prepare scenario data
    scenario_data = [
        (
            "Individual sessions",
            individual_time_ms,
            individual_time_ms / client_count,
            1000 * (client_count / individual_time_ms) if individual_time_ms else 0.0,
        ),
        (
            "Shared session",
            shared_time_ms,
            shared_time_ms / client_count,
            1000 * (client_count / shared_time_ms) if shared_time_ms else 0.0,
        ),
    ]
    scenario_data.sort(key=lambda x: x[1])  # Sort by total time

    print(f"Total clients: {client_count}")
    print()

    print("```text")
    print(
        "Scenario               | Total Time (ms) | Time per client (ms) | Clients/sec"
    )
    print("-" * 85)
    for scenario, total_time, time_per_client, clients_per_sec in scenario_data:
        print(
            f"{scenario:<22} | {total_time:14.2f} | "
            f"{time_per_client:18.4f} | {clients_per_sec:10.1f}"
        )
    print("```")

    print()
    print("PERFORMANCE ANALYSIS:")
    print("-" * 30)

    if individual_time_ms > 0 and shared_time_ms > 0:
        improvement = (individual_time_ms - shared_time_ms) / individual_time_ms * 100
        speedup = individual_time_ms / shared_time_ms

        print("Shared session vs Individual sessions:")
        print(f"  - Time difference: {individual_time_ms - shared_time_ms:.2f} ms")
        print(f"  - Performance improvement: {improvement:.1f}%")
        print(f"  - Shared session is {speedup:.1f}x faster")

        print()
        print("Conclusion:")
        if speedup >= 2.0:
            print("  ✓ Shared session provides significant performance benefit")
            print("    for high-frequency client creation")
        elif speedup >= 1.5:
            print("  ✓ Shared session provides good performance benefit")
        elif speedup >= 1.1:
            print("  ~ Shared session provides moderate performance benefit")
        else:
            print("  ⚠ Shared session benefit is minimal - consider individual")
            print("    sessions for low-frequency use")


async def main() -> None:
    """Run session manager benchmark tests."""
    print("SharedSessionManager Performance Benchmark")
    print("Comparing individual sessions vs shared session")

    # Run benchmark
    client_count = 100_000
    results = await benchmark_session_manager_scenarios(client_count)

    # Print summary
    print_session_manager_summary(results, client_count)


if __name__ == "__main__":
    asyncio.run(main())
