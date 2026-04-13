"""
LegalMesh — Streamlit Frontend
Multi-Agent Legal Research System
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import asyncio
import time
import json

st.set_page_config(
    page_title="LegalMesh — Multi-Agent Legal Research",
    page_icon="⚖️",
    layout="wide",
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1a1a2e;
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        margin-top: -10px;
        margin-bottom: 30px;
    }
    .agent-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        margin: 8px 0;
        border-left: 4px solid #ccc;
    }
    .agent-running { border-left-color: #ffc107; background: #fff9e6; }
    .agent-completed { border-left-color: #28a745; background: #f0fff0; }
    .agent-error { border-left-color: #dc3545; background: #fff0f0; }
    .source-badge {
        display: inline-block;
        background: #e9ecef;
        border-radius: 20px;
        padding: 4px 12px;
        margin: 3px;
        font-size: 0.8rem;
    }
    .stat-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        padding: 20px;
        color: white;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<p class="main-header">⚖️ LegalMesh</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Multi-Agent Legal Research System — 7 AI Agents × 7 Legal Datasets × Real-Time Analysis</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("🤖 Agent Network")
    st.markdown("""
    **Active Agents:**
    1. 🏷️ FOLIO Legal Classifier
    2. 📜 Statute Search (State + Federal)
    3. ⚖️ Case Law Search (6.7M cases)
    4. 🔍 TrustFoundry (8M+ docs)
    5. 📋 Federal Register Scanner
    6. 🏛️ Municipal Law Search
    7. 🧠 Claude Synthesizer
    """)
    st.divider()
    st.markdown("""
    **Data Sources:**
    - JusticeDAO HuggingFace (7 datasets)
    - TrustFoundry API (8M+ docs)
    - Caselaw Access Project (360 years)
    - FOLIO Ontology (18K concepts)
    """)
    st.divider()
    st.markdown("*Built at LLM × Law Hackathon @ Stanford*")

# Example queries
st.markdown("**Try these examples:**")
examples = [
    "My landlord won't return my security deposit in California. What are my rights?",
    "Can my employer force me to sign a non-compete in Texas?",
    "What are the zoning requirements for a home business in Portland, Oregon?",
    "I received a defective product and the company won't issue a refund. What federal consumer protection laws apply?",
    "What are the immigration requirements for an H-1B visa transfer?",
]
example_cols = st.columns(len(examples))
selected_example = None
for i, ex in enumerate(examples):
    with example_cols[i]:
        if st.button(ex[:40] + "...", key=f"ex_{i}", use_container_width=True):
            selected_example = ex

# Query input
query = st.text_area(
    "Describe your legal question in plain English:",
    value=selected_example or "",
    height=100,
    placeholder="e.g., My landlord hasn't returned my security deposit after 30 days in California...",
)

if st.button("🔍 Research with All Agents", type="primary", use_container_width=True):
    if not query.strip():
        st.warning("Please enter a legal question.")
    else:
        # Create columns for agent status and results
        status_col, results_col = st.columns([1, 2])

        with status_col:
            st.subheader("🤖 Agent Activity")
            agent_placeholders = {
                "classifier": st.empty(),
                "statute_search": st.empty(),
                "case_search": st.empty(),
                "trustfoundry": st.empty(),
                "federal_register": st.empty(),
                "municipal_law": st.empty(),
                "synthesizer": st.empty(),
            }

            # Show initial status
            agent_labels = {
                "classifier": "🏷️ Legal Classifier",
                "statute_search": "📜 Statute Search",
                "case_search": "⚖️ Case Law Search",
                "trustfoundry": "🔍 TrustFoundry",
                "federal_register": "📋 Federal Register",
                "municipal_law": "🏛️ Municipal Law",
                "synthesizer": "🧠 Synthesizer",
            }
            for key, ph in agent_placeholders.items():
                ph.markdown(f'<div class="agent-card">{agent_labels[key]}: ⏳ Waiting...</div>', unsafe_allow_html=True)

        with results_col:
            results_placeholder = st.empty()
            results_placeholder.info("🔄 Running multi-agent research pipeline...")

        # Run the research
        from backend.agents.orchestrator import AgentOrchestrator

        async def run_research():
            status_updates = []

            async def on_status(agent_name, status, detail, elapsed):
                status_updates.append((agent_name, status, detail, elapsed))
                if agent_name in agent_placeholders:
                    icon = "🔄" if status == "running" else "✅" if status == "completed" else "❌"
                    css_class = f"agent-{status}"
                    label = agent_labels.get(agent_name, agent_name)
                    agent_placeholders[agent_name].markdown(
                        f'<div class="agent-card {css_class}">{icon} {label}: {detail} ({int(elapsed*1000)}ms)</div>',
                        unsafe_allow_html=True
                    )

            orchestrator = AgentOrchestrator(on_status_update=on_status)
            return await orchestrator.research(query)

        result = asyncio.run(run_research())

        # Update final agent statuses
        for key, ph in agent_placeholders.items():
            agent_status = result.get("agent_statuses", {}).get(key, {})
            status = agent_status.get("status", "completed")
            detail = agent_status.get("detail", "Done")
            elapsed = agent_status.get("elapsed_ms", 0)
            icon = "✅" if status == "completed" else "❌"
            css_class = f"agent-{status}"
            label = agent_labels.get(key, key)
            ph.markdown(
                f'<div class="agent-card {css_class}">{icon} {label}: {detail} ({elapsed}ms)</div>',
                unsafe_allow_html=True
            )

        # Show results
        with results_col:
            results_placeholder.empty()

            # Stats row
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Sources Consulted", result["synthesis"].get("sources_consulted", 0))
            with c2:
                active_agents = [a for a in result["synthesis"].get("agents_used", []) if a]
                st.metric("Agents Used", len(active_agents))
            with c3:
                st.metric("Total Time", f"{result['total_time_seconds']}s")

            # Classification
            classification = result.get("classification", {})
            st.markdown(f"""
            **Domain:** `{classification.get('domain', 'N/A')}` |
            **Jurisdiction:** `{classification.get('jurisdiction_state', 'N/A')}` |
            **Key Terms:** {', '.join(f'`{t}`' for t in classification.get('key_terms', []))}
            """)

            st.divider()

            # Main synthesis
            st.subheader("📋 Legal Research Analysis")
            st.markdown(result["synthesis"].get("synthesis", "No synthesis available"))

            # Raw results in expanders
            st.divider()
            st.subheader("📚 Raw Agent Results")

            with st.expander(f"📜 State Laws ({len(result['statute_results'].get('state_laws', []))} found)"):
                for law in result["statute_results"].get("state_laws", []):
                    st.markdown(f"**{law.get('title', 'Untitled')}** ({law.get('state', '')})")
                    st.caption(law.get("text", "")[:300])
                    st.divider()

            with st.expander(f"📖 Federal Statutes ({len(result['statute_results'].get('federal_statutes', []))} found)"):
                for statute in result["statute_results"].get("federal_statutes", []):
                    st.markdown(f"**{statute.get('title', 'Untitled')}**")
                    st.caption(statute.get("text", "")[:300])
                    st.divider()

            with st.expander(f"⚖️ Case Law ({len(result['case_results'].get('cases', []))} found)"):
                for case in result["case_results"].get("cases", []):
                    st.markdown(f"**{case.get('case_name', 'Unknown')}** — {case.get('court', '')} ({case.get('date', '')})")
                    st.caption(f"Citation: {case.get('citation', 'N/A')}")
                    st.caption(case.get("text_preview", "")[:300])
                    st.divider()

            with st.expander(f"🔍 TrustFoundry ({len(result['trustfoundry_results'].get('documents', []))} found)"):
                for doc in result["trustfoundry_results"].get("documents", []):
                    st.markdown(f"**{doc.get('title', 'Untitled')}** ({doc.get('type', '')})")
                    st.caption(doc.get("text_preview", "")[:300])
                    st.divider()

            with st.expander(f"📋 Federal Register ({len(result.get('federal_register_results', {}).get('regulations', []))} found)"):
                for reg in result.get("federal_register_results", {}).get("regulations", []):
                    st.markdown(f"**{reg.get('title', 'Untitled')}**")
                    st.caption(reg.get("text", "")[:300])
                    st.divider()
