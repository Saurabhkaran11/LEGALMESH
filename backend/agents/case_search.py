"""
Agent 3: Case Law Search Agent
Searches Caselaw Access Project for relevant court opinions.
Uses the pre-computed embeddings dataset (10M-100M rows) for semantic search,
and the full case text dataset (1M-10M rows) for retrieving case details.
"""

import httpx
from backend.config import HF_TOKEN, DATASETS

HF_API_BASE = "https://datasets-server.huggingface.co"
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}


async def search_case_law(classification: dict) -> dict:
    """Search case law using the HuggingFace datasets API."""
    results = {
        "agent": "case_search",
        "status": "success",
        "cases": [],
    }

    key_terms = classification.get("key_terms", [])
    domain = classification.get("domain", "")
    state = classification.get("jurisdiction_state", "federal")
    summary = classification.get("summary", "")

    # Build a rich search query combining terms and summary
    search_query = f"{domain} {' '.join(key_terms)} {state}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Search the caselaw dataset
        try:
            resp = await client.get(
                f"{HF_API_BASE}/search",
                params={
                    "dataset": DATASETS["caselaw"],
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
                for row in rows[:7]:
                    r = row.get("row", {})
                    case_entry = {
                        "case_name": r.get("name_abbreviation", r.get("name", r.get("title", "Unknown Case"))),
                        "court": r.get("court", r.get("court_name", "")),
                        "date": r.get("decision_date", r.get("date", "")),
                        "citation": r.get("citation", r.get("citations", "")),
                        "jurisdiction": r.get("jurisdiction", r.get("state", state)),
                        "text_preview": str(r.get("text", r.get("opinion", r.get("content", ""))))[:600],
                        "cid": r.get("cid", ""),
                        "source": "justicedao/ipfs_caselaw_access_project",
                    }
                    # Clean up citation if it's a list/dict
                    if isinstance(case_entry["citation"], (list, dict)):
                        case_entry["citation"] = str(case_entry["citation"])
                    results["cases"].append(case_entry)
        except Exception as e:
            results["search_error"] = str(e)

    if not results["cases"]:
        results["status"] = "no_results"

    return results


async def search_municipal_law(classification: dict) -> dict:
    """Search municipal/county law for local ordinances."""
    key_terms = classification.get("key_terms", [])
    search_query = " ".join(key_terms)

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(
                f"{HF_API_BASE}/search",
                params={
                    "dataset": DATASETS["municipal_law"],
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
                    "agent": "municipal_law",
                    "status": "success",
                    "ordinances": [
                        {
                            "title": row.get("row", {}).get("title", row.get("row", {}).get("name", "Untitled")),
                            "text": str(row.get("row", {}).get("text", row.get("row", {}).get("content", "")))[:500],
                            "location": row.get("row", {}).get("location", ""),
                            "source": "justicedao/american_municipal_law",
                        }
                        for row in rows[:5]
                    ],
                }
        except Exception as e:
            return {"agent": "municipal_law", "status": "error", "error": str(e)}

    return {"agent": "municipal_law", "status": "no_results", "ordinances": []}
