"""
OpenRouter Client — Centralized model registry.
100% FREE TIER — Zero cost, no credits required.

Each agent is assigned the best available free model for its specific task:

┌─────────────────────┬────────────────────────────────────────────────┬──────────────────────────────────────────┐
│ Agent               │ Free Model                                     │ Why                                      │
├─────────────────────┼────────────────────────────────────────────────┼──────────────────────────────────────────┤
│ Topic Discovery     │ nvidia/nemotron-3-nano-30b-a3b:free            │ 256K ctx, tools, fast — best free scout  │
│ Structure & SEO     │ arcee-ai/trinity-large-preview:free            │ 400B MoE, reasoning, tools, 131K ctx     │
│ Deep Research       │ nousresearch/hermes-3-llama-3.1-405b:free      │ Largest free model (405B), deep knowledge│
│ Human Writer        │ arcee-ai/trinity-large-preview:free            │ #1 free for creative writing & narrative │
│ AI Detector Bypass  │ mistralai/mistral-small-3.1-24b-instruct:free  │ Low perplexity, naturally varied style   │
│ Social Repurpose    │ meta-llama/llama-3.3-70b-instruct:free         │ Fast, creative, great social content     │
│ LinkedIn Post       │ openai/gpt-oss-120b:free                       │ 131K ctx, OpenAI-trained, format precise │
└─────────────────────┴────────────────────────────────────────────────┴──────────────────────────────────────────┘

Rate limits (free tier): 20 requests/min · 200 requests/day
All models: zero cost, no credit card needed.
"""

import os
import json
import requests
from typing import Optional

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_BASE = "https://openrouter.ai/api/v1/chat/completions"

# ── FREE MODEL REGISTRY ───────────────────────────────────────────────────────
MODELS = {
    "discover":    "nvidia/nemotron-3-nano-30b-a3b:free",
    "structure":   "arcee-ai/trinity-large-preview:free",
    "research":    "nousresearch/hermes-3-llama-3.1-405b:free",
    "writer":      "arcee-ai/trinity-large-preview:free",
    "humanizer":   "mistralai/mistral-small-3.1-24b-instruct:free",
    "social":      "meta-llama/llama-3.3-70b-instruct:free",
    "caption":     "openai/gpt-oss-120b:free",
    # Image generation — Gemini Nano Banana via OpenRouter (free)
    "image":       "google/gemini-2.5-flash-preview:free",
}

# Fallback models if primary is rate-limited or unavailable
FALLBACK_MODELS = {
    "discover":    "meta-llama/llama-3.3-70b-instruct:free",
    "structure":   "openai/gpt-oss-120b:free",
    "research":    "meta-llama/llama-3.3-70b-instruct:free",
    "writer":      "mistralai/mistral-small-3.1-24b-instruct:free",
    "humanizer":   "meta-llama/llama-3.3-70b-instruct:free",
    "social":      "google/gemma-3-27b-it:free",
    "caption":     "meta-llama/llama-3.3-70b-instruct:free",
    "image":       "google/gemini-2.0-flash-exp:free",
}

def _do_request(model: str, messages: list, temperature: float,
                max_tokens: int, json_mode: bool,
                site_url: str, site_name: str) -> str:
    """Raw HTTP call to OpenRouter. Returns text content or raises."""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": site_url,
        "X-Title": site_name,
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    resp = requests.post(OPENROUTER_BASE, headers=headers, json=payload, timeout=120)

    # 429 = rate limit, 503 = model overloaded — both are retryable with fallback
    if resp.status_code in (429, 503, 404):
        raise RuntimeError(f"RETRYABLE:{resp.status_code}")

    if resp.status_code != 200:
        raise RuntimeError(
            f"OpenRouter error {resp.status_code} [{model}]: {resp.text[:300]}"
        )

    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    if content is None:
        raise RuntimeError("RETRYABLE:empty_content")
    return content.strip()


def call(
    model_key: str,
    messages: list,
    temperature: float = 0.7,
    max_tokens: int = 4000,
    json_mode: bool = False,
    site_url: str = "https://blog-writer-ai.netlify.app",
    site_name: str = "Blog Writer AI",
) -> str:
    """
    Call OpenRouter with the best free model for the given agent key.
    Auto-falls back to the secondary free model if primary is rate-limited
    or unavailable. Raises only if both primary and fallback fail.
    """
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY environment variable not set.")

    primary  = MODELS.get(model_key)
    fallback = FALLBACK_MODELS.get(model_key)

    if not primary:
        raise ValueError(f"Unknown model key: '{model_key}'. Valid: {list(MODELS.keys())}")

    # Try primary model
    try:
        result = _do_request(primary, messages, temperature, max_tokens,
                             json_mode, site_url, site_name)
        print(f"[OpenRouter] ✓ {model_key} → {primary}")
        return result
    except RuntimeError as e:
        if "RETRYABLE" not in str(e) or not fallback:
            raise
        print(f"[OpenRouter] Primary {primary} unavailable ({e}) — trying fallback {fallback}")

    # Try fallback model
    try:
        result = _do_request(fallback, messages, temperature, max_tokens,
                             json_mode, site_url, site_name)
        print(f"[OpenRouter] ✓ {model_key} → {fallback} (fallback)")
        return result
    except RuntimeError as e:
        raise RuntimeError(
            f"Both models failed for '{model_key}'. "
            f"Primary: {primary}, Fallback: {fallback}. Error: {e}"
        )


def call_json(model_key: str, messages: list, temperature: float = 0.7) -> dict:
    """
    Call and auto-parse JSON response.
    Handles markdown fences, trailing text, and minor formatting issues.
    """
    raw = call(model_key, messages, temperature=temperature, json_mode=True)

    # Strip markdown code fences if present
    if "```" in raw:
        lines = raw.split("\n")
        # Find content between first ``` and last ```
        start = next((i+1 for i, l in enumerate(lines) if l.strip().startswith("```")), 0)
        end   = next((i for i, l in enumerate(reversed(lines)) if l.strip() == "```"), 0)
        raw   = "\n".join(lines[start: len(lines)-end if end else None])

    raw = raw.strip()

    # Find JSON object boundaries in case there's preamble text
    if not raw.startswith("{"):
        start = raw.find("{")
        end   = raw.rfind("}") + 1
        if start != -1 and end > start:
            raw = raw[start:end]

    return json.loads(raw)


def generate_image(prompt: str, site_url: str = "https://blog-writer-ai.netlify.app") -> str | None:
    """
    Generate an image via OpenRouter using Gemini Nano Banana (free).
    Returns base64 PNG string, or None on failure.

    OpenRouter image generation uses modalities: ["image", "text"]
    Response image is in choices[0].message.content as a list,
    with image parts having type="image_url" containing base64 data URLs.
    """
    if not OPENROUTER_API_KEY:
        return None

    primary  = MODELS["image"]
    fallback = FALLBACK_MODELS["image"]

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": site_url,
        "X-Title": "Blog Writer AI",
    }

    payload = {
        "model": primary,
        "messages": [{"role": "user", "content": prompt}],
        "modalities": ["image", "text"],
    }

    for attempt, model in enumerate([primary, fallback]):
        payload["model"] = model
        try:
            resp = requests.post(OPENROUTER_BASE, headers=headers, json=payload, timeout=120)
            if resp.status_code in (429, 503, 404):
                print(f"[Image] Model {model} unavailable ({resp.status_code}), trying fallback")
                continue
            if resp.status_code != 200:
                print(f"[Image] HTTP {resp.status_code}: {resp.text[:200]}")
                continue

            data    = resp.json()
            content = data["choices"][0]["message"].get("content", [])

            # content can be a list of parts or a string
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "image_url":
                        url = part.get("image_url", {}).get("url", "")
                        # data:image/png;base64,XXXX  →  extract XXXX
                        if "base64," in url:
                            print(f"[Image] ✓ Generated via {model}")
                            return url.split("base64,", 1)[1]
            elif isinstance(content, str) and "base64," in content:
                return content.split("base64,", 1)[1]

            # Also check top-level images field (some models return here)
            images = data.get("images", [])
            if images:
                img = images[0]
                if isinstance(img, str) and "base64," in img:
                    return img.split("base64,", 1)[1]
                if isinstance(img, dict) and "base64," in img.get("url",""):
                    return img["url"].split("base64,", 1)[1]

            print(f"[Image] No image data found in response from {model}")

        except requests.Timeout:
            print(f"[Image] Timeout on {model}")
        except Exception as e:
            print(f"[Image] Error on {model}: {e}")

    return None
