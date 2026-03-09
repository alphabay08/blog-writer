"""
Agent 1 — Topic Discovery (Free Tier Edition)
Model: nvidia/nemotron-3-nano-30b-a3b:free (256K ctx, tools)
Fallback: meta-llama/llama-3.3-70b-instruct:free

Without Perplexity's live search, this agent uses a smarter strategy:
- Draws on the model's extensive training knowledge of recurring patterns
- Reasons about what is LIKELY trending/important in the category right now
- Generates a specific, concrete, compelling topic — never vague or generic
- Supports manual topic override: if user types their own topic,
  this agent formats and enriches it instead of auto-discovering

NOTE: Topics are knowledge-based (not live-scraped). They reflect real,
high-importance angles that professional audiences consistently care about.
"""

from utils.openrouter import call_json

CATEGORY_CONTEXT = {
    "current_affairs": (
        "major geopolitical tensions, economic shifts, climate events, "
        "humanitarian crises, international summits, election outcomes"
    ),
    "politics": (
        "legislation battles, election campaigns, policy reversals, "
        "political scandals, government budget fights, party dynamics"
    ),
    "technology": (
        "major product launches, startup funding rounds, big tech regulation, "
        "hardware breakthroughs, platform changes, open source milestones"
    ),
    "ai": (
        "new model releases, AI regulation debates, AGI timelines, "
        "AI safety controversies, enterprise AI adoption, AI in jobs, "
        "open source vs closed AI battles, inference cost breakthroughs"
    ),
    "cybersecurity": (
        "ransomware attacks on critical infrastructure, zero-day exploits, "
        "data breaches at major companies, nation-state hacking campaigns, "
        "AI-powered cyberattacks, new security legislation"
    ),
    "science": (
        "breakthrough research in physics, biology, medicine, materials science, "
        "space discoveries, quantum computing milestones, climate science updates"
    ),
    "business": (
        "major mergers and acquisitions, earnings surprises, layoff waves, "
        "supply chain disruptions, CEO controversies, market sector shifts"
    ),
    "health": (
        "new drug approvals, pandemic preparedness, mental health crises, "
        "longevity research, healthcare system reforms, medical AI tools"
    ),
    "environment": (
        "extreme weather records, carbon policy battles, renewable energy milestones, "
        "biodiversity loss, ocean health, corporate ESG controversies"
    ),
    "crypto": (
        "Bitcoin ETF developments, DeFi protocol hacks, regulatory crackdowns, "
        "stablecoin controversies, Layer 2 adoption, institutional crypto moves"
    ),
    "space": (
        "rocket launches, Mars mission updates, satellite internet expansion, "
        "space tourism, asteroid mining plans, lunar base developments"
    ),
    "geopolitics": (
        "trade war escalations, military alliance shifts, sanctions impacts, "
        "energy diplomacy, territorial disputes, diplomatic breakthroughs"
    ),
}


def agent_discover_topic(category: str, manual_topic: str = "") -> dict:
    """
    Discover or format a blog topic.

    If manual_topic is provided by user → format + enrich it.
    Otherwise → AI generates a specific, compelling topic from training knowledge.

    Returns: { topic, why_trending, key_angle, source_hint, category, is_manual }
    """
    if manual_topic and manual_topic.strip():
        return _format_manual_topic(manual_topic.strip(), category)
    return _ai_discover(category)


def _ai_discover(category: str) -> dict:
    context = CATEGORY_CONTEXT.get(category, f"major developments in {category}")

    messages = [
        {
            "role": "system",
            "content": (
                "You are a senior editor at a major digital publication. "
                "Identify ONE highly specific, compelling, currently relevant blog topic. "
                "\n\nRULES:\n"
                "- SPECIFIC: name real companies, people, technologies, or events\n"
                "- BAD: 'The future of AI'  |  "
                "GOOD: 'Why OpenAI o3 is forcing Google to rethink its Gemini roadmap'\n"
                "- Pick TIMELESS-RELEVANT topics: important any week, not just one day\n"
                "- Professional audience: CTOs, analysts, executives, enthusiasts\n"
                "Return ONLY raw JSON — no markdown, no preamble — with keys: "
                '"topic" (1-2 sentences, very specific), '
                '"why_trending" (why it matters now, 1 sentence), '
                '"key_angle" (sharpest blog angle, 1 sentence), '
                '"source_hint" (type of outlets that cover this).'
            )
        },
        {
            "role": "user",
            "content": (
                f"Category: {category}\n"
                f"High-interest angles in this space: {context}\n\n"
                "Choose the single most compelling, specific topic a professional "
                "audience would want to read about. Be concrete and bold."
            )
        }
    ]

    try:
        result = call_json("discover", messages, temperature=0.6)
        result["category"]  = category
        result["is_manual"] = False
        result.setdefault("topic",       f"Key developments reshaping {category} in 2025")
        result.setdefault("why_trending","This space is undergoing rapid transformation.")
        result.setdefault("key_angle",   "What this means for professionals and what to watch.")
        result.setdefault("source_hint", "Leading industry publications and analyst reports")
        return result
    except Exception as e:
        print(f"[Agent 1] Discovery error: {e}")
        return {
            "topic":       f"The most important shifts happening in {category} right now",
            "why_trending":"This area is evolving rapidly with real-world consequences.",
            "key_angle":   "Breaking down the changes and what they mean for practitioners.",
            "source_hint": "Industry analysts and major publications",
            "category":    category,
            "is_manual":   False,
        }


def _format_manual_topic(topic: str, category: str) -> dict:
    """Enrich a user-provided topic into the standard discovery structure."""
    messages = [
        {
            "role": "system",
            "content": (
                "You are a content strategist. Given a blog topic from a user, "
                "frame it compellingly for a professional audience. "
                "Return ONLY raw JSON with keys: "
                '"topic" (refine slightly if needed, keep close to original), '
                '"why_trending" (why this matters now, 1 sentence), '
                '"key_angle" (sharpest blog angle, 1 sentence), '
                '"source_hint" (who covers this topic). '
                "No markdown. Raw JSON only."
            )
        },
        {
            "role": "user",
            "content": f"User topic: {topic}\nCategory: {category}"
        }
    ]
    try:
        result = call_json("discover", messages, temperature=0.5)
        result["category"]  = category
        result["is_manual"] = True
        result.setdefault("topic",       topic)
        result.setdefault("why_trending","An important, high-interest topic for professional audiences.")
        result.setdefault("key_angle",   "Providing clarity, context, and actionable insight.")
        result.setdefault("source_hint", "Industry experts and thought leaders")
        return result
    except Exception:
        return {
            "topic":       topic,
            "why_trending":"An important topic for professional audiences.",
            "key_angle":   "Expert context and actionable insight.",
            "source_hint": "Industry publications",
            "category":    category,
            "is_manual":   True,
        }
