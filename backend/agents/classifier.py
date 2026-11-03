"""
Agent 1: Legal Domain Classifier
Uses Claude to classify the user's legal question into a domain,
jurisdiction, and key legal terms.
"""

import json

from backend.config import LEGAL_DOMAINS, US_STATES
from backend.llm import ask

CLASSIFIER_PROMPT = """You are a legal domain classifier. Given a user's legal question, extract:

1. **domain**: The primary legal domain (one of: employment, housing, family, consumer, immigration, criminal, personal_injury, business, tax, civil_rights)
2. **sub_domains**: Up to 3 specific sub-topics within that domain
3. **jurisdiction_state**: The U.S. state mentioned or implied (2-letter code, e.g., "CA", "TX"). If none mentioned, return "federal"
4. **key_terms**: 5-8 specific legal terms to search for in statutes and case law
5. **summary**: A 1-sentence restatement of the legal issue in formal legal language

Respond ONLY in valid JSON format:
{
    "domain": "...",
    "sub_domains": ["...", "..."],
    "jurisdiction_state": "...",
    "key_terms": ["...", "..."],
    "summary": "..."
}
"""


async def classify_legal_query(client, query: str) -> dict:
    """Classify a user's legal question. API errors propagate so the caller can report them."""
    response_text = await ask(client, f"{CLASSIFIER_PROMPT}\n\nUser's question: {query}", effort="low", max_tokens=4000)
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0]
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0]

    try:
        result = json.loads(response_text.strip())
        if not isinstance(result, dict):
            raise ValueError("not an object")
    except ValueError:
        return {
            "agent": "classifier",
            "status": "fallback",
            "domain": "consumer",
            "sub_domains": [],
            "jurisdiction_state": "federal",
            "key_terms": query.split()[:5],
            "summary": query,
        }

    if result.get("domain") not in LEGAL_DOMAINS:
        result["domain"] = "consumer"
    state = result.get("jurisdiction_state", "federal")
    if state not in US_STATES and state != "federal":
        result["jurisdiction_state"] = "federal"
    result["agent"] = "classifier"
    result["status"] = "success"
    return result
