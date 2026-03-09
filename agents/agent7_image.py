"""
Agent 7 — Image Generator
Model: google/gemini-2.5-flash-preview:free  (Nano Banana via OpenRouter)
Fallback: google/gemini-2.0-flash-exp:free

Uses OpenRouter's image generation endpoint — same OPENROUTER_API_KEY,
no separate Gemini API key needed. GEMINI_API_KEY env var is no longer required.
"""

from utils.openrouter import generate_image

TONE_STYLE = {
    "formal":       "clean editorial photography, professional corporate aesthetic, muted sophisticated palette, high contrast",
    "casual":       "bright warm illustration, friendly modern design, vibrant approachable colors",
    "technical":    "dark futuristic tech aesthetic, deep blues and greens, geometric circuit patterns, cyberpunk",
    "storytelling": "cinematic wide-angle, dramatic lighting, rich colors, evocative atmosphere, movie-poster composition",
}

CATEGORY_HINTS = {
    "ai":            "neural network nodes, glowing data streams, abstract intelligence visualization",
    "cybersecurity": "dark digital shield, binary code matrix, locked padlock motif",
    "technology":    "sleek modern devices, minimalist tech workspace, clean product aesthetic",
    "politics":      "government architecture, abstract governance symbols, civic imagery",
    "science":       "laboratory equipment, molecular structures, cosmic imagery",
    "business":      "modern office architecture, abstract growth visualization, professional environment",
    "crypto":        "blockchain nodes, digital gold coins, decentralized network abstract",
    "health":        "clean medical imagery, human body abstract, wellness and vitality",
    "environment":   "nature meets technology, renewable energy, green sustainable future",
    "current_affairs": "global map abstract, connected world, breaking news aesthetic",
    "space":         "stars, rockets, planetary surfaces, cosmos",
    "geopolitics":   "world map, flags abstract, diplomatic imagery",
}

def agent_generate_image(title: str, topic: str, tone: str, category: str) -> str | None:
    """
    Generate a blog header image via OpenRouter (Nano Banana).
    Returns base64 PNG string, or None if generation fails.
    No extra API key needed — uses OPENROUTER_API_KEY.
    """
    style    = TONE_STYLE.get(tone, TONE_STYLE["formal"])
    cat_hint = CATEGORY_HINTS.get(category, "compelling visual representing the topic")

    prompt = (
        f"Create a professional, striking blog header photograph or illustration "
        f"for an article titled: '{title}'. "
        f"Topic context: {topic}. "
        f"Art direction: {style}. "
        f"Visual elements to include: {cat_hint}. "
        "Composition: wide 16:9 panoramic format, rule of thirds, clean negative space. "

        # Watermark and text prevention — explicit and repeated
        "CRITICAL RULES — you must follow ALL of these without exception: "
        "1. NO watermarks of any kind — no logos, no service marks, no attribution marks. "
        "2. NO text anywhere — no words, no letters, no numbers, no captions, no labels, "
        "   no titles, no signatures, no copyright symbols, no URLs. "
        "3. NO overlays, NO UI elements, NO borders with text, NO badges. "
        "4. The image must be completely clean — pure visual art only. "
        "5. Do NOT add any branding from the image generation service. "

        "The final image should look like a premium stock photo bought from Shutterstock "
        "or Getty Images — completely clean, no markings whatsoever. "
        "Publication-ready, visually memorable, original artwork."
    )

    return generate_image(prompt)
