"""FastAPI application for agentic demo."""

from __future__ import annotations

from fastapi import FastAPI

from .graph import build_graph

app = FastAPI()
flow = build_graph()


@app.post("/chat")
async def chat(input: str) -> dict:
    """Handle chat requests returning the final response."""
    result = await flow.arun(input)
    return {"response": result["output"]}
