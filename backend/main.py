"""
LegalMesh - multi-agent legal research.

A Claude agent classifies the question, 4 search agents run concurrently across
official legal sources, and a final Claude agent writes the cited analysis.
Each visitor supplies their own API keys. Keys are used for one request and are
never stored or logged.
"""

import json
import re
from pathlib import Path
from typing import Optional

import anthropic
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field, ValidationError

from backend.agents.orchestrator import AgentOrchestrator
from backend.llm import Keys, RefusedError

PAGE = Path(__file__).resolve().parent.parent / "frontend_react" / "index.html"
ANTHROPIC_KEY = re.compile(r"^sk-ant-[A-Za-z0-9_-]{20,300}$")

app = FastAPI(title="LegalMesh", description="Multi-agent legal research", version="2.0.0", docs_url=None, redoc_url=None, openapi_url=None)


class QueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    anthropic_key: str = Field(default="", max_length=400)
    courtlistener_token: Optional[str] = Field(default=None, max_length=400)
    trustfoundry_key: Optional[str] = Field(default=None, max_length=400)

    def __repr__(self) -> str:
        return "QueryRequest(<hidden>)"

    __str__ = __repr__


class ApiProblem(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        self.message = message


def keys_from(request: QueryRequest) -> Keys:
    key = request.anthropic_key.strip()
    if not key:
        raise ApiProblem(400, "Add your Anthropic API key.")
    if not ANTHROPIC_KEY.match(key):
        raise ApiProblem(400, "That does not look like an Anthropic API key. Keys start with sk-ant-.")
    return Keys(
        anthropic=key,
        courtlistener=(request.courtlistener_token or "").strip() or None,
        trustfoundry=(request.trustfoundry_key or "").strip() or None,
    )


def problem_from(error: Exception) -> ApiProblem:
    """Turn a failure into a message that is safe to show. Original errors can quote request details."""
    if isinstance(error, ApiProblem):
        return error
    if isinstance(error, anthropic.AuthenticationError):
        return ApiProblem(401, "Anthropic rejected that key. Check it and try again.")
    if isinstance(error, anthropic.PermissionDeniedError):
        return ApiProblem(403, "That key does not have access to this model.")
    if isinstance(error, anthropic.RateLimitError):
        return ApiProblem(429, "Your Anthropic account is over its rate limit. Try again shortly.")
    if isinstance(error, anthropic.APIStatusError) and error.status_code == 402:
        return ApiProblem(402, "Your Anthropic account is out of credit.")
    if isinstance(error, RefusedError):
        return ApiProblem(422, "Claude declined to answer this question. Try rewording it.")
    return ApiProblem(502, "Could not complete the research. Try again.")


def result_payload(result: dict) -> dict:
    return {
        "query": result["query"],
        "synthesis": result["synthesis"].get("synthesis", ""),
        "sources_consulted": result["synthesis"].get("sources_consulted", 0),
        "agents_used": [a for a in result["synthesis"].get("agents_used", []) if a],
        "total_time_seconds": result["total_time_seconds"],
        "classification": result["classification"],
    }


@app.get("/", include_in_schema=False)
async def page():
    return FileResponse(PAGE, media_type="text/html")


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/query")
async def query_legal(request: QueryRequest):
    """Submit a legal research query. Search agents run concurrently."""
    try:
        keys = keys_from(request)
        result = await AgentOrchestrator().research(request.query.strip(), keys)
    except Exception as error:
        problem = problem_from(error)
        return JSONResponse(status_code=problem.status, content={"error": problem.message})
    return {**result_payload(result), "agent_statuses": result["agent_statuses"]}


@app.websocket("/ws/query")
async def websocket_query(websocket: WebSocket):
    """Same as POST /api/query, with live agent status updates."""
    await websocket.accept()

    async def send_status(agent_name, status, detail, elapsed):
        await websocket.send_json({"type": "agent_status", "agent": agent_name, "status": status, "detail": detail, "elapsed_ms": int(elapsed * 1000)})

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                request = QueryRequest(**json.loads(raw))
            except (ValueError, TypeError, ValidationError):
                await websocket.send_json({"type": "error", "error": "Enter a question of up to 2,000 characters."})
                continue
            try:
                keys = keys_from(request)
                result = await AgentOrchestrator(on_status_update=send_status).research(request.query.strip(), keys)
                await websocket.send_json({"type": "result", **result_payload(result)})
            except WebSocketDisconnect:
                raise
            except Exception as error:
                await websocket.send_json({"type": "error", "error": problem_from(error).message})
    except WebSocketDisconnect:
        pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000)
