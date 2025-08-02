from pathlib import Path
from typing import cast

from app.graph.nodes import (
    planner,
    researcher,
    synthesiser,
    pedagogy_critic,
    qa_reviewer,
)
from app.graph.state import LectureState


def _state(topic: str) -> LectureState:
    return {
        "topic": topic,
        "outline": "",
        "citations": [],
        "action_log": [],
        "stream_buffer": [],
    }


def _load(name: str) -> str:
    return (Path("app/prompts") / f"{name}.txt").read_text()


def test_planner_uses_external_prompt() -> None:
    template = _load("planner")
    result = planner.planner(_state("Physics"))
    assert result["outline"] == template.format(topic="Physics")


def test_researcher_uses_external_prompt() -> None:
    template = _load("researcher")
    result = researcher.researcher(_state("Chemistry"))
    citations = cast(list[dict[str, str]], result["citations"])
    snippet = citations[0]["snippet"]
    assert snippet == template.format(topic="Chemistry")


def test_synthesiser_uses_external_prompt() -> None:
    template = _load("synthesiser")
    result = synthesiser.synthesiser(_state("Math"))
    buffer = cast(list[str], result["stream_buffer"])
    expected = template.format(topic="Math").split()
    assert buffer == expected


def test_pedagogy_critic_uses_external_prompt() -> None:
    template = _load("pedagogy_critic")
    result = pedagogy_critic.pedagogy_critic(_state("Biology"))
    log = cast(list[str], result["action_log"])
    assert log[-1] == template.format(topic="Biology")


def test_qa_reviewer_uses_external_prompt() -> None:
    template = _load("qa_reviewer")
    result = qa_reviewer.qa_reviewer(_state("History"))
    log = cast(list[str], result["action_log"])
    assert log[-1] == template.format(topic="History")
