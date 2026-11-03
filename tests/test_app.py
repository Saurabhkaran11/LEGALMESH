"""Runs with Claude and the data sources faked, so it needs no keys and spends nothing."""

import logging

import anthropic
import httpx
import pytest
from fastapi.testclient import TestClient

from backend import llm
from backend.main import app

KEY = "sk-ant-visitorkey1234567890abcdefghij"
client = TestClient(app)


class Block:
    def __init__(self, type, text=""):
        self.type, self.text = type, text


class Response:
    def __init__(self, content, stop_reason="end_turn"):
        self.content, self.stop_reason = content, stop_reason


CLASSIFIED = '{"domain": "housing", "sub_domains": [], "jurisdiction_state": "CA", "key_terms": ["deposit"], "summary": "Deposit."}'


class FakeClaude:
    """Records how the app calls Claude. Thinking blocks come first, as they do on current models."""

    instances = []

    def __init__(self, api_key=None, **_):
        self.api_key = api_key
        self.calls = []
        FakeClaude.instances.append(self)
        self.beta = self
        self.messages = self

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        text = CLASSIFIED if len(self.calls) == 1 else "## Analysis"
        return Response([Block("thinking"), Block("text", text)])


def error(cls, status):
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    response = httpx.Response(status, request=request)
    if cls is anthropic.APIStatusError:
        return anthropic.APIStatusError(f"failed for {KEY}", response=response, body=None)
    return cls(f"failed for {KEY}", response=response, body=None)


@pytest.fixture(autouse=True)
def fakes(monkeypatch):
    FakeClaude.instances = []
    monkeypatch.setattr(llm.anthropic, "AsyncAnthropic", FakeClaude)
    seen = []

    def respond(request):
        seen.append(request)
        if "ecfr" in request.url.host:
            return httpx.Response(200, json={"results": [{"hierarchy": {"title": "12", "section": "1.1"}, "headings": {"section": "Deposit rule"}, "full_text_excerpt": "<strong>deposit</strong> text", "starts_on": "2020-01-01"}]})
        if "federalregister" in request.url.host:
            return httpx.Response(200, json={"results": [{"title": "Notice", "document_number": "2026-1", "abstract": "About deposits", "html_url": "https://example.gov", "publication_date": "2026-01-01"}]})
        return httpx.Response(200, json={"results": [{"caseName": "A v. B", "court": "Court", "dateFiled": "2020-01-01", "citation": ["1 U.S. 1"], "opinions": [{"snippet": "Held"}], "absolute_url": "/opinion/1/"}]})

    real = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: real(transport=httpx.MockTransport(respond), **kw))
    return seen


def query(**extra):
    return {"query": "My landlord kept my deposit", "anthropic_key": KEY, **extra}


def test_page_asks_for_a_key_and_uses_same_origin():
    r = client.get("/")
    assert r.status_code == 200 and "Your Anthropic API key" in r.text
    assert 'type="password"' in r.text and "localhost" not in r.text and "DOMPurify.sanitize" in r.text


def test_health():
    assert client.get("/api/health").json() == {"status": "ok"}


@pytest.mark.parametrize("body", [{"query": "x"}, query(anthropic_key=""), query(anthropic_key="hello"), query(anthropic_key="sk-ant-short")])
def test_missing_or_malformed_key_is_rejected_before_any_call(body):
    r = client.post("/api/query", json=body)
    assert r.status_code == 400 and "Anthropic API key" in r.json()["error"]
    assert FakeClaude.instances == []


def test_never_falls_back_to_a_server_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-ownerkey1234567890abcdefghijk")
    assert client.post("/api/query", json={"query": "x"}).status_code == 400
    assert FakeClaude.instances == []


@pytest.mark.parametrize("q", ["", "x" * 2001])
def test_bad_question_is_rejected(q):
    assert client.post("/api/query", json=query(query=q)).status_code == 422


def test_full_run_reads_text_after_thinking_and_uses_the_visitor_key(fakes):
    r = client.post("/api/query", json=query())
    assert r.status_code == 200
    data = r.json()
    assert data["synthesis"] == "## Analysis" and data["classification"]["domain"] == "housing"
    assert [c.api_key for c in FakeClaude.instances] == [KEY]
    assert len(FakeClaude.instances[0].calls) == 2
    assert data["agent_statuses"]["trustfoundry"]["detail"] == "No TrustFoundry key added"
    assert data["agent_statuses"]["case_search"]["detail"] == "No CourtListener token added"
    assert data["sources_consulted"] == 2
    assert KEY not in r.text


def test_keyless_sources_get_no_credentials_and_courtlistener_gets_only_its_token(fakes):
    client.post("/api/query", json=query())
    assert {req.url.host for req in fakes} == {"www.ecfr.gov", "www.federalregister.gov"}
    assert all("authorization" not in req.headers for req in fakes)
    fakes.clear()
    client.post("/api/query", json=query(courtlistener_token="cltoken123"))
    by_host = {req.url.host: req for req in fakes}
    assert by_host["www.courtlistener.com"].headers["authorization"] == "Token cltoken123"
    assert "authorization" not in by_host["www.ecfr.gov"].headers
    assert KEY not in str(fakes[0].headers)


def test_synthesizer_is_told_not_to_invent_citations_and_sees_documents():
    client.post("/api/query", json=query())
    prompt = FakeClaude.instances[0].calls[1]["messages"][0]["content"]
    assert "Never invent" in prompt and "Deposit rule" in prompt and "12 CFR" in prompt and "FR Doc. 2026-1" in prompt


def test_one_failing_source_does_not_stop_the_answer(monkeypatch):
    async def boom(*_):
        raise RuntimeError(f"failed with {KEY}")

    monkeypatch.setattr("backend.agents.orchestrator.search_regulations", boom)
    r = client.post("/api/query", json=query())
    assert r.status_code == 200 and r.json()["synthesis"] == "## Analysis"
    assert r.json()["agent_statuses"]["regulations"]["status"] == "error"
    assert r.json()["sources_consulted"] == 1
    assert KEY not in r.text


@pytest.mark.parametrize("cls,status,code,text", [
    (anthropic.AuthenticationError, 401, 401, "rejected"),
    (anthropic.PermissionDeniedError, 403, 403, "access"),
    (anthropic.RateLimitError, 429, 429, "rate limit"),
    (anthropic.APIStatusError, 402, 402, "credit"),
    (anthropic.InternalServerError, 500, 502, "Could not"),
])
def test_claude_errors_are_explained_without_exposing_the_key(monkeypatch, caplog, cls, status, code, text):
    async def fail(self, **_):
        raise error(cls, status)

    monkeypatch.setattr(FakeClaude, "create", fail)
    with caplog.at_level(logging.DEBUG):
        r = client.post("/api/query", json=query())
    assert r.status_code == code and text in r.json()["error"]
    assert KEY not in r.text and KEY not in caplog.text


def test_refusal_is_reported(monkeypatch):
    async def refuse(self, **_):
        return Response([], stop_reason="refusal")

    monkeypatch.setattr(FakeClaude, "create", refuse)
    r = client.post("/api/query", json=query())
    assert r.status_code == 422 and "declined" in r.json()["error"]


def test_websocket_streams_status_then_result():
    with client.websocket_connect("/ws/query") as ws:
        ws.send_json(query())
        frames = []
        while True:
            frame = ws.receive_json()
            frames.append(frame)
            if frame["type"] != "agent_status":
                break
    assert frames[-1]["type"] == "result" and frames[-1]["synthesis"] == "## Analysis"
    agents = {f["agent"] for f in frames if f["type"] == "agent_status"}
    assert {"classifier", "regulations", "case_search", "trustfoundry", "federal_register", "synthesizer"} <= agents


def test_websocket_reports_bad_input_and_stays_open():
    with client.websocket_connect("/ws/query") as ws:
        ws.send_text("not json")
        assert ws.receive_json()["type"] == "error"
        ws.send_json({"query": "x"})
        assert "Anthropic API key" in ws.receive_json()["error"]


def test_keys_are_hidden_from_repr():
    assert KEY not in repr(llm.Keys(anthropic=KEY))
