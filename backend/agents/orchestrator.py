"""
Agent Orchestrator
Runs the classifier, then the search agents concurrently, then the synthesizer,
tracking each agent's status along the way.
"""

import asyncio
import time
from typing import Callable, Optional

from backend.agents.classifier import classify_legal_query
from backend.agents.searches import search_case_law, search_federal_register, search_regulations
from backend.agents.trustfoundry_search import search_trustfoundry
from backend.agents.synthesizer import synthesize_results
from backend.llm import Keys, make_client


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
            if result.get("status") == "skipped":
                await self._update_status(name, "completed", result.get("reason", "Skipped"))
            elif result.get("status") in ("error", "auth_error", "api_error"):
                await self._update_status(name, "error", "This source could not be searched")
            elif result.get("status") == "no_results":
                await self._update_status(name, "completed", "No matching results")
            else:
                await self._update_status(name, "completed", f"Found {self._count_results(result)} results")
            return result
        except Exception:
            # One failing source must not stop the query. The message is hidden because it can quote request details.
            await self._update_status(name, "error", "This source could not be searched")
            return {"agent": name, "status": "error"}

    def _count_results(self, result: dict) -> int:
        """Count how many results an agent returned."""
        count = 0
        for key, val in result.items():
            if isinstance(val, list):
                count += len(val)
        return count

    async def research(self, query: str, keys: Keys) -> dict:
        """Run the full multi-agent legal research pipeline."""
        self.start_time = time.time()
        client = make_client(keys.anthropic)

        # Step 1: Classify the query
        await self._update_status("classifier", "running", "Classifying legal domain...")
        classification = await classify_legal_query(client, query)
        await self._update_status("classifier", "completed", f"Domain: {classification.get('domain', 'unknown')}")

        # Step 2: Run all search agents in parallel
        await self._update_status("parallel_search", "running", "Launching search agents in parallel...")

        regulations, federal_register, cases, trustfoundry = await asyncio.gather(
            self._run_agent("regulations", search_regulations(classification)),
            self._run_agent("federal_register", search_federal_register(classification)),
            self._run_agent("case_search", search_case_law(classification, keys.courtlistener)),
            self._run_agent("trustfoundry", search_trustfoundry(classification, keys.trustfoundry)),
        )

        await self._update_status("parallel_search", "completed", "All search agents finished")

        # Step 3: Synthesize everything
        await self._update_status("synthesizer", "running", "Synthesizing legal analysis...")
        synthesis = await synthesize_results(client, query, classification, [regulations, federal_register, cases, trustfoundry])
        await self._update_status("synthesizer", "completed", "Analysis complete")

        total_time = time.time() - self.start_time

        return {
            "query": query,
            "classification": classification,
            "synthesis": synthesis,
            "agent_statuses": self.agent_statuses,
            "total_time_seconds": round(total_time, 2),
        }
