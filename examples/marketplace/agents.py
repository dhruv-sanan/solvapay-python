"""Marketplace agent catalog. Each agent calls a real LLM (Google Gemini).

All 4 agents bill the same SolvaPay product (the one in your sandbox). They
differ only by system prompt + display price — the marketplace framing is
cosmetic; real metering is per-call against `SOLVAPAY_PRODUCT_REF`.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Callable

from google import genai
from google.genai import types

log = logging.getLogger("marketplace.llm")

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    return _client


def _model() -> str:
    return os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")


def _llm(system: str, user: str, max_tokens: int = 600, *, agent_name: str = "unknown") -> str:
    """Single-turn LLM call. Returns the model's text response."""
    model = _model()
    log.info("LLM CALL → model=%s | agent=%s | input_chars=%d", model, agent_name, len(user))
    response = _get_client().models.generate_content(
        model=model,
        contents=user,
        config=types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=max_tokens,
        ),
    )
    text = (response.text or "(no response)").strip()
    log.info("LLM DONE ✓ model=%s | agent=%s | output_chars=%d", model, agent_name, len(text))
    return text


# --- agent runners ---------------------------------------------------------

def _run_web_researcher(query: str) -> str:
    return _llm(
        system=(
            "You are a concise research assistant. Given a topic, return 3 bullet points "
            "of factual, well-known information about it. No fluff. Use markdown."
        ),
        user=query.strip() or "Stockholm fintech startups in agent payments",
        agent_name="web_researcher",
    )


def _run_text_analyst(text: str) -> str:
    return _llm(
        system=(
            "You are a text analyst. Given a piece of text, return: (1) sentiment with a "
            "confidence score 0-1, (2) 2-3 key themes, (3) one suggested action. "
            "Markdown bullets only."
        ),
        user=text.strip() or "I love this product but the onboarding is a bit confusing.",
        agent_name="text_analyst",
    )


def _run_code_reviewer(diff: str) -> str:
    return _llm(
        system=(
            "You are a senior code reviewer. Given a code snippet or diff, return a "
            "terse review: 🟢 strengths, 🟡 nits, 🔴 bugs. Max 6 bullets total."
        ),
        user=diff.strip() or "def add(a, b):\n    return a + b  # TODO: handle floats",
        agent_name="code_reviewer",
    )


def _run_image_describer(prompt: str) -> str:
    return _llm(
        system=(
            "You are an image-description assistant. The user describes an image in words. "
            "Return a 3-bullet refinement covering subject, composition, and mood."
        ),
        user=prompt.strip() or "A cat sitting on a windowsill at golden hour",
        agent_name="image_describer",
    )


@dataclass(frozen=True)
class Agent:
    slug: str
    name: str
    blurb: str
    icon: str
    price_usd: float  # display only; real billing is per the SolvaPay product config
    run: Callable[[str], str]


AGENTS: list[Agent] = [
    Agent("web_researcher",  "Web Researcher",  "3-bullet brief on any topic.",                     "🔎",  0.02, _run_web_researcher),
    Agent("text_analyst",    "Text Analyst",    "Sentiment + themes for any text.",                 "📊",  0.05, _run_text_analyst),
    Agent("code_reviewer",   "Code Reviewer",   "Senior-style review of a snippet. (Decorator-gated.)", "🧑‍💻", 0.10, _run_code_reviewer),
    Agent("image_describer", "Image Describer", "Refines an image description.",                    "🖼️",  0.03, _run_image_describer),
]

AGENTS_BY_SLUG: dict[str, Agent] = {a.slug: a for a in AGENTS}


def example_input_for(slug: str) -> str:
    return {
        "web_researcher": "Stockholm fintech startups working on AI agent payments",
        "text_analyst": "I love this product but the onboarding is a bit confusing.",
        "code_reviewer": "def divide(a, b):\n    return a / b  # TODO",
        "image_describer": "A short-haired tabby cat on a windowsill at golden hour",
    }.get(slug, "")
