"""
LegalMesh — Gradio Frontend
Multi-Agent Legal Research System
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import gradio as gr
import asyncio
import json


def research_legal_question(query: str) -> tuple:
    """Run multi-agent legal research and return results."""
    if not query.strip():
        return "Please enter a legal question.", "", "{}", ""

    from backend.agents.orchestrator import AgentOrchestrator

    async def run():
        status_log = []

        async def on_status(agent_name, status, detail, elapsed):
            icon = "🔄" if status == "running" else "✅" if status == "completed" else "❌"
            status_log.append(f"{icon} **{agent_name}**: {detail} ({int(elapsed*1000)}ms)")

        orchestrator = AgentOrchestrator(on_status_update=on_status)
        result = await orchestrator.research(query)
        return result, status_log

    result, status_log = asyncio.run(run())

    # Format synthesis
    synthesis = result["synthesis"].get("synthesis", "No results available.")

    # Format agent activity log
    agent_log = "\n\n".join(status_log)

    # Format classification
    cls = result.get("classification", {})
    classification_md = f"""
**Domain:** {cls.get('domain', 'N/A')}
**Jurisdiction:** {cls.get('jurisdiction_state', 'N/A')}
**Key Terms:** {', '.join(cls.get('key_terms', []))}
**Summary:** {cls.get('summary', 'N/A')}
"""

    # Stats
    stats = f"""
**Sources Consulted:** {result['synthesis'].get('sources_consulted', 0)}
**Agents Used:** {len([a for a in result['synthesis'].get('agents_used', []) if a])}
**Total Time:** {result['total_time_seconds']}s
"""

    return synthesis, agent_log, classification_md, stats


# Build Gradio interface
with gr.Blocks(
    title="LegalMesh — Multi-Agent Legal Research",
    theme=gr.themes.Soft(primary_hue="blue"),
    css="""
    .main-title { text-align: center; margin-bottom: 5px; }
    .subtitle { text-align: center; color: #666; margin-bottom: 20px; }
    """
) as demo:
    gr.Markdown("# ⚖️ LegalMesh", elem_classes=["main-title"])
    gr.Markdown("*Multi-Agent Legal Research System — 7 AI Agents × 7 Legal Datasets*", elem_classes=["subtitle"])

    with gr.Row():
        with gr.Column(scale=3):
            query_input = gr.Textbox(
                label="Describe your legal question in plain English",
                placeholder="e.g., My landlord won't return my security deposit in California...",
                lines=3,
            )
            with gr.Row():
                submit_btn = gr.Button("🔍 Research with All Agents", variant="primary", scale=3)
                clear_btn = gr.ClearButton(scale=1)

            gr.Examples(
                examples=[
                    ["My landlord won't return my security deposit in California. What are my rights?"],
                    ["Can my employer force me to sign a non-compete in Texas?"],
                    ["What federal consumer protection laws apply to defective products?"],
                    ["What are the immigration requirements for an H-1B visa transfer?"],
                    ["What are the zoning requirements for a home business in Portland, Oregon?"],
                ],
                inputs=query_input,
            )

        with gr.Column(scale=1):
            stats_output = gr.Markdown(label="📊 Stats")
            classification_output = gr.Markdown(label="🏷️ Classification")

    with gr.Tabs():
        with gr.TabItem("📋 Legal Analysis"):
            synthesis_output = gr.Markdown(label="Research Results")

        with gr.TabItem("🤖 Agent Activity Log"):
            agent_log_output = gr.Markdown(label="Agent Status")

    submit_btn.click(
        fn=research_legal_question,
        inputs=[query_input],
        outputs=[synthesis_output, agent_log_output, classification_output, stats_output],
    )

    clear_btn.add([query_input, synthesis_output, agent_log_output, classification_output, stats_output])

    gr.Markdown("""
    ---
    **Data Sources:** JusticeDAO (7 HF datasets) • TrustFoundry (8M+ docs) • Caselaw Access Project (6.7M cases) • FOLIO Ontology (18K concepts)

    *Built at LLM × Law Hackathon @ Stanford | Not legal advice*
    """)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=True)
