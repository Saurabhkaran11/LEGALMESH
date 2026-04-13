"""
Agent 4: TrustFoundry Legal Search Agent
Searches TrustFoundry's 8M+ laws, regulations, and cases via their API.
Provides verified legal context with citations.
"""

import httpx
from backend.config import TRUSTFOUNDRY_API_KEY, TRUSTFOUNDRY_BASE_URL


async def search_trustfoundry(classification: dict) -> dict:
    """Search TrustFoundry's legal database for relevant documents."""
    results = {
        "agent": "trustfoundry",
        "status": "success",
        "documents": [],
    }

    if not TRUSTFOUNDRY_API_KEY:
        return {
            "agent": "trustfoundry",
            "status": "skipped",
            "reason": "No TrustFoundry API key configured",
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
                    "Authorization": f"Bearer {TRUSTFOUNDRY_API_KEY}",
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
                        "type": doc.get("type", doc.get("doc_type", "unknown")),
                        "citation": doc.get("citation", ""),
                        "jurisdiction": doc.get("jurisdiction", state),
                        "text_preview": str(doc.get("text", doc.get("content", doc.get("snippet", ""))))[:500],
                        "url": doc.get("url", ""),
                        "relevance_score": doc.get("score", doc.get("relevance", 0)),
                        "source": "TrustFoundry API",
                    })
            elif resp.status_code == 401:
                results["status"] = "auth_error"
                results["error"] = "Invalid TrustFoundry API key"
            else:
                # Try alternative endpoint format
                resp2 = await client.get(
                    f"{TRUSTFOUNDRY_BASE_URL}/search",
                    params={"q": search_query, "limit": 10},
                    headers={"Authorization": f"Bearer {TRUSTFOUNDRY_API_KEY}"},
                )
                if resp2.status_code == 200:
                    data = resp2.json()
                    for doc in data.get("results", [])[:7]:
                        results["documents"].append({
                            "title": doc.get("title", "Untitled"),
                            "text_preview": str(doc.get("text", ""))[:500],
                            "source": "TrustFoundry API",
                        })
                else:
                    results["status"] = "api_error"
                    results["error"] = f"HTTP {resp.status_code}"

        except Exception as e:
            results["status"] = "error"
            results["error"] = str(e)

    if not results["documents"] and results["status"] == "success":
        results["status"] = "no_results"

    return results
