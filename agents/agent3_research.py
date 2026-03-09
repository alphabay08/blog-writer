"""
Agent 3 — Deep Research
Model: perplexity/llama-3.1-sonar-huge-128k-online
(Largest Perplexity model — 128k context, real-time web, extensive citations)

Pulls verifiable, current facts, stats, quotes, and data points
organized per section so Agent 4 can write with precision.
"""

from utils.openrouter import call

def agent_research(topic: str, structure: dict) -> dict:
    """
    Returns a dict:
    {
      "overview": str,          ← general topic summary with key facts
      "per_section": {          ← section heading → specific research for that section
        "Section Heading": str,
        ...
      },
      "expert_quotes": [str],   ← notable quotes from real people if found
      "key_stats": [str],       ← bullet-point stats and data points
      "sources": [str],         ← source names/outlets found
    }
    """
    sections = structure.get("sections", [])
    headings = [s["heading"] for s in sections]

    # Overall research call
    overview_messages = [
        {
            "role": "system",
            "content": (
                "You are a senior research analyst and investigative journalist "
                "with deep expertise across technology, business, science, and policy. "
                "Draw on your comprehensive knowledge to provide thorough research. "
                "\n\nProvide:\n"
                "1. Key established facts with approximate timeframes\n"
                "2. Concrete statistics and data points (cite known studies/reports)\n"
                "3. Real expert names and their known positions or quotes on this topic\n"
                "4. Historical context and how we got here\n"
                "5. Competing perspectives and ongoing debates\n"
                "6. Real-world implications and consequences\n"
                "\nBe SPECIFIC — use real company names, real people, real numbers. "
                "If you cite a statistic, name the organization or study it comes from. "
                "Format as a clear numbered list of findings. "
                "Do NOT say 'I don't have access to the internet' — use your knowledge."
            )
        },
        {
            "role": "user",
            "content": (
                f"Research this topic thoroughly: {topic}\n\n"
                f"Focus on these specific angles: {', '.join(headings)}\n\n"
                "Give me 10-15 specific, well-grounded research findings "
                "that a blog writer can use to write authoritative content."
            )
        }
    ]

    overview = call("research", overview_messages, temperature=0.2, max_tokens=3000)

    # Per-section targeted research
    per_section = {}
    for section in sections[:5]:  # Limit to 5 to avoid rate limits
        heading = section["heading"]
        key_points = section.get("key_points", [])

        sec_messages = [
            {
                "role": "system",
                "content": (
                    "You are a specialist researcher with deep domain expertise. "
                    "Provide 3-5 highly specific, knowledge-based facts, statistics, "
                    "or insights for this blog section. Use real names, real organizations, "
                    "real data points. Be concrete — no vague generalities. Under 200 words."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Blog topic: {topic}\n"
                    f"Section I'm writing: {heading}\n"
                    f"Key points to cover: {', '.join(key_points)}\n\n"
                    "Give me targeted research for this specific section."
                )
            }
        ]

        try:
            per_section[heading] = call("research", sec_messages, temperature=0.2, max_tokens=400)
        except Exception:
            per_section[heading] = ""

    return {
        "overview": overview,
        "per_section": per_section,
        "raw_for_writer": overview,  # full context for writer agent
    }
