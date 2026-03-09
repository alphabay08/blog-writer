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
from agents.agent7_image     import agent_generate_image
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

        # Agent 7: Image (via OpenRouter Nano Banana — no extra key needed)
        image_b64 = agent_generate_image(chosen_title, topic, tone, category)

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


def _render_blog_png(title, content, meta, category, hashtags, image_b64):
    """Render blog as styled PNG using Pillow (no Chrome needed)."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        import textwrap
    except ImportError:
        raise RuntimeError("Pillow not installed. Add 'Pillow' to requirements.txt")

    W, H = 1200, 1600
    BG       = (10, 10, 18)
    ACCENT   = (124, 106, 247)
    WHITE    = (232, 232, 240)
    MUTED    = (100, 100, 120)
    GOLD     = (247, 200, 106)

    img  = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Try to load fonts, fall back gracefully
    def fnt(size):
        try:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
        except Exception:
            return ImageFont.load_default()
    def fnt_reg(size):
        try:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
        except Exception:
            return ImageFont.load_default()

    y = 0

    # Header image strip
    if image_b64:
        try:
            img_data = base64.b64decode(image_b64)
            header_img = Image.open(io.BytesIO(img_data)).convert("RGB")
            header_img = header_img.resize((W, 380))
            img.paste(header_img, (0, 0))
            y = 380
        except Exception:
            y = 0
    
    # Accent bar
    draw.rectangle([0, y, W, y + 4], fill=ACCENT)
    y += 4

    # Category pill
    y += 28
    cat_text = (category or "blog").upper()
    draw.rectangle([60, y, 60 + len(cat_text)*11 + 24, y + 32], fill=ACCENT)
    draw.text((72, y + 6), cat_text, font=fnt(14), fill=(255, 255, 255))
    y += 52

    # Title
    title_lines = textwrap.wrap(title, width=38)
    for line in title_lines[:3]:
        draw.text((60, y), line, font=fnt(42), fill=WHITE)
        y += 54
    y += 12

    # Meta description
    for line in textwrap.wrap(meta, width=72)[:2]:
        draw.text((60, y), line, font=fnt_reg(20), fill=MUTED)
        y += 28
    y += 28

    # Divider
    draw.rectangle([60, y, W - 60, y + 1], fill=(40, 40, 58))
    y += 24

    # Blog content preview
    plain = content.replace("## ", "\n").replace("**", "")
    words = plain.split()[:180]
    preview = " ".join(words) + ("..." if len(plain.split()) > 180 else "")
    for line in textwrap.wrap(preview, width=68)[:18]:
        draw.text((60, y), line, font=fnt_reg(22), fill=(180, 180, 200))
        y += 30
    y += 20

    # Divider
    draw.rectangle([60, y, W - 60, y + 1], fill=(40, 40, 58))
    y += 28

    # Hashtags
    tag_text = "  ".join(hashtags[:7]) if hashtags else ""
    for line in textwrap.wrap(tag_text, width=70):
        draw.text((60, y), line, font=fnt_reg(20), fill=ACCENT)
        y += 28
    y += 16

    # Footer branding strip
    draw.rectangle([0, H - 48, W, H], fill=(20, 20, 32))
    draw.text((60, H - 34), "Blog Writer AI  ·  Generated with OpenRouter Free Models", 
              font=fnt_reg(16), fill=MUTED)

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
