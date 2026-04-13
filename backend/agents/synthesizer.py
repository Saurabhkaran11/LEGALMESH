"""
Agent 5: Synthesizer Agent
Takes all results from the other agents and produces a comprehensive,
structured legal research summary using Claude.
"""

import json
import anthropic
from backend.config import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYNTHESIZER_PROMPT = """You are a legal research synthesizer. You have received research results from multiple specialized legal agents. Your job is to produce a comprehensive, structured legal analysis.

IMPORTANT: You are NOT providing legal advice. You are providing legal research and information.

Given the user's original question and the research results below, produce a structured response with these sections:

1. **Legal Issue Summary**: 2-3 sentence restatement of the legal issue
2. **Applicable Law**: Key statutes and regulations that apply, with citations
3. **Relevant Case Law**: Key court decisions that inform this issue, with case names and holdings
4. **Key Legal Principles**: The main legal rules and standards that govern this situation
5. **Action Steps**: Practical next steps the person can take (filing deadlines, required forms, where to seek help)
6. **Important Disclaimers**: Note that this is legal research, not legal advice

Format your response in clean markdown. Cite specific statutes and cases where available.
If the research returned limited results, acknowledge that and suggest additional resources.
"""


async def synthesize_results(
    query: str,
    classification: dict,
    statute_results: dict,
    case_results: dict,
    trustfoundry_results: dict,
    federal_register_results: dict = None,
    municipal_results: dict = None,
) -> dict:
    """Synthesize all agent results into a comprehensive legal analysis."""

    # Build context from all agents
    context_parts = []

    context_parts.append(f"## Classification\n{json.dumps(classification, indent=2)}")

    # Statutes
    if statute_results.get("state_laws"):
        context_parts.append("## State Laws Found")
        for law in statute_results["state_laws"]:
            context_parts.append(f"- **{law['title']}** ({law.get('state', 'Unknown state')}): {law['text']}")

    if statute_results.get("federal_statutes"):
        context_parts.append("## Federal Statutes Found")
        for statute in statute_results["federal_statutes"]:
            context_parts.append(f"- **{statute['title']}**: {statute['text']}")

    if statute_results.get("court_rules"):
        context_parts.append("## Court Rules Found")
        for rule in statute_results["court_rules"]:
            context_parts.append(f"- **{rule['title']}**: {rule['text']}")

    # Case law
    if case_results.get("cases"):
        context_parts.append("## Case Law Found")
        for case in case_results["cases"]:
            context_parts.append(
                f"- **{case['case_name']}** ({case.get('date', 'Unknown date')}, {case.get('court', 'Unknown court')})"
                f"\n  Citation: {case.get('citation', 'N/A')}"
                f"\n  Preview: {case['text_preview']}"
            )

    # TrustFoundry
    if trustfoundry_results.get("documents"):
        context_parts.append("## TrustFoundry Verified Legal Documents")
        for doc in trustfoundry_results["documents"]:
            context_parts.append(
                f"- **{doc['title']}** (Type: {doc.get('type', 'unknown')}, "
                f"Citation: {doc.get('citation', 'N/A')}): {doc['text_preview']}"
            )

    # Federal Register
    if federal_register_results and federal_register_results.get("regulations"):
        context_parts.append("## Federal Register Regulations")
        for reg in federal_register_results["regulations"]:
            context_parts.append(f"- **{reg['title']}**: {reg['text']}")

    # Municipal law
    if municipal_results and municipal_results.get("ordinances"):
        context_parts.append("## Municipal/Local Ordinances")
        for ord in municipal_results["ordinances"]:
            context_parts.append(f"- **{ord['title']}** ({ord.get('location', '')}): {ord['text']}")

    research_context = "\n\n".join(context_parts)

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"{SYNTHESIZER_PROMPT}\n\n"
                        f"## User's Original Question\n{query}\n\n"
                        f"## Research Results from Legal Agents\n{research_context}"
                    ),
                }
            ],
        )

        synthesis = message.content[0].text

        # Count sources
        source_count = (
            len(statute_results.get("state_laws", []))
            + len(statute_results.get("federal_statutes", []))
            + len(statute_results.get("court_rules", []))
            + len(case_results.get("cases", []))
            + len(trustfoundry_results.get("documents", []))
            + len((federal_register_results or {}).get("regulations", []))
            + len((municipal_results or {}).get("ordinances", []))
        )

        return {
            "agent": "synthesizer",
            "status": "success",
            "synthesis": synthesis,
            "sources_consulted": source_count,
            "agents_used": [
                "classifier",
                "statute_search",
                "case_search",
                "trustfoundry" if trustfoundry_results.get("documents") else None,
                "federal_register" if federal_register_results else None,
                "municipal_law" if municipal_results else None,
            ],
            "classification": classification,
        }

    except Exception as e:
        return {
            "agent": "synthesizer",
            "status": "error",
            "error": str(e),
            "synthesis": "Error generating synthesis. Raw results are still available above.",
        }
