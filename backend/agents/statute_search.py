"""
Agent 2: Statute Search Agent
Searches JusticeDAO HuggingFace datasets for relevant statutes:
- ipfs_state_laws (51 jurisdictions, 10K-100K rows)
- ipfs_uscode (federal statutes, 100K-1M rows)
- ipfs_court_rules (procedural rules, <1K rows)
"""

import httpx
from backend.config import HF_TOKEN, DATASETS

HF_API_BASE = "https://datasets-server.huggingface.co"
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}


async def search_statutes(classification: dict) -> dict:
    """Search state laws and US Code for relevant statutes."""
    results = {
        "agent": "statute_search",
        "status": "success",
        "state_laws": [],
        "federal_statutes": [],
        "court_rules": [],
    }

    key_terms = classification.get("key_terms", [])
    state = classification.get("jurisdiction_state", "federal")
    search_query = " ".join(key_terms)

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Search state laws
        try:
            resp = await client.get(
                f"{HF_API_BASE}/search",
                params={
                    "dataset": DATASETS["state_laws"],
                    "config": "default",
                    "split": "train",
                    "query": search_query,
                    "offset": 0,
                    "length": 10,
                },
                headers=HEADERS,
            )
            if resp.status_code == 200:
                data = resp.json()
                rows = data.get("rows", [])
                for row in rows[:5]:
                    r = row.get("row", {})
                    results["state_laws"].append({
                        "title": r.get("title", r.get("name", "Untitled")),
                        "text": str(r.get("text", r.get("content", "")))[:500],
                        "state": r.get("state", state),
                        "cid": r.get("cid", ""),
                        "source": "justicedao/ipfs_state_laws",
                    })
        except Exception as e:
            results["state_laws_error"] = str(e)

        # Search US Code
        try:
            resp = await client.get(
                f"{HF_API_BASE}/search",
                params={
                    "dataset": DATASETS["uscode"],
                    "config": "default",
                    "split": "train",
                    "query": search_query,
                    "offset": 0,
                    "length": 10,
                },
                headers=HEADERS,
            )
            if resp.status_code == 200:
                data = resp.json()
                rows = data.get("rows", [])
                for row in rows[:5]:
                    r = row.get("row", {})
                    results["federal_statutes"].append({
                        "title": r.get("title", r.get("section", "Untitled")),
                        "text": str(r.get("text", r.get("content", "")))[:500],
                        "usc_title": r.get("usc_title", ""),
                        "section": r.get("section", ""),
                        "cid": r.get("cid", ""),
                        "source": "justicedao/ipfs_uscode",
                    })
        except Exception as e:
            results["uscode_error"] = str(e)

        # Search court rules
        try:
            resp = await client.get(
                f"{HF_API_BASE}/search",
                params={
                    "dataset": DATASETS["court_rules"],
                    "config": "default",
                    "split": "train",
                    "query": search_query,
                    "offset": 0,
                    "length": 5,
                },
                headers=HEADERS,
            )
            if resp.status_code == 200:
                data = resp.json()
                rows = data.get("rows", [])
                for row in rows[:3]:
                    r = row.get("row", {})
                    results["court_rules"].append({
                        "title": r.get("title", r.get("name", "Untitled")),
                        "text": str(r.get("text", r.get("content", "")))[:500],
                        "state": r.get("state", ""),
                        "cid": r.get("cid", ""),
                        "source": "justicedao/ipfs_court_rules",
                    })
        except Exception as e:
            results["court_rules_error"] = str(e)

    total = len(results["state_laws"]) + len(results["federal_statutes"]) + len(results["court_rules"])
    if total == 0:
        results["status"] = "no_results"

    return results


async def search_federal_register(classification: dict) -> dict:
    """Search Federal Register for relevant regulations."""
    key_terms = classification.get("key_terms", [])
    search_query = " ".join(key_terms)

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(
                f"{HF_API_BASE}/search",
                params={
                    "dataset": DATASETS["federal_register"],
                    "config": "default",
                    "split": "train",
                    "query": search_query,
                    "offset": 0,
                    "length": 5,
                },
                headers=HEADERS,
            )
            if resp.status_code == 200:
                data = resp.json()
                rows = data.get("rows", [])
                return {
                    "agent": "federal_register",
                    "status": "success",
                    "regulations": [
                        {
                            "title": row.get("row", {}).get("title", "Untitled"),
                            "text": str(row.get("row", {}).get("text", ""))[:500],
                            "source": "justicedao/ipfs_federal_register",
                        }
                        for row in rows[:5]
                    ],
                }
        except Exception as e:
            return {"agent": "federal_register", "status": "error", "error": str(e)}

    return {"agent": "federal_register", "status": "no_results", "regulations": []}
