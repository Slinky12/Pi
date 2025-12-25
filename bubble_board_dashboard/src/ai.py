from __future__ import annotations
from typing import Dict

import requests


def _build_prompt(item: Dict) -> str:
    # Lightweight prompt so it looks good on a TV display.
    return (
        "You are an assistant that writes concise, practical project blurbs.\n"
        "Given this task, write:\n"
        "1) A 2–3 sentence description of what it is.\n"
        "2) A bullet list of next steps (max 5 bullets).\n"
        "3) A short 'risks & blockers' section.\n\n"
        f"Category: {item.get('Category','')}\n"
        f"Project / Item: {item.get('Project / Item','')}\n"
        f"Current Status: {item.get('Current Status','')}\n"
        f"Start Date: {item.get('Start Date','')}\n"
        f"Target End Date: {item.get('Target End Date','')}\n"
        f"Estimated Cost ($): {item.get('Estimated Cost ($)','')}\n"
        f"Dependencies / Prerequisites: {item.get('Dependencies / Prerequisites','')}\n"
        f"Next Action: {item.get('Next Action','')}\n"
        f"Priority: {item.get('Priority','')}\n"
    )


def get_ai_description(item: Dict, settings) -> str:
    """
    Calls an OpenAI-compatible local server.
    Works with:
      - Ollama (with OpenAI compatibility via /v1)
      - LM Studio (OpenAI server)
      - vLLM / llama.cpp servers that emulate OpenAI
    """
    url = settings.ai_base_url.rstrip("/") + "/chat/completions"
    headers = {}
    if getattr(settings, "ai_api_key", ""):
        headers["Authorization"] = f"Bearer {settings.ai_api_key}"

    payload = {
        "model": settings.ai_model,
        "messages": [
            {"role": "system", "content": "Be helpful, specific, and not verbose."},
            {"role": "user", "content": _build_prompt(item)},
        ],
        "temperature": 0.4,
        "max_tokens": 500,
    }

    r = requests.post(url, headers=headers, json=payload, timeout=settings.ai_timeout_seconds)
    r.raise_for_status()
    data = r.json()
    # OpenAI-style response
    return data["choices"][0]["message"]["content"]
