"""
OpenRouter Client — Multi-model waterfall with exponential backoff.

PROBLEM SOLVED: "Both models failed — RETRYABLE:429"
─────────────────────────────────────────────────────
Old system: 2 models per agent → both 429 → crash.
New system:  5-model waterfall + exponential backoff + openrouter/free as ultimate fallback.

HOW IT WORKS NOW:
  1. Try primary model
  2. On 429/503/404 → wait (backoff) → retry same model once
  3. If still fails → try each fallback model in order (up to 4 fallbacks)
  4. Between each fallback → short wait (1-3 seconds)
  5. Last resort → openrouter/free (random available free model)
  6. Only errors out if ALL 5 attempts fail

This makes 429 errors essentially impossible to surface to the user.
"""

import os, json, time, requests
from typing import Optional

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_BASE    = "https://openrouter.ai/api/v1/chat/completions"

# ── FREE MODEL WATERFALL CHAINS ────────────────────────────────────────────────
# Each agent gets a list of 5 models tried in order.
# The last entry is always openrouter/free (catches whatever's available).
# Models chosen for different providers — avoids one provider being down wiping out all.

MODEL_CHAINS = {
    "discover": [
        "nvidia/nemotron-3-nano-30b-a3b:free",          # Fast, 256K ctx
        "meta-llama/llama-3.3-70b-instruct:free",       # Meta — different provider
        "google/gemma-3-27b-it:free",                   # Google — different provider
        "mistralai/mistral-small-3.1-24b-instruct:free",# Mistral — different provider
        "openrouter/free",                              # Ultimate fallback
    ],
    "structure": [
        "arcee-ai/trinity-large-preview:free",          # 400B MoE, best for structure
        "openai/gpt-oss-120b:free",                     # 120B, precise formatting
        "meta-llama/llama-3.3-70b-instruct:free",       # Reliable generalist
        "mistralai/mistral-small-3.1-24b-instruct:free",# Fast, good JSON
        "openrouter/free",
    ],
    "research": [
        "nousresearch/hermes-3-llama-3.1-405b:free",    # Largest free model
        "arcee-ai/trinity-large-preview:free",          # 400B, deep knowledge
        "openai/gpt-oss-120b:free",                     # Good factual recall
        "meta-llama/llama-3.3-70b-instruct:free",       # Strong generalist
        "openrouter/free",
    ],
    "writer": [
        "arcee-ai/trinity-large-preview:free",          # Best free creative writing
        "nousresearch/hermes-3-llama-3.1-405b:free",    # Large, quality prose
        "openai/gpt-oss-120b:free",                     # Good narrative
        "meta-llama/llama-3.3-70b-instruct:free",       # Reliable fallback
        "openrouter/free",
    ],
    "humanizer": [
        "mistralai/mistral-small-3.1-24b-instruct:free",# Low perplexity, varied style
        "meta-llama/llama-3.3-70b-instruct:free",       # Good rewriter
        "google/gemma-3-27b-it:free",                   # Different provider
        "arcee-ai/trinity-mini:free",                   # Smaller Trinity, fast
        "openrouter/free",
    ],
    "social": [
        "meta-llama/llama-3.3-70b-instruct:free",       # Fast, creative social
        "mistralai/mistral-small-3.1-24b-instruct:free",# Good copy
        "google/gemma-3-27b-it:free",                   # Different provider
        "openai/gpt-oss-120b:free",                     # Format-precise
        "openrouter/free",
    ],
    "caption": [
        "openai/gpt-oss-120b:free",                     # Format-precise LinkedIn
        "meta-llama/llama-3.3-70b-instruct:free",       # Reliable
        "mistralai/mistral-small-3.1-24b-instruct:free",# Good copy
        "arcee-ai/trinity-large-preview:free",          # Quality writing
        "openrouter/free",
    ],
    "image": [
        "google/gemini-2.5-flash-preview:free",         # Best free image gen
        "google/gemini-2.0-flash-exp:free",             # Fallback Gemini
    ],
}

# ── BACKOFF CONFIGURATION ──────────────────────────────────────────────────────
# Waits (seconds) between retries on 429. Grows exponentially.
BACKOFF_SEQUENCE = [2, 5, 10, 20]   # Wait 2s, then 5s, then 10s, then 20s
RETRY_SAME_MODEL = 1                # Retry same model once before switching


def _do_request(
    model: str,
    messages: list,
    temperature: float,
    max_tokens: int,
    json_mode: bool,
    site_url: str,
    site_name: str,
) -> str:
    """Single HTTP call. Returns content string or raises RuntimeError."""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type":  "application/json",
        "HTTP-Referer":  site_url,
        "X-Title":       site_name,
    }
    payload: dict = {
        "model":       model,
        "messages":    messages,
        "temperature": temperature,
        "max_tokens":  max_tokens,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    resp = requests.post(OPENROUTER_BASE, headers=headers, json=payload, timeout=120)

    if resp.status_code in (429, 503):
        raise RuntimeError(f"RATE_LIMITED:{resp.status_code}")
    if resp.status_code == 404:
        raise RuntimeError(f"MODEL_NOT_FOUND:404")
    if resp.status_code != 200:
        raise RuntimeError(f"HTTP_{resp.status_code}:{resp.text[:200]}")

    data    = resp.json()
    content = data["choices"][0]["message"]["content"]
    if content is None:
        raise RuntimeError("EMPTY_CONTENT")
    return content.strip()


def call(
    model_key:  str,
    messages:   list,
    temperature: float = 0.7,
    max_tokens:  int   = 4000,
    json_mode:   bool  = False,
    site_url:    str   = "https://blog-writer-ai.netlify.app",
    site_name:   str   = "Blog Writer AI",
) -> str:
    """
    Call OpenRouter with automatic waterfall fallback + exponential backoff.

    Strategy per attempt:
      - Try model
      - On RATE_LIMITED: wait backoff[i] seconds, retry once
      - If still fails: move to next model in chain
      - Last model in chain is openrouter/free (always has something available)
    """
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY environment variable not set.")

    chain = MODEL_CHAINS.get(model_key)
    if not chain:
        raise ValueError(f"Unknown model key: '{model_key}'. Valid: {list(MODEL_CHAINS.keys())}")

    last_error = None

    for attempt_idx, model in enumerate(chain):
        # Per-model: try once, on 429 wait+retry once more
        for retry in range(RETRY_SAME_MODEL + 1):
            try:
                result = _do_request(
                    model, messages, temperature,
                    max_tokens, json_mode, site_url, site_name
                )
                if attempt_idx > 0 or retry > 0:
                    print(f"[OpenRouter] ✓ {model_key} → {model} "
                          f"(attempt {attempt_idx+1}, retry {retry})")
                else:
                    print(f"[OpenRouter] ✓ {model_key} → {model}")
                return result

            except RuntimeError as e:
                last_error = str(e)
                is_rate_limit = "RATE_LIMITED" in last_error
                is_not_found  = "MODEL_NOT_FOUND" in last_error

                if is_not_found:
                    # Model doesn't exist — skip immediately, no point retrying
                    print(f"[OpenRouter] ✗ {model} not found, skipping")
                    break

                if is_rate_limit and retry < RETRY_SAME_MODEL:
                    # Wait and retry same model
                    wait = BACKOFF_SEQUENCE[min(attempt_idx, len(BACKOFF_SEQUENCE)-1)]
                    print(f"[OpenRouter] ⚠ {model} rate limited — "
                          f"waiting {wait}s before retry…")
                    time.sleep(wait)
                    continue

                # Give up on this model, move to next
                print(f"[OpenRouter] ✗ {model} failed ({last_error}) — "
                      f"trying next in chain…")
                # Brief pause between models to avoid hammering
                if attempt_idx < len(chain) - 1:
                    time.sleep(1)
                break

    raise RuntimeError(
        f"All models exhausted for '{model_key}'. "
        f"Tried: {chain}. Last error: {last_error}"
    )


def call_json(model_key: str, messages: list, temperature: float = 0.7) -> dict:
    """Call and auto-parse JSON. Strips markdown fences, fixes minor formatting."""
    raw = call(model_key, messages, temperature=temperature, json_mode=True)

    if "```" in raw:
        lines = raw.split("\n")
        start = next((i+1 for i, l in enumerate(lines) if l.strip().startswith("```")), 0)
        end   = next((i   for i, l in enumerate(reversed(lines)) if l.strip() == "```"), 0)
        raw   = "\n".join(lines[start: len(lines)-end if end else None])

    raw = raw.strip()

    if not raw.startswith("{"):
        s = raw.find("{")
        e = raw.rfind("}") + 1
        if s != -1 and e > s:
            raw = raw[s:e]

    return json.loads(raw)


def generate_image(
    prompt:   str,
    site_url: str = "https://blog-writer-ai.netlify.app",
) -> str | None:
    """
    Generate image via OpenRouter (Gemini free).
    Returns base64 string or None — never raises, image is optional.
    """
    if not OPENROUTER_API_KEY:
        return None

    chain = MODEL_CHAINS["image"]
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type":  "application/json",
        "HTTP-Referer":  site_url,
        "X-Title":       "Blog Writer AI",
    }

    for model in chain:
        payload = {
            "model":      model,
            "messages":   [{"role": "user", "content": prompt}],
            "modalities": ["image", "text"],
        }
        try:
            resp = requests.post(
                OPENROUTER_BASE, headers=headers, json=payload, timeout=120
            )
            if resp.status_code in (429, 503, 404):
                print(f"[Image] {model} → {resp.status_code}, trying next…")
                time.sleep(2)
                continue
            if resp.status_code != 200:
                print(f"[Image] {model} HTTP {resp.status_code}")
                continue

            data    = resp.json()
            content = data["choices"][0]["message"].get("content", [])

            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "image_url":
                        url = part.get("image_url", {}).get("url", "")
                        if "base64," in url:
                            print(f"[Image] ✓ {model}")
                            return url.split("base64,", 1)[1]
            elif isinstance(content, str) and "base64," in content:
                return content.split("base64,", 1)[1]

            images = data.get("images", [])
            if images:
                img = images[0]
                if isinstance(img, str) and "base64," in img:
                    return img.split("base64,", 1)[1]
                if isinstance(img, dict) and "base64," in img.get("url", ""):
                    return img["url"].split("base64,", 1)[1]

            print(f"[Image] {model} → no image data in response")

        except requests.Timeout:
            print(f"[Image] {model} timed out")
        except Exception as e:
            print(f"[Image] {model} error: {e}")

    print("[Image] All models failed — returning None (image is optional)")
    return None
