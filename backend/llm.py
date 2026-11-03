"""Claude access for LegalMesh. Each request uses the key the visitor supplied."""

import os
from dataclasses import dataclass
from typing import Optional

import anthropic

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-opus-5-5")


class RefusedError(Exception):
    """Claude declined the request."""


@dataclass(frozen=True)
class Keys:
    """Keys for one request. Never logged or stored."""

    anthropic: str
    courtlistener: Optional[str] = None
    trustfoundry: Optional[str] = None

    def __repr__(self) -> str:
        return "Keys(<hidden>)"


def make_client(api_key: str) -> anthropic.AsyncAnthropic:
    return anthropic.AsyncAnthropic(api_key=api_key, timeout=120.0, max_retries=1)


async def ask(client: anthropic.AsyncAnthropic, prompt: str, effort: str, max_tokens: int) -> str:
    response = await client.beta.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        output_config={"effort": effort},
        messages=[{"role": "user", "content": prompt}],
    )
    if response.stop_reason == "refusal":
        raise RefusedError()
    return "".join(block.text for block in response.content if block.type == "text")
