"""
Agent 1: Legal Domain Classifier
Uses FOLIO taxonomy concepts + Claude to classify the user's legal question
into domain, jurisdiction, and key legal concepts.
"""

import anthropic
from backend.config import ANTHROPIC_API_KEY, LEGAL_DOMAINS, US_STATES

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

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


async def classify_legal_query(query: str) -> dict:
    """Classify a user's legal question into structured legal metadata."""
    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[
                {"role": "user", "content": f"{CLASSIFIER_PROMPT}\n\nUser's question: {query}"}
            ],
        )
        import json
        response_text = message.content[0].text
        # Extract JSON from response
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        result = json.loads(response_text.strip())

        # Validate domain
        if result.get("domain") not in LEGAL_DOMAINS:
            result["domain"] = "consumer"  # fallback

        # Validate state
        state = result.get("jurisdiction_state", "federal")
        if state not in US_STATES and state != "federal":
            result["jurisdiction_state"] = "federal"

        result["agent"] = "classifier"
        result["status"] = "success"
        return result

    except Exception as e:
        return {
            "agent": "classifier",
            "status": "error",
            "error": str(e),
            "domain": "consumer",
            "sub_domains": [],
            "jurisdiction_state": "federal",
            "key_terms": query.split()[:5],
            "summary": query,
        }
