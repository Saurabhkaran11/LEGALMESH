# LegalMesh

Ask a legal question in plain English and get a cited research summary. Built at the LLM × Law Hackathon at Stanford (April 2026) for the Harvey track, Justice for the Underserved.

This is a legal research tool, not legal advice. Always consult a licensed attorney.

## How it works

1. A Claude agent classifies the question by legal domain, jurisdiction and key terms.
2. Four search agents run concurrently. If one source fails, the others continue.
3. A final Claude agent writes the analysis. It cites only retrieved documents and labels anything from general knowledge.

Progress streams to the page over a WebSocket.

| Source | Covers | Key |
|---|---|---|
| [eCFR](https://www.ecfr.gov/) | Current federal regulations | None |
| [Federal Register](https://www.federalregister.gov/) | Federal rules, proposed rules and notices | None |
| [CourtListener](https://www.courtlistener.com/) | Court opinions | Free token, optional |
| TrustFoundry | Legal documents | Optional |

These sources are strongest on federal law. They usually do not include state statutes, and the app says so instead of inventing citations.

The original hackathon version searched Hugging Face datasets. Those datasets have since been restructured or closed to search, so this version uses official APIs.

## API keys

Each visitor enters their own keys on the page. Keys are used for one request and are never stored or logged.

The default model is `claude-opus-5-5`. Set the `ANTHROPIC_MODEL` environment variable to change it. Requests use Anthropic's server-side fallback if a model declines.

## Tech stack

Python, FastAPI, asyncio, WebSockets, Anthropic Python SDK, httpx, HTML and JavaScript, pytest

## Run it

```bash
pip install -r requirements-dev.txt
python -m backend.main        # then open http://127.0.0.1:8000
python -m pytest              # needs no API keys
```

## Deploy to Render

Create a new Blueprint on Render and select this repository. It uses `render.yaml` and needs no environment variables.

## API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | The web page |
| `GET` | `/api/health` | Health check |
| `POST` | `/api/query` | Run a query with `query` and `anthropic_key` |
| `WS` | `/ws/query` | The same query with live agent updates |
