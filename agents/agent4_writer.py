"""
Agent 4 — Human Blog Writer
Model: anthropic/claude-3.5-sonnet (most human-like, nuanced prose via OpenRouter)

Writes each section with:
- Hook sentence from structure
- Per-section research injected
- Tone-specific writing style
- Natural keyword integration
- Human writing patterns (imperfect starts, varied sentence length, personal asides)
"""

from utils.openrouter import call

WORD_TARGETS = {"short": 150, "medium": 200, "long": 350}

TONE_VOICE = {
    "formal": (
        "Write like a respected industry analyst. Third person. Complete, sophisticated sentences. "
        "No contractions. Build arguments with evidence. Professional gravitas."
    ),
    "casual": (
        "Write like a smart, enthusiastic person sharing something they love. "
        "First person is fine. Use contractions. Short punchy sentences mixed with longer ones. "
        "Add a personal aside or relatable observation once per section."
    ),
    "technical": (
        "Write for engineers and technical practitioners. Use precise terminology. "
        "Reference specific versions, protocols, architectures. Assume high baseline knowledge. "
        "Include technical nuance, trade-offs, and edge cases."
    ),
    "storytelling": (
        "Write with narrative momentum. Start each section with a small scene, anecdote, or vivid example. "
        "Use sensory details. Build toward a payoff. Active voice always. "
        "Vary sentence length dramatically — short punches after long descriptive sentences."
    ),
}

HUMANIZE_INSTRUCTIONS = """
CRITICAL HUMANIZATION RULES — follow every single one:
1. NEVER start a sentence with 'Additionally', 'Furthermore', 'Moreover', 'In conclusion', 'It is important to note', 'It is worth noting'
2. NEVER use these phrases: 'delve into', 'dive into', 'in today's fast-paced world', 'in the ever-evolving landscape', 'game-changer', 'paradigm shift', 'leverage', 'utilize' (use 'use'), 'cutting-edge' (use 'new' or 'latest')
3. VARY sentence length — mix 5-word punches with 25-word flowing sentences
4. Occasionally use sentence fragments for emphasis. Like this.
5. Include one specific, concrete example or analogy per section
6. Show don't tell — instead of 'this is important', explain WHY it matters with a consequence
7. Use em dashes — occasionally — for natural thought flow
8. Write numbers under 10 as words (three, not 3) unless it's a stat
9. Use rhetorical questions sparingly — one per two sections maximum
10. Transition between paragraphs using the last idea of one to lead into the next
"""

def agent_write_blog(
    topic: str,
    title: str,
    structure: dict,
    research: dict,
    tone: str,
    word_count: str,
    seo_keywords: list,
) -> str:
    """
    Writes the complete blog post section by section.
    Returns full markdown-formatted content string.
    """
    words_per_section = WORD_TARGETS.get(word_count, 200)
    tone_voice        = TONE_VOICE.get(tone, TONE_VOICE["formal"])
    hook              = structure.get("hook_sentence", "")
    keywords_str      = ", ".join(seo_keywords) if seo_keywords else "none"
    sections          = structure.get("sections", [])
    per_section_research = research.get("per_section", {})
    overview_research    = research.get("overview", "")

    # Write intro paragraph first
    intro_messages = [
        {
            "role": "system",
            "content": (
                f"{tone_voice}\n\n{HUMANIZE_INSTRUCTIONS}\n\n"
                "Write ONLY the opening/introduction paragraph of a blog post. "
                f"Target: {words_per_section} words. "
                "Start with the provided hook sentence, then expand into context. "
                "Do NOT write a heading. Just the paragraph content."
            )
        },
        {
            "role": "user",
            "content": (
                f"Blog title: {title}\n"
                f"Topic: {topic}\n"
                f"Hook to open with: {hook}\n"
                f"Research context: {overview_research[:800]}\n"
                f"SEO keywords to weave in naturally: {keywords_str}\n\n"
                "Write the opening paragraph."
            )
        }
    ]
    intro = call("writer", intro_messages, temperature=0.8, max_tokens=600)
    full_content = f"{intro}\n\n"

    # Write each section
    for i, section in enumerate(sections):
        heading     = section["heading"]
        key_points  = section.get("key_points", [])
        seo_angle   = section.get("seo_angle", "")
        sec_research = per_section_research.get(heading, overview_research[:600])

        messages = [
            {
                "role": "system",
                "content": (
                    f"{tone_voice}\n\n{HUMANIZE_INSTRUCTIONS}\n\n"
                    f"You are writing section {i+1} of {len(sections)} of a blog post. "
                    f"Target: {words_per_section} words for this section. "
                    "Do NOT include the section heading in your output — just the paragraph content. "
                    f"SEO purpose of this section: {seo_angle}. "
                    f"Naturally include relevant terms from: {keywords_str} if they fit."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Blog title: {title}\n"
                    f"Full topic: {topic}\n"
                    f"This section: {heading}\n"
                    f"Must cover these points: {', '.join(key_points)}\n"
                    f"Research to draw from:\n{sec_research}\n\n"
                    f"Write this section in {words_per_section} words. "
                    "Be specific — use real facts, examples, names from the research."
                )
            }
        ]

        section_text = call("writer", messages, temperature=0.82, max_tokens=1000)
        full_content += f"## {heading}\n\n{section_text}\n\n"

    # Write conclusion
    conclusion_messages = [
        {
            "role": "system",
            "content": (
                f"{tone_voice}\n\n{HUMANIZE_INSTRUCTIONS}\n\n"
                "Write ONLY the conclusion paragraph of the blog post. "
                f"Target: {words_per_section} words. "
                "Synthesize the key insight. End with a forward-looking thought or call to action. "
                "Do NOT start with 'In conclusion' or 'To summarize'. "
                "Do NOT write a heading."
            )
        },
        {
            "role": "user",
            "content": (
                f"Blog title: {title}\n"
                f"Topic: {topic}\n"
                f"Write a powerful, memorable conclusion that leaves readers with something to think about."
            )
        }
    ]
    conclusion = call("writer", conclusion_messages, temperature=0.8, max_tokens=600)
    full_content += f"## Final Thoughts\n\n{conclusion}\n"

    return full_content
