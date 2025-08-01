"""Command-line interface to run the demo graph."""

from __future__ import annotations

import argparse
import asyncio
import os
from typing import Optional

from app.graph import build_graph
from app.overlay_agent import OverlayAgent


# ---------------------------------------------------------------------------
# argument parsing
# ---------------------------------------------------------------------------


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    """Parse command line arguments.

    Parameters
    ----------
    argv:
        List of argument strings. If ``None`` the arguments are taken from
        ``sys.argv``.

    Returns
    -------
    argparse.Namespace
        Namespace with ``topic`` and ``mode`` attributes.
    """
    parser = argparse.ArgumentParser(description="Run agentic demo")
    parser.add_argument(
        "--topic",
        required=True,
        help="Topic to generate material for.",
    )
    parser.add_argument(
        "--mode",
        choices=["basic", "overlay"],
        default="basic",
        help="Execution mode: 'basic' or 'overlay'",
    )
    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# core execution helpers
# ---------------------------------------------------------------------------


async def run_demo(topic: str, mode: str) -> dict[str, str]:
    """Run the conversation flow asynchronously and return the result."""
    overlay = OverlayAgent() if mode == "overlay" else None
    flow = build_graph(overlay)
    return await asyncio.to_thread(flow.run, topic)


async def main(argv: Optional[list[str]] = None) -> None:
    """Entry point for the demo script."""
    args = parse_args(argv)
    if not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY not set - using placeholder responses.")
    result = await run_demo(args.topic, args.mode)
    print(result["output"])


if __name__ == "__main__":  # pragma: no cover - manual execution only
    asyncio.run(main())
