"""Command-line interface for generating lecture material."""

# ruff: noqa: E402
from __future__ import annotations

import argparse
import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from agents.streaming import stream_messages


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
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("run_output.md"),
        help="Path to the output markdown file",
    )
    return parser.parse_args()


async def _generate(topic: str) -> Dict[str, Any]:
    """Run the full graph for ``topic`` and return the final state."""

    from core.orchestrator import graph_orchestrator
    from core.state import State

    state = State(prompt=topic)
    await graph_orchestrator.run(state)
    return state.to_dict()


def save_markdown(output: Path, topic: str, payload: Dict[str, Any]) -> None:
    """Write the generated lecture payload to ``output`` in Markdown."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    output_json = json.dumps(payload, indent=2)
    lines = [
        "# Lecture Output",
        f"Topic: {topic}",
        "",
        "```json",
        output_json,
        "```",
        "",
        f"Generated at {timestamp} UTC",
    ]
    output.write_text("\n".join(lines) + "\n")


def main() -> None:
    """Entry point for console scripts."""
    args = parse_args()
    from observability import init_observability, install_auto_tracing

    install_auto_tracing()
    init_observability()
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
    save_markdown(args.output, args.topic, payload)


if __name__ == "__main__":
    main()
