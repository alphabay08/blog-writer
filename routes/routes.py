"""
API Routes — v3 Final (No LinkedIn OAuth)

Blog pipeline:
  POST /api/blog/discover          — Agent 1: topic discovery
  POST /api/blog/titles            — Agent 2: structure + 3 titles
  POST /api/blog/generate          — Agents 3-7: full pipeline
  POST /api/blog/download/txt      — Download .txt
  POST /api/blog/download/docx     — Download .docx
  POST /api/blog/download/blogimg  — Download blog as styled PNG image (for LinkedIn)

History:
  GET  /api/history/               — List past posts
  GET  /api/history/<id>           — Get single post
"""

import io, re, json, base64, textwrap
from flask import Blueprint, request, jsonify, send_file

from agents.agent1_discover  import agent_discover_topic
from agents.agent2_structure import agent_title_and_structure
from agents.agent3_research  import agent_research
from agents.agent4_writer    import agent_write_blog
from agents.agent5_humanizer import agent_humanize
from agents.agent6_social    import agent_social_repurpose
from utils.db                import save_blog, get_history, get_blog_by_id
from utils.docx_gen          import generate_docx

blog_bp    = Blueprint("blog",    __name__)
history_bp = Blueprint("history", __name__)


# ═══════════════════════════════════════════════════════════
# BLOG ROUTES
# ═══════════════════════════════════════════════════════════

@blog_bp.route("/discover", methods=["POST"])
def discover():
    d            = request.get_json()
    category     = d.get("category", "technology").strip()
    manual_topic = d.get("manual_topic", "").strip()
    try:
        result = agent_discover_topic(category, manual_topic)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@blog_bp.route("/titles", methods=["POST"])
def get_titles():
    d            = request.get_json()
    topic        = d.get("topic", "").strip()
    seo_keywords = d.get("seo_keywords", [])
    tone         = d.get("tone", "formal")
    word_count   = d.get("word_count", "medium")
    category     = d.get("category", "technology")
    if not topic:
        return jsonify({"success": False, "error": "topic is required"}), 400
    try:
        structure = agent_title_and_structure(topic, seo_keywords, tone, word_count, category)
        return jsonify({"success": True, "data": structure})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@blog_bp.route("/generate", methods=["POST"])
def generate():
    d             = request.get_json()
    topic         = d.get("topic", "")
    chosen_title  = d.get("chosen_title", "")
    structure     = d.get("structure", {})
    seo_keywords  = d.get("seo_keywords", [])
    tone          = d.get("tone", "formal")
    word_count    = d.get("word_count", "medium")
    category      = d.get("category", "technology")
    slug          = d.get("slug", _slugify(chosen_title))
    author_name   = d.get("author_name", "")

    if not topic or not chosen_title or not structure:
        return jsonify({"success": False, "error": "topic, chosen_title, structure required"}), 400

    try:
        # Agent 3: Research
        research = agent_research(topic, structure)

        # Agent 4: Write
        raw_content = agent_write_blog(
            topic, chosen_title, structure,
            research, tone, word_count, seo_keywords
        )

        # Agent 5: Humanize
        humanized = agent_humanize(raw_content, tone)

        # Agent 6: Social + LinkedIn caption
        social = agent_social_repurpose(chosen_title, humanized, tone, topic)

        # Agent 7: Image — fetch a real photo from Unsplash (free, no key needed)
        # Unsplash source API returns a real photo redirect for any keyword.
        # Much more reliable than OpenRouter free image generation (which returns None).
        image_b64 = _fetch_unsplash_image(chosen_title, topic, category, tone)

        result = {
            "title":             chosen_title,
            "slug":              slug,
            "category":          category,
            "tone":              tone,
            "topic":             topic,
            "meta_description":  structure.get("meta_description", ""),
            "content":           raw_content,
            "humanized_content": humanized,
            "research_overview": research.get("overview", ""),
            "seo_keywords":      seo_keywords,
            "image_b64":         image_b64,
            "tweet_thread":      social.get("tweet_thread", []),
            "linkedin_caption":  social.get("linkedin_caption", ""),
            "hashtags":          social.get("hashtags", []),
            "word_count":        len(humanized.split()),
            "author_name":       author_name,
        }

        # Save to Supabase
        try:
            saved = save_blog(result)
            if saved:
                result["db_id"] = saved.get("id")
        except Exception:
            pass

        return jsonify({"success": True, "data": result})

    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@blog_bp.route("/download/txt", methods=["POST"])
def download_txt():
    d        = request.get_json()
    content  = d.get("humanized_content") or d.get("content", "")
    title    = d.get("title", "blog")
    tweets   = "\n".join(f"  {t}" for t in d.get("tweet_thread", []))
    caption  = d.get("linkedin_caption", "")
    research = d.get("research_overview", "")

    full = (
        f"TITLE: {title}\n"
        f"SLUG:  /{d.get('slug','')}\n"
        f"META:  {d.get('meta_description','')}\n"
        f"{'='*70}\n\n"
        f"BLOG CONTENT:\n\n{content}\n\n"
        f"{'='*70}\n\n"
        f"RESEARCH NOTES:\n\n{research}\n\n"
        f"{'='*70}\n\n"
        f"LINKEDIN CAPTION (copy-paste):\n\n{caption}\n\n"
        f"{'='*70}\n\n"
        f"TWITTER / X THREAD:\n\n{tweets}\n"
    )
    buf = io.BytesIO(full.encode("utf-8"))
    buf.seek(0)
    return send_file(buf, mimetype="text/plain", as_attachment=True,
                     download_name=f"{_slugify(title)[:50]}.txt")


@blog_bp.route("/download/docx", methods=["POST"])
def download_docx():
    d          = request.get_json()
    docx_bytes = generate_docx(d)
    if not docx_bytes:
        return jsonify({"error": "DOCX generation failed"}), 500
    buf = io.BytesIO(docx_bytes)
    buf.seek(0)
    return send_file(
        buf,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        as_attachment=True,
        download_name=f"{_slugify(d.get('title','blog'))[:50]}.docx"
    )


@blog_bp.route("/download/blogimg", methods=["POST"])
def download_blogimg():
    """
    Generate and return a styled PNG image of the blog post
    suitable for posting on LinkedIn as a document/image post.
    Uses html2image approach via a self-contained HTML → rendered as PNG via headless Chrome.
    Falls back to a clean text-card PNG if Chrome unavailable.
    """
    d         = request.get_json()
    title     = d.get("title", "Blog Post")
    content   = d.get("humanized_content") or d.get("content", "")
    meta      = d.get("meta_description", "")
    category  = d.get("category", "")
    tone      = d.get("tone", "")
    hashtags  = d.get("hashtags", [])
    image_b64 = d.get("image_b64", "")

    try:
        png_bytes = _render_blog_png(title, content, meta, category, hashtags, image_b64)
        buf = io.BytesIO(png_bytes)
        buf.seek(0)
        return send_file(buf, mimetype="image/png", as_attachment=True,
                         download_name=f"{_slugify(title)[:40]}-linkedin.png")
    except Exception as e:
        return jsonify({"error": f"Image render failed: {e}"}), 500


def _fetch_unsplash_image(title: str, topic: str, category: str, tone: str) -> str | None:
    """
    Fetch a real category-relevant photo for the thumbnail.

    Priority order:
      1. Unsplash Source (free, no key) — https://source.unsplash.com
      2. Picsum + category seed (free, no key) — deterministic beautiful photo
      3. Pixabay (free, no key needed for basic hits)

    All return a real photo. Falls back gracefully — never crashes.
    """
    import requests

    CATEGORY_KEYWORDS = {
        "cybersecurity":   "cybersecurity hacker security network",
        "ai":              "artificial intelligence technology robot future",
        "technology":      "technology computer digital innovation",
        "politics":        "politics government capitol democracy",
        "science":         "science laboratory research experiment",
        "business":        "business office corporate finance",
        "health":          "healthcare medical doctor hospital",
        "environment":     "environment nature climate sustainability",
        "crypto":          "cryptocurrency bitcoin blockchain digital",
        "space":           "space galaxy stars rocket cosmos",
        "geopolitics":     "world globe diplomacy international",
        "current_affairs": "news journalism media global",
    }

    # Unsplash: deterministic seed per category so same category → consistent style
    CATEGORY_SEEDS = {
        "cybersecurity": 1084, "ai": 2048, "technology": 512,
        "politics": 777,  "science": 333,  "business": 999,
        "health": 444,    "environment": 222, "crypto": 1337,
        "space": 4096,    "geopolitics": 888, "current_affairs": 100,
    }

    kw_raw  = CATEGORY_KEYWORDS.get(category, category + " " + topic[:30])
    kw_url  = requests.utils.quote(kw_raw.replace(" ", ","))

    # ── Attempt 1: Unsplash Source ─────────────────────────────────────────────
    try:
        url  = f"https://source.unsplash.com/1200x675/?{kw_url}"
        resp = requests.get(url, timeout=12, allow_redirects=True)
        if resp.status_code == 200 and len(resp.content) > 8000:
            print(f"[Image] ✓ Unsplash ({len(resp.content)//1024}KB) — {category}")
            return base64.b64encode(resp.content).decode()
    except Exception as e:
        print(f"[Image] Unsplash failed: {e}")

    # ── Attempt 2: Picsum with category seed (always works) ────────────────────
    try:
        seed = CATEGORY_SEEDS.get(category, abs(hash(category)) % 1000)
        url  = f"https://picsum.photos/seed/{seed}/1200/675"
        resp = requests.get(url, timeout=12, allow_redirects=True)
        if resp.status_code == 200 and len(resp.content) > 8000:
            print(f"[Image] ✓ Picsum seed={seed} ({len(resp.content)//1024}KB)")
            return base64.b64encode(resp.content).decode()
    except Exception as e:
        print(f"[Image] Picsum failed: {e}")

    # ── Attempt 3: Pixabay (free, no key for simple queries) ───────────────────
    try:
        kw_pix = kw_raw.replace(" ", "+")
        url    = f"https://pixabay.com/api/?key=47058696-b39dda6f0785a16b5c2e05e7f&q={kw_pix}&image_type=photo&orientation=horizontal&per_page=3&safesearch=true"
        resp   = requests.get(url, timeout=10)
        if resp.status_code == 200:
            hits = resp.json().get("hits", [])
            if hits:
                img_url  = hits[0].get("webformatURL") or hits[0].get("largeImageURL")
                img_resp = requests.get(img_url, timeout=12)
                if img_resp.status_code == 200 and len(img_resp.content) > 5000:
                    print(f"[Image] ✓ Pixabay ({len(img_resp.content)//1024}KB)")
                    return base64.b64encode(img_resp.content).decode()
    except Exception as e:
        print(f"[Image] Pixabay failed: {e}")

    print(f"[Image] All photo sources failed — thumbnail will use gradient background")
    return None


def _render_blog_png(title, content, meta, category, hashtags, image_b64):
    """
    Render a clean THUMBNAIL style image — like YouTube or Medium.
    Layout:
      ┌──────────────────────────────┐
      │                              │
      │   AI-generated photo (top)   │  ~55% height
      │   category badge on photo    │
      │                              │
      ├──────────────────────────────┤
      │  TITLE — big, bold, 2-3 ln   │  dominant text
      │  subtitle / meta (1 line)    │
      │  hashtags                    │
      │  branding                    │
      └──────────────────────────────┘
    No paragraphs. No bullets. No body text. Just title + image.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        raise RuntimeError("Pillow not installed.")

    W, H = 1200, 675          # 16:9 — standard LinkedIn / YouTube thumbnail size
    PAD  = 48

    WHITE  = (255, 255, 255)
    YELLOW = (255, 214, 10)
    SHADOW = (0,   0,   0)

    img  = Image.new("RGB", (W, H), (15, 15, 20))
    draw = ImageDraw.Draw(img)

    def fb(s):
        try:    return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", s)
        except: return ImageFont.load_default()
    def fr(s):
        try:    return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", s)
        except: return ImageFont.load_default()

    # ── 1. AI IMAGE fills the ENTIRE canvas as background ──────────────────────
    if image_b64:
        try:
            raw   = base64.b64decode(image_b64)
            photo = Image.open(io.BytesIO(raw)).convert("RGB")
            pw, ph = photo.size
            # Cover-crop: fill W×H without stretching
            if pw / ph > W / H:            # image wider → crop left/right
                new_w = int(ph * W / H)
                photo = photo.crop(((pw - new_w) // 2, 0, (pw + new_w) // 2, ph))
            else:                           # image taller → crop top/bottom
                new_h = int(pw * H / W)
                photo = photo.crop((0, (ph - new_h) // 2, pw, (ph + new_h) // 2))
            photo = photo.resize((W, H), Image.LANCZOS)
            img.paste(photo, (0, 0))
        except Exception as e:
            print(f"[Thumb] photo error: {e}")

    # ── 2. DARK GRADIENT over bottom half so title is always readable ───────────
    grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd   = ImageDraw.Draw(grad)
    for py in range(H):
        frac  = py / H
        # Transparent at top, solid dark at bottom
        alpha = int(255 * max(0, (frac - 0.25) / 0.75) ** 1.4)
        gd.rectangle([0, py, W, py + 1], fill=(0, 0, 0, min(alpha, 218)))
    img.paste(grad, (0, 0), grad)

    # ── 3. CATEGORY BADGE — top-left ───────────────────────────────────────────
    cat  = (category or "BLOG").upper()
    bfnt = fb(17)
    bp   = 9
    bb   = draw.textbbox((0, 0), cat, font=bfnt)
    bw   = bb[2] - bb[0] + bp * 2 + 2
    bh   = bb[3] - bb[1] + bp
    draw.rectangle([PAD, 30, PAD + bw, 30 + bh], fill=YELLOW)
    draw.text((PAD + bp, 30 + bp // 2), cat, font=bfnt, fill=(10, 10, 10))

    # ── 4. TITLE — big bold text near bottom of image ──────────────────────────
    tf     = fb(58)
    max_px = W - PAD * 2

    # pixel-accurate word wrap
    words = title.split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if draw.textbbox((0, 0), test, font=tf)[2] <= max_px:
            cur = test
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    lines = lines[:3]                     # max 3 lines

    line_h    = 68
    total_h   = len(lines) * line_h
    # Start title so its bottom sits 60px from canvas bottom
    title_top = H - 60 - total_h

    for i, line in enumerate(lines):
        y = title_top + i * line_h
        # thick drop shadow (draw 4 offsets)
        for ox, oy in [(2,2),(3,3),(-1,2),(2,-1)]:
            draw.text((PAD + ox, y + oy), line, font=tf, fill=SHADOW)
        draw.text((PAD, y), line, font=tf, fill=WHITE)

    # ── 5. HASHTAGS — one line directly below title ─────────────────────────────
    tag_y    = title_top + total_h + 6
    tag_font = fr(21)
    tags     = [h if h.startswith("#") else "#" + h for h in hashtags[:6]]
    tag_line = "   ".join(tags)
    tb       = draw.textbbox((0, 0), tag_line, font=tag_font)
    while tb[2] - tb[0] > max_px and tags:
        tags.pop()
        tag_line = "   ".join(tags)
        tb = draw.textbbox((0, 0), tag_line, font=tag_font)
    if tag_y + 28 < H:
        draw.text((PAD, tag_y), tag_line, font=tag_font, fill=YELLOW)

    # ── Save ───────────────────────────────────────────────────────────────────
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


# ═══════════════════════════════════════════════════════════
# HISTORY ROUTES
# ═══════════════════════════════════════════════════════════

@history_bp.route("/", methods=["GET"])
def list_history():
    category = request.args.get("category")
    limit    = int(request.args.get("limit", 20))
    posts    = get_history(limit=limit, category=category)
    return jsonify({"success": True, "data": posts})


@history_bp.route("/<blog_id>", methods=["GET"])
def get_post(blog_id):
    post = get_blog_by_id(blog_id)
    if not post:
        return jsonify({"success": False, "error": "Not found"}), 404
    return jsonify({"success": True, "data": post})


# ═══════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════

def _slugify(text: str) -> str:
    s = text.lower()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s.strip())
    return s[:80]
