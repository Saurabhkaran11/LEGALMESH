"""
Agent 5: Synthesizer Agent
Takes all results from the other agents and produces a comprehensive,
structured legal research summary using Claude.
"""

import json

from backend.llm import ask

SYNTHESIZER_PROMPT = """You are a legal research synthesizer. You have received research results from multiple specialized legal agents. Your job is to produce a comprehensive, structured legal analysis.

IMPORTANT: You are NOT providing legal advice. You are providing legal research and information.

Given the user's original question and the research results below, produce a structured response with these sections:

1. **Legal Issue Summary**: 2-3 sentence restatement of the legal issue
2. **Applicable Law**: Key statutes and regulations that apply, with citations
3. **Relevant Case Law**: Key court decisions that inform this issue, with case names and holdings
4. **Key Legal Principles**: The main legal rules and standards that govern this situation
5. **Action Steps**: Practical next steps the person can take (filing deadlines, required forms, where to seek help)
6. **Important Disclaimers**: Note that this is legal research, not legal advice

Format your response in clean markdown.

Citation rules:
- Cite only the retrieved documents listed below, using their titles, citations and links.
- The retrieved sources cover federal regulations, the Federal Register, and sometimes case law. They usually do not include state statutes.
- You may explain well-known law from your general knowledge, but label it "From general knowledge, not retrieved here" and tell the reader to verify it.
- Never invent a case name, statute number, citation or link. If the documents do not answer the question, say so plainly and suggest where to look.
"""


async def synthesize_results(client, query: str, classification: dict, searches: list) -> dict:
    """Write the analysis from whatever the search agents found."""
    documents = [doc for search in searches for doc in search.get("documents", [])]
    context = "\n".join(
        f"- [{doc.get('source', '')}] {doc.get('title', '')} ({doc.get('citation') or 'no citation'}, {doc.get('date') or 'no date'})"
        f"\n  {doc.get('text', '')}\n  {doc.get('url', '')}"
        for doc in documents
    ) or "No documents were retrieved."

    synthesis = await ask(
        client,
        f"{SYNTHESIZER_PROMPT}\n\n## User's Original Question\n{query}\n\n"
        f"## Classification\n{json.dumps(classification, indent=2)}\n\n## Retrieved Documents\n{context}",
        effort="medium",
        max_tokens=16000,
    )
    return {
        "agent": "synthesizer",
        "status": "success",
        "synthesis": synthesis,
        "sources_consulted": len(documents),
        "agents_used": ["classifier"] + [s["agent"] for s in searches if s.get("documents")] + ["synthesizer"],
        "classification": classification,
    }
