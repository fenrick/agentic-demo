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

from agents.models import AssessmentItem, Citation, Slide, WeaveResult
from agents.streaming import stream_messages
from export.markdown import from_weave_result

PORTFOLIOS_ALL = [
    "Research & Innovation",
    "Education",
    "STEM",
    "Design & Social Context",
    "Business & Law",
    "Vocational Education",
]


def slugify(text: str) -> str:
    """Create a filesystem-friendly slug from ``text``."""
    return text.lower().replace("&", "and").replace("/", " ").replace(" ", "_")


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
    parser.add_argument(
        "--portfolio",
        dest="portfolios",
        action="append",
        help="Portfolio to target. May be used multiple times.",
    )
    args = parser.parse_args()
    if not args.portfolios:
        args.portfolios = PORTFOLIOS_ALL
    return args


async def _generate(topic: str, verbose: bool = False) -> Dict[str, Any]:
    """Run the full graph for ``topic`` and return the final state.

    When ``verbose`` is ``True`` the orchestrator is executed using the
    streaming interface so that progress messages are emitted as nodes
    advance. Otherwise the graph runs silently.
    """

    from core.orchestrator import graph_orchestrator
    from core.state import State

    state = State(prompt=topic)
    if verbose:
        async for _ in graph_orchestrator.stream(state):
            pass
    else:
        await graph_orchestrator.run(state)
    return state.to_dict()


def save_markdown(output: Path, topic: str, payload: Dict[str, Any]) -> None:
    """Write the generated lecture payload to ``output`` in Markdown."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    markdown_body: str
    try:
        module = payload.get("modules", [])[-1]
        slides = [Slide(**s) for s in module.get("slides", [])]
        assessment = [AssessmentItem(**a) for a in module.get("assessment", [])]
        references = [Citation(**c) for c in module.get("references", [])]
        weave = WeaveResult(
            title=module.get("title", topic),
            learning_objectives=module.get("learning_objectives", []),
            duration_min=module.get("duration_min", 0),
            author=module.get("author"),
            date=module.get("date"),
            version=module.get("version"),
            summary=module.get("summary"),
            tags=module.get("tags"),
            prerequisites=module.get("prerequisites"),
            slides=slides or None,
            assessment=assessment or None,
            references=references or None,
        )
        citations = [Citation(**c) for c in payload.get("sources", [])]
        markdown_body = from_weave_result(weave, citations)
    except Exception:
        output_json = json.dumps(payload, indent=2)
        markdown_body = "```json\n" + output_json + "\n```"

    lines = [
        "# Lecture Output",
        f"Topic: {topic}",
        "",
        markdown_body,
        "",
        f"Generated at {timestamp} UTC",
    ]
    output.write_text("\n".join(lines) + "\n")


def main() -> None:
    """Entry point for console scripts."""
    args = parse_args()
    from observability import init_observability

    init_observability()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    for portfolio in args.portfolios:
        topic = f"{args.topic} for {portfolio}"
        if args.verbose:
            stream_messages("LLM response stream start")
        try:
            payload = asyncio.run(_generate(topic, verbose=args.verbose))
        except Exception as exc:  # pragma: no cover - defensive
            raise SystemExit(f"Error generating lecture: {exc}") from exc
        if args.verbose:
            stream_messages("LLM response stream complete: %s" % json.dumps(payload))
        output_name = f"{args.output.stem}_{slugify(portfolio)}{args.output.suffix}"
        output_path = args.output.parent / output_name
        save_markdown(output_path, topic, payload)


if __name__ == "__main__":
    main()
