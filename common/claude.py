"""Shared helpers for calling the Claude API.

Every script in this repo imports from here, so the model, the client setup
and the refusal handling live in one place.
"""

from __future__ import annotations

from typing import Optional, Type, TypeVar

import anthropic
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()  # reads ANTHROPIC_API_KEY from a local .env file, if there is one

MODEL = "claude-opus-5-5"

# If Claude's safety classifiers decline a request, the API retries it on a
# suitable fallback model inside the same call instead of just stopping.
FALLBACK_BETA = "server-side-fallback-2026-07-01"

client = anthropic.Anthropic()

T = TypeVar("T", bound=BaseModel)


class RefusalError(RuntimeError):
    """Raised when the request was declined (stop_reason == "refusal")."""


def _text_of(response) -> str:
    return "".join(block.text for block in response.content if block.type == "text")


def _check(response) -> None:
    if response.stop_reason == "refusal":
        details = response.stop_details
        reason = details.explanation if details else "no details"
        raise RefusalError(f"Request was declined: {reason}")


def chat(
    messages: list[dict],
    system: Optional[str] = None,
    max_tokens: int = 16000,
    effort: str = "medium",
) -> str:
    """Send a conversation to Claude and return the text of its reply."""
    kwargs = {"system": system} if system else {}
    response = client.beta.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        messages=messages,
        output_config={"effort": effort},
        betas=[FALLBACK_BETA],
        fallbacks="default",
        **kwargs,
    )
    _check(response)
    return _text_of(response)


def structured(
    prompt: str,
    schema: Type[T],
    system: Optional[str] = None,
    max_tokens: int = 16000,
    effort: str = "medium",
) -> T:
    """Ask Claude for output that matches a Pydantic model and return it validated."""
    kwargs = {"system": system} if system else {}
    response = client.beta.messages.parse(
        model=MODEL,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
        output_format=schema,
        output_config={"effort": effort},
        betas=[FALLBACK_BETA],
        fallbacks="default",
        **kwargs,
    )
    _check(response)
    return response.parsed_output
