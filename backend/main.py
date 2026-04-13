"""
LegalMesh - Multi-Agent Legal Research System
FastAPI Backend

Coordinates 5+ MCP agents across 7 legal datasets to answer legal questions:
- FOLIO Legal Classifier (18K legal concepts)
- Statute Search (state laws + US Code + court rules)
- Case Law Search (6.7M cases, 360 years)
- TrustFoundry (8M+ verified legal documents)
- Federal Register Scanner (1M+ regulations)
- Municipal Law Search (county/city ordinances)
- Claude Synthesizer (produces final analysis)
"""

import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend.agents.orchestrator import AgentOrchestrator

app = FastAPI(
    title="LegalMesh",
    description="Multi-Agent Legal Research System — Hackathon @ Stanford LLM x Law",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    query: str
    synthesis: str
    sources_consulted: int
    agents_used: list
    total_time_seconds: float
    classification: dict
    raw_results: dict


@app.get("/")
async def root():
    return {
        "name": "LegalMesh",
        "description": "Multi-Agent Legal Research System",
        "version": "1.0.0",
        "agents": [
            "FOLIO Legal Classifier",
            "Statute Search (HuggingFace: state laws, US Code, court rules)",
            "Case Law Search (HuggingFace: Caselaw Access Project)",
            "TrustFoundry (8M+ legal documents)",
            "Federal Register Scanner",
            "Municipal Law Search",
            "Claude Synthesizer",
        ],
        "datasets": [
            "justicedao/ipfs_state_laws",
            "justicedao/ipfs_uscode",
            "justicedao/ipfs_court_rules",
            "justicedao/ipfs_caselaw_access_project",
            "justicedao/ipfs_federal_register",
            "justicedao/american_municipal_law",
            "justicedao/Caselaw_Access_Project_embeddings",
        ],
        "endpoints": {
            "POST /api/query": "Submit a legal research query",
            "WS /ws/query": "WebSocket for real-time agent status updates",
            "GET /api/health": "Health check",
        },
    }


@app.get("/api/health")
async def health():
    return {"status": "ok", "agents": 7, "datasets": 7}


@app.post("/api/query")
async def query_legal(request: QueryRequest):
    """Submit a legal research query. All agents run in parallel."""
    orchestrator = AgentOrchestrator()
    result = await orchestrator.research(request.query)

    return {
        "query": result["query"],
        "synthesis": result["synthesis"].get("synthesis", ""),
        "sources_consulted": result["synthesis"].get("sources_consulted", 0),
        "agents_used": [a for a in result["synthesis"].get("agents_used", []) if a],
        "total_time_seconds": result["total_time_seconds"],
        "classification": result["classification"],
        "raw_results": {
            "statutes": result["statute_results"],
            "cases": result["case_results"],
            "trustfoundry": result["trustfoundry_results"],
            "federal_register": result["federal_register_results"],
            "municipal": result["municipal_results"],
        },
        "agent_statuses": result["agent_statuses"],
    }


@app.websocket("/ws/query")
async def websocket_query(websocket: WebSocket):
    """WebSocket endpoint for real-time agent status updates during research."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            request = json.loads(data)
            query = request.get("query", "")

            if not query:
                await websocket.send_json({"error": "No query provided"})
                continue

            # Create orchestrator with WebSocket status callback
            async def send_status(agent_name, status, detail, elapsed):
                await websocket.send_json({
                    "type": "agent_status",
                    "agent": agent_name,
                    "status": status,
                    "detail": detail,
                    "elapsed_ms": int(elapsed * 1000),
                })

            orchestrator = AgentOrchestrator(on_status_update=send_status)
            result = await orchestrator.research(query)

            # Send final result
            await websocket.send_json({
                "type": "result",
                "query": result["query"],
                "synthesis": result["synthesis"].get("synthesis", ""),
                "sources_consulted": result["synthesis"].get("sources_consulted", 0),
                "agents_used": [a for a in result["synthesis"].get("agents_used", []) if a],
                "total_time_seconds": result["total_time_seconds"],
                "classification": result["classification"],
            })

    except WebSocketDisconnect:
        pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
