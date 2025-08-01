"""FastAPI application for agentic demo."""

from __future__ import annotations

from fastapi import FastAPI
from web.router import router as web_router

from .graph import build_graph
from .mcp import MCP

app = FastAPI()
flow = build_graph()
app.include_router(web_router)
mcp = MCP()


@app.post("/chat")
async def chat(input: str) -> dict:
    """Handle chat requests returning the final response."""
    result = await flow.arun(input)
    return {"response": result["output"]}


@app.post("/mcp")
async def mcp_edit(payload: dict) -> dict:
    """Edit the persistent document via the MCP."""
    addition = payload.get("addition", "")
    text = mcp.edit(addition)
    return {"text": text}
