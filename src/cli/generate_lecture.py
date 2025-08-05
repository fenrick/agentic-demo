"""Command-line interface for generating lecture material."""

from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import asdict
from typing import Any, Dict

from agents.content_weaver import run_content_weaver
from core.state import State


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate lecture material from a topic prompt."
    )
    parser.add_argument("topic", help="Topic or outline for the lecture")
    return parser.parse_args()


async def _generate(topic: str) -> Dict[str, Any]:
    """Invoke the content weaver for ``topic``.

    Args:
        topic: Subject matter to base the lecture on.

    Returns:
        Dict[str, Any]: Lecture material as a plain dictionary.
    """

    state = State(prompt=topic)
    result = await run_content_weaver(state)
    return asdict(result)


def main() -> None:
    """Entry point for console scripts."""
    args = parse_args()
    try:
        payload = asyncio.run(_generate(args.topic))
    except Exception as exc:  # pragma: no cover - defensive
        raise SystemExit(f"Error generating lecture: {exc}") from exc
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
