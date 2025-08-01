from unittest.mock import patch

from app.mcp import MCP


def test_mcp_edit_updates_text():
    mcp = MCP()
    with patch("app.overlay_agent.OverlayAgent.__call__", return_value="new") as mock:
        result = mcp.edit("add")
    assert result == "new"
    assert mcp.text == "new"
    mock.assert_called_once_with("", "add")
