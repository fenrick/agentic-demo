"""Benchmark the instrumented pipeline against baseline to detect regressions."""

from __future__ import annotations

import asyncio
from time import perf_counter

from core.orchestrator import wrap_with_tracing
from core.state import State


async def _dummy_node(state: State) -> dict:
    """Trivial node used for benchmarking."""
    return {"ok": True}


async def _run(fn, iterations: int = 100) -> float:
    """Execute ``fn`` repeatedly and return average latency in ms."""
    state = State(prompt="benchmark")
    start = perf_counter()
    for _ in range(iterations):
        await fn(state)
    return (perf_counter() - start) * 1000 / iterations


async def main() -> None:
    """Run benchmark comparing baseline and instrumented variants."""
    baseline = await _run(_dummy_node)
    instrumented = await _run(wrap_with_tracing(_dummy_node))
    overhead = instrumented - baseline
    print(
        f"baseline={baseline:.3f}ms instrumented={instrumented:.3f}ms"
        f" overhead={overhead:.3f}ms"
    )


if __name__ == "__main__":
    asyncio.run(main())
