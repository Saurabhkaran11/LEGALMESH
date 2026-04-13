"""
Agent Orchestrator
Coordinates all MCP agents in parallel, tracks their status,
and produces the final unified result.
Designed to be Thenvoi-ready: if THENVOI_API_KEY is set, agents
communicate through the Thenvoi Agentic Mesh.
"""

import asyncio
import time
from typing import Callable, Optional

from backend.agents.classifier import classify_legal_query
from backend.agents.statute_search import search_statutes, search_federal_register
from backend.agents.case_search import search_case_law, search_municipal_law
from backend.agents.trustfoundry_search import search_trustfoundry
from backend.agents.synthesizer import synthesize_results


class AgentOrchestrator:
    """Orchestrates multi-agent legal research pipeline."""

    def __init__(self, on_status_update: Optional[Callable] = None):
        self.on_status_update = on_status_update
        self.agent_statuses = {}
        self.start_time = None

    async def _update_status(self, agent_name: str, status: str, detail: str = ""):
        """Track and broadcast agent status updates."""
        elapsed = time.time() - self.start_time if self.start_time else 0
        self.agent_statuses[agent_name] = {
            "status": status,
            "detail": detail,
            "elapsed_ms": int(elapsed * 1000),
        }
        if self.on_status_update:
            await self.on_status_update(agent_name, status, detail, elapsed)

    async def _run_agent(self, name: str, coro):
        """Run a single agent with status tracking."""
        await self._update_status(name, "running", f"Agent {name} started")
        try:
            result = await coro
            status = result.get("status", "success")
            await self._update_status(name, "completed", f"Found {self._count_results(result)} results")
            return result
        except Exception as e:
            await self._update_status(name, "error", str(e))
            return {"agent": name, "status": "error", "error": str(e)}

    def _count_results(self, result: dict) -> int:
        """Count how many results an agent returned."""
        count = 0
        for key, val in result.items():
            if isinstance(val, list):
                count += len(val)
        return count

    async def research(self, query: str) -> dict:
        """Run the full multi-agent legal research pipeline."""
        self.start_time = time.time()

        # Step 1: Classify the query
        await self._update_status("classifier", "running", "Classifying legal domain...")
        classification = await classify_legal_query(query)
        await self._update_status("classifier", "completed", f"Domain: {classification.get('domain', 'unknown')}")

        # Step 2: Run all search agents in parallel
        await self._update_status("parallel_search", "running", "Launching search agents in parallel...")

        statute_task = self._run_agent("statute_search", search_statutes(classification))
        case_task = self._run_agent("case_search", search_case_law(classification))
        trustfoundry_task = self._run_agent("trustfoundry", search_trustfoundry(classification))
        federal_register_task = self._run_agent("federal_register", search_federal_register(classification))
        municipal_task = self._run_agent("municipal_law", search_municipal_law(classification))

        statute_results, case_results, trustfoundry_results, federal_register_results, municipal_results = (
            await asyncio.gather(
                statute_task,
                case_task,
                trustfoundry_task,
                federal_register_task,
                municipal_task,
            )
        )

        await self._update_status("parallel_search", "completed", "All search agents finished")

        # Step 3: Synthesize everything
        await self._update_status("synthesizer", "running", "Synthesizing legal analysis...")
        synthesis = await synthesize_results(
            query=query,
            classification=classification,
            statute_results=statute_results,
            case_results=case_results,
            trustfoundry_results=trustfoundry_results,
            federal_register_results=federal_register_results,
            municipal_results=municipal_results,
        )
        await self._update_status("synthesizer", "completed", "Analysis complete")

        total_time = time.time() - self.start_time

        return {
            "query": query,
            "classification": classification,
            "statute_results": statute_results,
            "case_results": case_results,
            "trustfoundry_results": trustfoundry_results,
            "federal_register_results": federal_register_results,
            "municipal_results": municipal_results,
            "synthesis": synthesis,
            "agent_statuses": self.agent_statuses,
            "total_time_seconds": round(total_time, 2),
        }
