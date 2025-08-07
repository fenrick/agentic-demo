import types
import sys

import os

# mypy: ignore-errors

os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("PERPLEXITY_API_KEY", "test")

# Stub core.orchestrator before importing document_dag
orchestrator = types.ModuleType("core.orchestrator")


class _Graph:
    def __init__(self, nodes, edges, conditionals):
        self.nodes = nodes

    async def run(self, state):
        await self.nodes["Researcher-Web"](state)
        await self.nodes["Content-Weaver"](state)
        await self.nodes["Pedagogy-Critic"](state)


orchestrator.Graph = _Graph
orchestrator.START = "START"
orchestrator.END = "END"
sys.modules["core.orchestrator"] = orchestrator


# Stub policy
core_policies = types.ModuleType("core.policies")
core_policies.policy_retry_on_critic_failure = lambda *_, **__: False
sys.modules["core.policies"] = core_policies


# Stub agent functions
calls: list[str] = []


a_research = types.ModuleType("agents.researcher_web_node")


async def run_researcher_web(state):  # noqa: D401 - stub
    calls.append("research")


a_research.run_researcher_web = run_researcher_web
sys.modules["agents.researcher_web_node"] = a_research


a_weaver = types.ModuleType("agents.content_weaver")


async def run_content_weaver(state, section_id=None):  # noqa: D401 - stub
    calls.append("draft")
    module = Module(id=str(section_id), title=f"t{section_id}", duration_min=1)
    state.modules.append(module)
    return module


a_weaver.run_content_weaver = run_content_weaver
sys.modules["agents.content_weaver"] = a_weaver


a_critic = types.ModuleType("agents.pedagogy_critic")


async def run_pedagogy_critic(state):  # noqa: D401 - stub
    calls.append("critic")


a_critic.run_pedagogy_critic = run_pedagogy_critic
sys.modules["agents.pedagogy_critic"] = a_critic


# Import after stubs
from core.document_dag import run_document_dag  # noqa: E402
from core.state import Outline, State, Module  # noqa: E402


def test_run_document_dag_processes_sections():
    state = State(prompt="p", outline=Outline(steps=["a", "b"]))
    asyncio_run = getattr(__import__("asyncio"), "run")
    asyncio_run(run_document_dag(state, skip_plan=True))
    assert calls == [
        "research",
        "draft",
        "critic",
        "research",
        "draft",
        "critic",
    ]
    assert len(state.modules) == 2
    assert state.outline.modules == state.modules
