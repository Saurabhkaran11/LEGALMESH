"""
Agent 4: TrustFoundry Legal Search Agent
Searches TrustFoundry's 8M+ laws, regulations, and cases via their API.
Provides verified legal context with citations.
"""

import httpx
from backend.config import TRUSTFOUNDRY_BASE_URL


async def search_trustfoundry(classification: dict, api_key=None) -> dict:
    """Search TrustFoundry's legal database for relevant documents."""
    results = {
        "agent": "trustfoundry",
        "status": "success",
        "documents": [],
    }

    if not api_key:
        return {
            "agent": "trustfoundry",
            "status": "skipped",
            "reason": "No TrustFoundry key added",
            "documents": [],
        }

    key_terms = classification.get("key_terms", [])
    domain = classification.get("domain", "")
    state = classification.get("jurisdiction_state", "federal")
    summary = classification.get("summary", "")

    search_query = summary if summary else f"{domain} {' '.join(key_terms)}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # TrustFoundry search endpoint
            resp = await client.post(
                f"{TRUSTFOUNDRY_BASE_URL}/v1/search",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "query": search_query,
                    "jurisdiction": state if state != "federal" else None,
                    "limit": 10,
                    "include_text": True,
                },
            )

            if resp.status_code == 200:
                data = resp.json()
                docs = data.get("results", data.get("documents", data.get("hits", [])))
                for doc in docs[:7]:
                    results["documents"].append({
                        "title": doc.get("title", doc.get("name", "Untitled")),
                        "citation": doc.get("citation", ""),
                        "date": "",
                        "text": str(doc.get("text", doc.get("content", doc.get("snippet", ""))))[:500],
                        "url": doc.get("url", ""),
                        "source": "TrustFoundry",
                    })
            elif resp.status_code == 401:
                results["status"] = "auth_error"
            else:
                # Try alternative endpoint format
                resp2 = await client.get(
                    f"{TRUSTFOUNDRY_BASE_URL}/search",
                    params={"q": search_query, "limit": 10},
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                if resp2.status_code == 200:
                    data = resp2.json()
                    for doc in data.get("results", [])[:7]:
                        results["documents"].append({
                            "title": doc.get("title", "Untitled"),
                            "text": str(doc.get("text", ""))[:500],
                            "source": "TrustFoundry",
                        })
                else:
                    results["status"] = "api_error"

        except Exception:
            results["status"] = "error"

    if not results["documents"] and results["status"] == "success":
        results["status"] = "no_results"

    return results
