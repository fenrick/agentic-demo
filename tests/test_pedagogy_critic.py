# isort: skip_file
import sys
import types

import pytest

from agents.models import Activity
from core.state import Module, State

# Provide minimal config stub before importing the critic
config_stub = types.ModuleType("config")
config_stub.load_settings = lambda: types.SimpleNamespace(  # type: ignore[attr-defined]
    model_provider="openai", model_name="gpt"
)
sys.modules["config"] = config_stub

from agents.pedagogy_critic import run_pedagogy_critic  # noqa: E402


@pytest.mark.asyncio
async def test_run_pedagogy_critic_uses_module_activities(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Pedagogy critic aggregates activities from state modules."""

    async def _fake_classify(_text: str) -> str:
        return "remember"

    monkeypatch.setattr("agents.pedagogy_critic.classify_bloom_level", _fake_classify)

    state = State(prompt="topic")
    state.learning_objectives = ["List facts"]
    state.modules.append(
        Module(
            id="m1",
            title="Intro",
            duration_min=10,
            learning_objectives=["List facts"],
            activities=[
                Activity(
                    type="Lecture",
                    description="talk",
                    duration_min=10,
                    learning_objectives=["List facts"],
                )
            ],
        )
    )

    report = await run_pedagogy_critic(state)
    assert report.diversity.type_percentages["Lecture"] == 1.0
    assert report.bloom.level_counts["remember"] == 2
