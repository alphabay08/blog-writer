"""
Supabase Database Utility

Run this SQL once in Supabase SQL editor:

CREATE TABLE blog_posts (
    id                UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    created_at        TIMESTAMPTZ DEFAULT now(),
    title             TEXT NOT NULL,
    slug              TEXT,
    category          TEXT,
    tone              TEXT,
    topic             TEXT,
    meta_description  TEXT,
    content           TEXT,
    humanized_content TEXT,
    research_overview TEXT,
    seo_keywords      TEXT[],
    word_count        INTEGER,
    has_image         BOOLEAN DEFAULT false,
    tweet_thread      JSONB,
    linkedin_caption  TEXT,
    hashtags          TEXT[]
);
CREATE INDEX idx_created  ON blog_posts(created_at DESC);
CREATE INDEX idx_category ON blog_posts(category);
"""

import os, json, requests

SUPABASE_URL      = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")

def _h():
    return {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }

def save_blog(data: dict) -> dict | None:
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return None
    payload = {
        "title":             data.get("title", ""),
        "slug":              data.get("slug", ""),
        "category":          data.get("category", ""),
        "tone":              data.get("tone", ""),
        "topic":             data.get("topic", ""),
        "meta_description":  data.get("meta_description", ""),
        "content":           data.get("content", ""),
        "humanized_content": data.get("humanized_content", ""),
        "research_overview": data.get("research_overview", ""),
        "seo_keywords":      data.get("seo_keywords", []),
        "word_count":        len(data.get("humanized_content", "").split()),
        "has_image":         bool(data.get("image_b64")),
        "tweet_thread":      json.dumps(data.get("tweet_thread", [])),
        "linkedin_caption":  data.get("linkedin_caption", ""),
        "hashtags":          data.get("hashtags", []),
    }
    try:
        r = requests.post(f"{SUPABASE_URL}/rest/v1/blog_posts",
                          headers=_h(), json=payload, timeout=10)
        r.raise_for_status()
        res = r.json()
        return res[0] if res else None
    except Exception as e:
        print(f"[DB] Save error: {e}")
        return None

def get_history(limit=20, category=None) -> list:
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return []
    params = (f"?select=id,title,slug,category,tone,created_at,"
              f"word_count,meta_description,has_image"
              f"&order=created_at.desc&limit={limit}")
    if category:
        params += f"&category=eq.{category}"
    try:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/blog_posts{params}",
                         headers=_h(), timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[DB] Fetch error: {e}")
        return []

def get_blog_by_id(blog_id: str) -> dict | None:
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return None
    try:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/blog_posts?id=eq.{blog_id}&select=*",
                         headers=_h(), timeout=10)
        r.raise_for_status()
        res = r.json()
        return res[0] if res else None
    except Exception as e:
        print(f"[DB] Get error: {e}")
        return None
