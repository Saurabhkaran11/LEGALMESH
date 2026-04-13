# ⚖️ LegalMesh — Multi-Agent Legal Research System

> **Built at LLM × Law Hackathon @ Stanford** | Harvey Track: Justice for the Underserved

LegalMesh is a multi-agent AI system that coordinates **7 specialized legal research agents** across **7 open legal datasets** to answer legal questions in plain English. Agents run in parallel, searching statutes, case law, regulations, and municipal ordinances simultaneously, then synthesize everything into a comprehensive legal analysis.

## Architecture

```
User Question (plain English)
        │
        ▼
┌─────────────────────────┐
│  Agent 1: FOLIO Legal   │──▶ Classifies domain, jurisdiction, key terms
│  Classifier (Claude)    │    (18K legal concepts from FOLIO ontology)
└────────────┬────────────┘
             │
    ┌────────┼────────┬──────────┬──────────┐
    ▼        ▼        ▼          ▼          ▼
┌────────┐┌────────┐┌─────────┐┌─────────┐┌──────────┐
│Statute ││Case Law││Trust-   ││Federal  ││Municipal │
│Search  ││Search  ││Foundry  ││Register ││Law Search│
│Agent   ││Agent   ││Agent    ││Agent    ││Agent     │
│        ││        ││         ││         ││          │
│State   ││6.7M    ││8M+ docs ││1M+ regs ││County/   │
│laws +  ││cases   ││verified ││& rules  ││city      │
│US Code ││360 yrs ││legal    ││         ││ordinances│
└────┬───┘└───┬────┘└────┬────┘└────┬────┘└────┬─────┘
     │        │          │          │          │
     └────────┴──────────┴──────────┴──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │  Agent 7: Claude    │──▶ Comprehensive legal analysis
              │  Synthesizer        │    with citations & action steps
              └─────────────────────┘
```

## Data Sources

| Dataset | Source | Scale |
|---------|--------|-------|
| U.S. State Laws | `justicedao/ipfs_state_laws` | 10K-100K rows, 51 jurisdictions |
| U.S. Code | `justicedao/ipfs_uscode` | 100K-1M rows |
| Court Rules | `justicedao/ipfs_court_rules` | Per-state procedural rules |
| Case Law | `justicedao/ipfs_caselaw_access_project` | 1M-10M cases |
| Case Embeddings | `justicedao/Caselaw_Access_Project_embeddings` | 10M-100M vectors |
| Federal Register | `justicedao/ipfs_federal_register` | 1M-10M regulations |
| Municipal Law | `justicedao/american_municipal_law` | County/city ordinances |
| TrustFoundry | TrustFoundry API | 8M+ verified legal documents |

## Quick Start (< 10 steps)

### 1. Clone and install
```bash
cd legalmesh
pip install -r requirements.txt
```

### 2. Set up API keys
Edit `.env` with your keys:
```
ANTHROPIC_API_KEY=sk-ant-...
HF_TOKEN=hf_...
TRUSTFOUNDRY_API_KEY=api_...
```

### 3. Run the backend
```bash
python -m backend.main
# API running at http://localhost:8000
```

### 4. Choose your frontend

**Option A — Streamlit** (recommended for demo):
```bash
cd frontend_streamlit
streamlit run app.py
# UI at http://localhost:8501
```

**Option B — Gradio** (shareable link):
```bash
cd frontend_gradio
python app.py
# UI at http://localhost:7860 (+ public share link)
```

**Option C — React** (polished standalone):
```bash
# Just open frontend_react/index.html in a browser
# (requires backend running on port 8000)
```

### 5. Ask a question
Enter any legal question in plain English, e.g.:
> "My landlord won't return my security deposit after 30 days in California"

Watch all 7 agents work in parallel and receive a comprehensive legal analysis.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Service info and available agents |
| `GET` | `/api/health` | Health check |
| `POST` | `/api/query` | Submit legal research query |
| `WS` | `/ws/query` | WebSocket for real-time agent updates |

## Example API Call
```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What are my rights if my employer withholds overtime pay in Texas?"}'
```

## Hackathon Tracks

- **Harvey**: Justice for the Underserved — Multi-step workflow agents
- **Thenvoi** ($1000): Modular agent orchestration (Thenvoi-ready design)

## Disclaimer

This is a legal research tool, NOT legal advice. Always consult a licensed attorney.

## Team

Built by Karan at LLM × Law Hackathon, Stanford, April 2026.
