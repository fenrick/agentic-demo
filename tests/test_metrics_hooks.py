import pytest

try:  # pragma: no cover - skip if orchestrator dependencies missing
    from core.orchestrator import metrics, wrap_with_tracing
    from core.state import State
except Exception as exc:  # noqa: BLE001 - allow broad except for optional import
    pytest.skip(f"orchestrator import failed: {exc}", allow_module_level=True)


@pytest.mark.asyncio
async def test_metrics_recorded_for_wrapped_node() -> None:
    async def dummy(state: State) -> dict:
        return {"ok": True}

    wrapped = wrap_with_tracing(dummy)
    state = State(prompt="hi")
    metrics._buffer.clear()  # type: ignore[attr-defined]
    await wrapped(state)
    names = {m.name for m in metrics._buffer}  # type: ignore[attr-defined]
    assert {"dummy.tokens", "dummy.latency_ms"} <= names
