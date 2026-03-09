"""
Agent 5 — Deep Humanizer
Model: mistralai/mistral-small-3.1-24b-instruct:free

Rewrites AI-generated blog content to:
1. Pass AI detectors (GPTZero, Originality.ai, Copyleaks, Winston AI)
2. Match human writing patterns — burstiness, imperfections, personality
3. Sound like a real expert author, not a language model
4. Preserve every fact, stat, name, and number from the original

HOW AI DETECTORS WORK (so we can beat them):
- Perplexity: AI uses predictable, "safe" word choices. Humans use surprising ones.
- Burstiness: AI sentences are uniform length. Humans mix short punches with long flows.
- Transition words: AI over-uses "Furthermore", "Moreover", "Additionally", "In conclusion"
- Hedging: AI hedges constantly ("it is worth noting", "it is important to consider")
- Structure: AI always does Intro → Point → Example → Transition. Humans wander.
"""

from utils.openrouter import call

HUMANIZER_SYSTEM = """
You are a professional human ghostwriter and editor. Your ONLY job is to rewrite
the given AI-written blog section so it reads exactly like a real human expert wrote it.

You MUST follow every single rule below. No exceptions.

━━━ BANNED WORDS AND PHRASES (replace every single one) ━━━
Never use ANY of these — they instantly flag AI authorship:
- Transition openers: "Moreover", "Furthermore", "Additionally", "In addition",
  "It is worth noting", "It is important to note", "Notably", "Interestingly",
  "In conclusion", "To summarize", "To recap", "In summary"
- Filler phrases: "delve into", "dive into", "in today's fast-paced world",
  "in the ever-evolving landscape", "it goes without saying", "needless to say",
  "at the end of the day", "when all is said and done", "the fact of the matter"
- Weak AI verbs: "utilize" → use, "leverage" → use/apply, "facilitate" → help,
  "implement" → build/set up, "demonstrate" → show, "ensure" → make sure,
  "provide" → give, "enable" → let/allow, "enhance" → improve, "optimize" → improve
- Overused adjectives: "crucial", "vital", "pivotal", "paramount", "groundbreaking",
  "revolutionary", "game-changing", "transformative", "unprecedented", "cutting-edge"
  → Replace with plain specific language: "important", "new", "first of its kind", etc.

━━━ SENTENCE STRUCTURE RULES ━━━
1. BURSTINESS — vary sentence length dramatically:
   Short. Then a longer sentence that builds on the idea with more detail and context.
   Then short again. It creates rhythm.
2. Start 20% of sentences with something other than the subject:
   "What nobody tells you is..." / "Here's the thing:" / "That said," / "Still,"
3. Use em dashes — for natural thought interruptions — like this
4. Occasionally use a sentence fragment. For emphasis. Like that.
5. One rhetorical question per 2 sections maximum.
6. Never end two consecutive paragraphs with the same type of sentence.

━━━ PARAGRAPH STRUCTURE RULES ━━━
1. Vary paragraph length: mix 1-sentence paragraphs with 4-5 sentence ones
2. First paragraph of each section: start with the most interesting thing, not background
3. Do NOT always transition from one paragraph to the next with a linking sentence
4. Occasionally let a paragraph stand alone — make its point and stop
5. One unexpected analogy or comparison per section (makes it feel human and original)

━━━ VOICE AND PERSONALITY RULES ━━━
1. Write in first person occasionally when the tone allows: "I've seen this pattern before"
2. Show genuine opinion once per section: "This is the part most people get wrong"
3. Add one small parenthetical aside per 3 paragraphs: (and yes, that actually matters)
4. Use contraction naturally where formal tone allows: "it's", "they're", "doesn't"
5. Reference the reader occasionally: "If you've worked in this space..."

━━━ WHAT TO ABSOLUTELY PRESERVE ━━━
- Every factual claim, statistic, number, and named source
- Every section heading in ## format
- The overall tone (formal/casual/technical/storytelling) passed in
- Approximate word count — do not drastically shorten or lengthen

━━━ OUTPUT FORMAT ━━━
Return ONLY the rewritten content. No preamble. No "Here is the rewritten version:".
No explanation. Just the rewritten blog section.
"""

def agent_humanize(content: str, tone: str) -> str:
    """
    Deep-humanizes the entire blog post section by section.
    Processes intro, each ## section, and conclusion separately
    to stay within token limits and maintain quality per section.
    """

    # Split on section headings
    parts   = content.split("\n## ")
    intro   = parts[0]
    sections = parts[1:] if len(parts) > 1 else []

    humanized_parts = []

    # ── Humanize intro ────────────────────────────────────────────────────
    humanized_parts.append(_humanize_chunk(
        intro, tone,
        chunk_type="opening",
        extra_instruction=(
            "This is the OPENING of the blog. The very first sentence must grab "
            "attention immediately — start with a surprising fact, a bold claim, "
            "or a vivid scene. Do NOT start with 'In today's world' or 'Have you ever'."
        )
    ))

    # ── Humanize each section ─────────────────────────────────────────────
    for i, section in enumerate(sections):
        is_last = (i == len(sections) - 1)
        humanized_parts.append(_humanize_chunk(
            f"## {section}", tone,
            chunk_type="conclusion" if is_last else "body_section",
            extra_instruction=(
                "This is the FINAL SECTION. End the entire blog with a forward-looking "
                "thought, a call to reflection, or a memorable closing line. "
                "Do NOT start with 'In conclusion' or 'To summarize'."
            ) if is_last else ""
        ))

    return "\n\n".join(humanized_parts)


def _humanize_chunk(
    chunk: str,
    tone: str,
    chunk_type: str = "body_section",
    extra_instruction: str = ""
) -> str:
    """Humanize a single chunk (intro or one section)."""

    tone_note = {
        "formal":       "Authoritative but NOT stiff. Sophisticated sentences but real voice.",
        "casual":       "Warm, friendly, first-person-friendly. Conversational but not sloppy.",
        "technical":    "Expert-level precision. Use correct jargon but still vary sentence length.",
        "storytelling": "Narrative momentum. Every paragraph should make the reader want to read the next.",
    }.get(tone, "Professional and clear.")

    try:
        result = call(
            "humanizer",
            [
                {"role": "system", "content": HUMANIZER_SYSTEM},
                {
                    "role": "user",
                    "content": (
                        f"Tone: {tone} — {tone_note}\n"
                        f"Chunk type: {chunk_type}\n"
                        + (f"Special instruction: {extra_instruction}\n" if extra_instruction else "")
                        + f"\nRewrite this to sound completely human:\n\n{chunk}"
                    )
                }
            ],
            temperature=0.88,
            max_tokens=1400
        )

        # Safety: ensure ## heading is preserved if it was in input
        if chunk.startswith("## ") and not result.startswith("## "):
            heading = chunk.split("\n")[0]
            result  = heading + "\n\n" + result

        return result

    except Exception as e:
        print(f"[Humanizer] Chunk failed: {e} — returning original")
        return chunk
