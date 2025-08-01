import asyncio
from types import SimpleNamespace
from unittest.mock import patch

import scripts.run_demo as rd


def test_parse_args_defaults():
    args = rd.parse_args(["--topic", "abc"])
    assert args.topic == "abc"
    assert args.mode == "basic"


def test_run_demo_basic_executes_flow():
    fake_graph = SimpleNamespace(run=lambda topic: {"output": f"out-{topic}"})
    with patch("scripts.run_demo.build_graph", return_value=fake_graph) as build:
        result = asyncio.run(rd.run_demo("hello", "basic"))
        build.assert_called_once_with(None)
        assert result["output"] == "out-hello"


def test_run_demo_overlay_builds_overlay():
    fake_graph = SimpleNamespace(run=lambda topic: {"output": "done"})
    with patch("scripts.run_demo.build_graph", return_value=fake_graph) as build:
        result = asyncio.run(rd.run_demo("hello", "overlay"))
        assert result["output"] == "done"
        build.assert_called_once()
        assert build.call_args[0][0] is not None


def test_main_prints_result(capsys):
    fake_graph = SimpleNamespace(run=lambda topic: {"output": "printed"})
    with patch("scripts.run_demo.build_graph", return_value=fake_graph):
        asyncio.run(rd.main(["--topic", "abc"]))
    captured = capsys.readouterr()
    assert "printed" in captured.out
