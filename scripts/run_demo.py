"""Run the FastAPI demo app."""

from __future__ import annotations

import uvicorn
from fastapi import FastAPI

from app.graph import build_graph

app = FastAPI()
flow = build_graph()


@app.post("/chat")
async def chat(input: str) -> dict:
    result = flow.run(input)
    return {"response": result["output"]}


if __name__ == "__main__":
    uvicorn.run("scripts.run_demo:app", host="0.0.0.0", port=8000)
