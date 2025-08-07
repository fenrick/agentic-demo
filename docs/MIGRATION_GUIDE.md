# Migration Guide

This guide helps contributors move to the graph-based orchestrator and typed Pydantic models.

## Rationale

- Strong typing via Pydantic provides clearer contracts between agents.
- The `GraphOrchestrator` offers predictable node execution and better observability.
- Shared models reduce duplication and ease validation across the system.

## Major API Differences

- `GraphOrchestrator` replaces the previous `run_workflow` helper.
- Workflows are defined through `build_main_flow()` which returns a list of `Node` objects.
- State is now managed by the Pydantic `State` dataclass instead of free-form dictionaries.
- Agent inputs and outputs are expressed as Pydantic models in `src/agents/models.py`.

## Migration Steps

1. Import and instantiate the orchestrator:

   ```python
   from core.orchestrator import GraphOrchestrator, build_main_flow
   orch = GraphOrchestrator(build_main_flow())
   ```

2. Replace dictionary state with the typed model:

   ```python
   from core.state import State
   state = State(prompt=old_state["prompt"])
   await orch.run(state)
   ```

3. Update agent calls to use the models defined in `agents.models` rather than raw dicts.
4. When persisting data, use `.model_dump()` instead of manually constructing dictionaries.

Following these steps will bring extensions and custom nodes in line with the new orchestrator and model architecture.
