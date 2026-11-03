"""
Search agents backed by official public APIs. Each returns the same shape:
{"agent", "status", "documents": [{"title", "citation", "date", "text", "url", "source"}]}
"""

import html
import re

import httpx

TIMEOUT = httpx.Timeout(20.0)
LIMIT = 6
TAG = re.compile(r"<[^>]+>")


def _clean(text) -> str:
    return html.unescape(TAG.sub("", str(text or ""))).strip()[:600]


def _terms(classification: dict) -> str:
    terms = classification.get("key_terms") or []
    return " ".join(str(t) for t in terms[:4]) or str(classification.get("summary", ""))


def _result(agent: str, documents: list) -> dict:
    return {"agent": agent, "status": "success" if documents else "no_results", "documents": documents}


async def search_regulations(classification: dict) -> dict:
    """Current federal regulations from the eCFR. No key needed."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.get(
            "https://www.ecfr.gov/api/search/v1/results",
            params={"query": _terms(classification), "per_page": LIMIT},
            follow_redirects=True,
        )
    resp.raise_for_status()
    documents = []
    for row in resp.json().get("results", [])[:LIMIT]:
        place = row.get("hierarchy") or {}
        heading = row.get("headings") or {}
        title, section = place.get("title"), place.get("section")
        documents.append({
            "title": _clean(heading.get("section") or heading.get("part") or "Federal regulation"),
            "citation": f"{title} CFR § {section}" if title and section else "",
            "date": row.get("starts_on", ""),
            "text": _clean(row.get("full_text_excerpt")),
            "url": f"https://www.ecfr.gov/current/title-{title}/section-{section}" if title and section else "",
            "source": "eCFR",
        })
    return _result("regulations", documents)


async def search_federal_register(classification: dict) -> dict:
    """Rules, proposed rules and notices from the Federal Register. No key needed."""
    params = [("conditions[term]", _terms(classification)), ("per_page", LIMIT), ("order", "relevance")]
    params += [("fields[]", f) for f in ("title", "abstract", "document_number", "html_url", "publication_date", "type", "agency_names")]
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.get("https://www.federalregister.gov/api/v1/documents.json", params=params, follow_redirects=True)
    resp.raise_for_status()
    documents = [{
        "title": _clean(row.get("title")),
        "citation": f"FR Doc. {row.get('document_number', '')}",
        "date": row.get("publication_date", ""),
        "text": _clean(row.get("abstract")),
        "url": row.get("html_url", ""),
        "source": "Federal Register",
    } for row in resp.json().get("results", [])[:LIMIT]]
    return _result("federal_register", documents)


async def search_case_law(classification: dict, token=None) -> dict:
    """Court opinions from CourtListener, using the visitor's free API token."""
    if not token:
        return {"agent": "case_search", "status": "skipped", "reason": "No CourtListener token added", "documents": []}
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.get(
            "https://www.courtlistener.com/api/rest/v4/search/",
            params={"q": _terms(classification), "type": "o"},
            headers={"Authorization": f"Token {token}"},
            follow_redirects=True,
        )
    if resp.status_code in (401, 403):
        return {"agent": "case_search", "status": "auth_error", "documents": []}
    resp.raise_for_status()
    documents = []
    for row in resp.json().get("results", [])[:LIMIT]:
        opinions = row.get("opinions") or [{}]
        citations = row.get("citation") or []
        path = row.get("absolute_url", "")
        documents.append({
            "title": _clean(row.get("caseName")),
            "citation": ", ".join(str(c) for c in citations[:2]),
            "date": row.get("dateFiled", ""),
            "text": _clean(opinions[0].get("snippet")),
            "url": f"https://www.courtlistener.com{path}" if path else "",
            "source": f"CourtListener ({_clean(row.get('court'))})",
        })
    return _result("case_search", documents)
