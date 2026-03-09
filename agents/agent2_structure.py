"""
Agent 2 — Title Options + Blog Structure + SEO
Model: openai/gpt-4o (best JSON adherence and SEO strategy)

Takes the discovered topic, user's tone, keywords, and word count.
Returns 3 title variants + full section structure with SEO optimization.
"""

from utils.openrouter import call_json

TONE_GUIDANCE = {
    "formal":       "Authoritative, sophisticated, third-person perspective. Avoid contractions. Suitable for Harvard Business Review.",
    "casual":       "Warm, friendly, first-person. Use contractions. Like a smart friend explaining something over coffee.",
    "technical":    "Precise, jargon-rich for expert readers. Reference tools, frameworks, specs. Like a senior engineer's blog.",
    "storytelling": "Narrative-driven. Open with a scene or anecdote. Build tension. Use active voice and vivid language.",
}

def agent_title_and_structure(
    topic: str,
    seo_keywords: list,
    tone: str,
    word_count: str,
    category: str,
) -> dict:
    """
    Returns:
    {
      title_options: [str, str, str],
      meta_description: str,
      slug: str,
      hook_sentence: str,      ← opening line for the blog
      sections: [
        { heading: str, key_points: [str, str, str], seo_angle: str }
      ]
    }
    """
    keywords_str = ", ".join(seo_keywords) if seo_keywords else "none — use topically relevant terms naturally"
    tone_instr   = TONE_GUIDANCE.get(tone, TONE_GUIDANCE["formal"])
    wc_map       = {"short": "~500 words (3 sections)", "medium": "~1000 words (5 sections)", "long": "~2000 words (7 sections)"}
    wc_instr     = wc_map.get(word_count, wc_map["medium"])
    num_sections = {"short": 3, "medium": 5, "long": 7}.get(word_count, 5)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a world-class SEO strategist and content architect. "
                f"Tone to use: {tone_instr}. "
                "Return ONLY a raw JSON object. No markdown. No explanation. "
                "The JSON must have these exact keys: "
                '"title_options" (array of 3 strings — each a distinct, compelling title), '
                '"meta_description" (string, exactly 150-155 characters, includes primary keyword), '
                '"slug" (string, URL-friendly, hyphen-separated, max 60 chars), '
                '"hook_sentence" (string — one powerful opening sentence that grabs attention immediately), '
                f'"sections" (array of {num_sections} objects, each with: '
                '"heading" string, "key_points" array of 3 specific strings, "seo_angle" string explaining SEO purpose of this section). '
                "Make every title option distinct in framing: one informational, one opinion/bold, one listicle/how-to. "
                "Naturally integrate SEO keywords throughout structure without stuffing."
            )
        },
        {
            "role": "user",
            "content": (
                f"Topic: {topic}\n"
                f"Category: {category}\n"
                f"Target length: {wc_instr}\n"
                f"SEO keywords to include: {keywords_str}\n\n"
                "Generate the full blog structure."
            )
        }
    ]

    result = call_json("structure", messages, temperature=0.75)
    result["tone"] = tone
    result["word_count"] = word_count
    result["seo_keywords"] = seo_keywords
    return result
