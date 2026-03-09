"""
Agent 6 — Social Media Repurposing
Model: meta-llama/llama-3.3-70b-instruct:free  (fast, creative)
Caption model: openai/gpt-oss-120b:free  (format-precise)

Generates:
1. Twitter/X thread (5 tweets)
2. LinkedIn caption — description + hashtags formatted for copy-paste posting.
   No OAuth. No API. User copies and pastes manually.
   Caption includes: hook line, key insights, CTA, and 5-7 hashtags.
"""

import json
from utils.openrouter import call, call_json

def agent_social_repurpose(title: str, content: str, tone: str, topic: str) -> dict:
    """
    Returns:
    {
      tweet_thread: [str x5],
      linkedin_caption: str,   ← ready-to-paste LinkedIn post description + hashtags
      hashtags: [str],         ← extracted hashtag list for easy copy
    }
    """
    excerpt = content[:3000]

    messages = [
        {
            "role": "system",
            "content": (
                "You are a viral social media strategist. "
                "Return ONLY raw JSON with these exact keys:\n"
                '"tweet_thread": array of exactly 5 strings, each under 270 chars, '
                'numbered "1/5" through "5/5". First tweet = hook. Last tweet = CTA.\n'
                '"linkedin_caption": full LinkedIn post string ready to copy-paste. '
                "Rules: (1) First line = bold hook, max 12 words, no emoji, stops scroll. "
                "(2) Blank line after first line. "
                "(3) Body = single-sentence paragraphs, blank line between each. "
                "(4) 4-6 key insights as standalone lines. "
                "(5) One question near end to drive comments. "
                "(6) Final line = 5-7 relevant hashtags only. "
                "Total 180-250 words.\n"
                '"hashtags": array of 5-7 hashtag strings (with # prefix).\n'
                "No markdown in values. Raw JSON only."
            )
        },
        {
            "role": "user",
            "content": (
                f"Title: {title}\nTopic: {topic}\nTone: {tone}\n\n"
                f"Blog content:\n{excerpt}"
            )
        }
    ]

    try:
        result = call_json("social", messages, temperature=0.85)
        return {
            "tweet_thread":      result.get("tweet_thread", []),
            "linkedin_caption":  result.get("linkedin_caption", ""),
            "hashtags":          result.get("hashtags", []),
        }
    except Exception as e:
        print(f"[Social Agent] {e}")
        tags = ["#blog", "#content", "#writing", f"#{category_slug(topic)}"]
        return {
            "tweet_thread":      [f"Just published: {title}", "Link in bio. 🔗"],
            "linkedin_caption":  f"{title}\n\n{topic}\n\n" + " ".join(tags),
            "hashtags":          tags,
        }


def category_slug(text: str) -> str:
    import re
    return re.sub(r"[^a-zA-Z0-9]", "", text.split()[:1][0] if text.split() else "blog")
