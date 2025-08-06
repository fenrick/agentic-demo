"""Command-line interface for generating lecture material."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
from typing import Any, Dict

from agents.streaming import stream_messages
from core.orchestrator import create_checkpoint_saver, graph


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
    """Run the full LangGraph for ``topic``.

    Args:
        topic: Subject matter to base the lecture on.

    Returns:
        Dict[str, Any]: Final graph state serialized to a plain dictionary.
    """

    async with create_checkpoint_saver() as saver:
        return await graph.ainvoke(
            {"prompt": topic},
            config={
                "checkpoint": saver,
                "resume": True,
                "configurable": {"thread_id": "cli"},
            },
        )


def main() -> None:
    """Entry point for console scripts."""
    args = parse_args()
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
