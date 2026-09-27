"""
Pipeline 1 - Python + OpenAI API Generation Pipeline (SRS section on
Pipeline 1). Generates the personalized onboarding plan as structured JSON.
Handles retries (Step 39) and logs prompt version / model / timestamp (Step 41/65).
"""
import json
import re
from datetime import datetime
from typing import Dict, List

from openai import OpenAI

from ..config import settings
from ..security.prompt_injection import sanitize_for_prompt
from .prompt_templates import (
    ONBOARDING_PLAN_SYSTEM_INSTRUCTIONS,
    ONBOARDING_PLAN_PROMPT_VERSION,
    build_onboarding_user_prompt,
)

_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not set. Configure it in your .env file.")
        _client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


def _extract_json(raw_text: str) -> dict:
    """The model sometimes wraps JSON in markdown fences despite instructions;
    this strips fences and extracts the first {...} block defensively."""
    text = raw_text.strip()
    text = re.sub(r"^```(json)?", "", text.strip())
    text = re.sub(r"```$", "", text.strip())
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


def generate_onboarding_plan(employee: dict, role_requirements: List[dict],
                              source_chunks: List[dict]) -> Dict:
    """
    Calls OpenAI with source-grounded content and returns:
    {plan: <parsed json>, raw_response: str, prompt_version, model, generated_at, attempts}
    Free-form text is never returned as the sole output - JSON parsing is mandatory.
    """
    client = _get_client()

    sanitized_chunks_text = "\n\n".join(
        sanitize_for_prompt(f"[doc:{c['document_id']} section:{c['section_id']}] {c['text'][:1500]}")
        for c in source_chunks
    )
    user_prompt = build_onboarding_user_prompt(employee, role_requirements, sanitized_chunks_text)

    last_error = None
    for attempt in range(1, settings.MAX_GENAI_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": ONBOARDING_PLAN_SYSTEM_INSTRUCTIONS},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                response_format={"type": "json_object"},
            )
            raw_text = response.choices[0].message.content
            parsed = _extract_json(raw_text)
            return {
                "plan": parsed,
                "raw_response": raw_text,
                "prompt_version": ONBOARDING_PLAN_PROMPT_VERSION,
                "model": settings.OPENAI_MODEL,
                "generated_at": datetime.utcnow().isoformat(),
                "attempts": attempt,
                "status": "success",
            }
        except Exception as e:  # noqa: BLE001 - retry on any generation/parsing failure
            last_error = str(e)
            continue

    return {
        "plan": None,
        "raw_response": None,
        "prompt_version": ONBOARDING_PLAN_PROMPT_VERSION,
        "model": settings.OPENAI_MODEL,
        "generated_at": datetime.utcnow().isoformat(),
        "attempts": settings.MAX_GENAI_RETRIES,
        "status": "failed",
        "error": last_error,
    }


def generate_twice_for_consistency(employee: dict, role_requirements: List[dict],
                                    source_chunks: List[dict]) -> Dict:
    """Step 44/45 - GenAI Consistency Check: runs generation twice with the same
    controlled inputs and returns both results for structured comparison."""
    run_a = generate_onboarding_plan(employee, role_requirements, source_chunks)
    run_b = generate_onboarding_plan(employee, role_requirements, source_chunks)
    return {"run_a": run_a, "run_b": run_b}
