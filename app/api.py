"""FastAPI application for agentic demo."""

from __future__ import annotations

from fastapi import FastAPI
from web.router import router as web_router

from .graph import build_graph
from .mcp import MCP
from .persistence import (
    add_log,
    get_connection,
    init_db,
    read_versions,
    save_checkpoint,
)

app = FastAPI()
flow = build_graph()
app.include_router(web_router)
mcp = MCP()

# Database setup
conn = get_connection()
init_db(conn)

# TODO(#test_chat_persists_steps): rollback gracefully if persisting a
# checkpoint fails mid-conversation.


@app.post("/chat")
async def chat(input: str, run: str) -> dict:
    """Handle chat requests returning the final response.

    Parameters
    ----------
    input:
        Prompt provided by the user.
    run:
        Identifier grouping checkpoints and logs for this conversation.

    Returns
    -------
    dict
        Mapping containing the final ``response`` string.
    """

    result = await flow.arun(input)
    for step in result["messages"]:
        save_checkpoint(conn, run, step)
        add_log(conn, run, "INFO", step)
    return {"response": result["output"]}


@app.post("/mcp")
async def mcp_edit(payload: dict) -> dict:
    """Edit the persistent document via the MCP."""
    addition = payload.get("addition", "")
    text = mcp.edit(addition)
    return {"text": text}


# TODO(#test_versions_endpoint_returns_saved_versions): add authentication and
# pagination for version history responses.
@app.get("/versions")
async def versions(run: str) -> dict:
    """Return stored checkpoints for ``run``.

    Parameters
    ----------
    run:
        Identifier used when saving checkpoints via :func:`chat`.

    Returns
    -------
    dict
        Dictionary with a ``versions`` key mapping to an ordered list of
        version records.
    """

    rows = read_versions(conn, run)
    data = [{"version": int(row["version"]), "data": row["data"]} for row in rows]
    return {"versions": data}
