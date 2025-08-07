"""Command-line interface for generating lecture material."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
from typing import Any, Dict

from agents.streaming import stream_messages
from core.orchestrator import graph
from core.state import State
from config import load_settings
import logfire


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate lecture material from a topic prompt.",
    )
    parser.add_argument("topic", help="Topic or outline for the lecture")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable progress feedback on the console",
    )
    return parser.parse_args()


async def _generate(topic: str) -> Dict[str, Any]:
    """Run the full graph for ``topic`` and return the final state."""

    state = State(prompt=topic)
    await graph.run(state)
    return state.to_dict()


def main() -> None:
    """Entry point for console scripts."""
    args = parse_args()
    settings = load_settings()
    if settings.enable_tracing:
        logfire.configure(
            token=settings.logfire_api_key,
            service_name=settings.logfire_project,
        )
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
        stream_messages("LLM response stream start")
    try:
        payload = asyncio.run(_generate(args.topic))
    except Exception as exc:  # pragma: no cover - defensive
        raise SystemExit(f"Error generating lecture: {exc}") from exc
    if args.verbose:
        stream_messages("LLM response stream complete: %s" % json.dumps(payload))
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
