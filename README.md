# Blog Writer AI

A multi-agent AI blog writing system that generates humanized, SEO-optimized blog posts using 7 specialist AI models — all completely free via OpenRouter.

---

## What It Does

1. **Discovers** a compelling topic in your chosen category (or accepts your own topic)
2. **Generates** 3 title options with full SEO structure
3. **Researches** the topic with a 405B parameter model
4. **Writes** the full blog post in your chosen tone and length
5. **Humanizes** the content to pass AI detectors (GPTZero, Originality.ai, etc.)
6. **Creates** a LinkedIn caption + hashtags ready to copy-paste
7. **Generates** a watermark-free header image
8. Saves everything to your Supabase database

Output: Blog post + header image + LinkedIn caption + tweet thread + .DOCX download + blog image PNG for LinkedIn

---

## Tech Stack

| Layer | Service | Cost |
|-------|---------|------|
| Backend | Render (Python/Flask) | Free |
| Frontend | Netlify (Static HTML) | Free |
| AI Models | OpenRouter | Free |
| Database | Supabase (PostgreSQL) | Free |
| Images | Gemini via OpenRouter | Free |

**Total running cost: $0**

---

## Agent Pipeline

```
User Input
    │
    ▼
Agent 1 ── nvidia/nemotron-3-nano-30b-a3b:free
           Topic discovery from category patterns
    │
    ▼
Agent 2 ── arcee-ai/trinity-large-preview:free  (400B MoE)
           SEO structure + 3 title options + meta description
    │
    ▼
Agent 3 ── nousresearch/hermes-3-llama-3.1-405b:free  (405B)
           Deep per-section research and fact gathering
    │
    ▼
Agent 4 ── arcee-ai/trinity-large-preview:free  (400B MoE)
           Human-quality prose writing with tone + SEO
    │
    ▼
Agent 5 ── mistralai/mistral-small-3.1-24b-instruct:free
           AI-detector bypass humanization (GPTZero, Originality.ai)
    │
    ▼
Agent 6 ── meta-llama/llama-3.3-70b-instruct:free
           Tweet thread + LinkedIn caption + hashtags
    │
    ▼
Agent 7 ── google/gemini-2.5-flash-preview:free
           Watermark-free header image generation
    │
    ▼
Supabase ── Save post, research, caption, image flag
```

---

## Project Structure

```
blog-writer-backend/
│
├── app.py                      # Flask app entry point
├── requirements.txt            # Python dependencies
├── render.yaml                 # Render deploy config
├── README.md                   # This file
│
├── agents/
│   ├── agent1_discover.py      # Topic discovery (Nemotron)
│   ├── agent2_structure.py     # SEO structure + titles (Trinity)
│   ├── agent3_research.py      # Deep research (Hermes 405B)
│   ├── agent4_writer.py        # Blog writer (Trinity)
│   ├── agent5_humanizer.py     # AI-bypass humanizer (Mistral)
│   ├── agent6_social.py        # Social content (Llama 70B)
│   └── agent7_image.py         # Image generation (Gemini)
│
├── routes/
│   └── routes.py               # All API endpoints
│
└── utils/
    ├── openrouter.py            # OpenRouter client + model registry
    ├── db.py                    # Supabase database operations
    └── docx_gen.py              # Word document generator
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/blog/discover` | Agent 1: discover or enrich topic |
| POST | `/api/blog/titles` | Agent 2: structure + 3 title options |
| POST | `/api/blog/generate` | Agents 3-7: full generation pipeline |
| POST | `/api/blog/download/txt` | Download as .txt file |
| POST | `/api/blog/download/docx` | Download as .docx file |
| POST | `/api/blog/download/blogimg` | Download blog as styled PNG |
| GET | `/api/history/` | List past blog posts |
| GET | `/api/history/<id>` | Get single blog post |
| GET | `/health` | Health check + model list |

---

## Environment Variables

Set these in Render dashboard → Environment tab:

| Variable | Where to get it |
|----------|----------------|
| `OPENROUTER_API_KEY` | https://openrouter.ai → Settings → API Keys |
| `SUPABASE_URL` | Supabase project → Settings → API → Project URL |
| `SUPABASE_ANON_KEY` | Supabase project → Settings → API → anon/public key |
| `FRONTEND_URL` | Your Netlify URL, e.g. `https://yoursite.netlify.app` |

---

## Supabase Table Schema

Run this SQL once in Supabase → SQL Editor → New Query:

```sql
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
```

---

## Local Development

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/blog-writer-backend.git
cd blog-writer-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENROUTER_API_KEY="sk-or-v1-..."
export SUPABASE_URL="https://xxxx.supabase.co"
export SUPABASE_ANON_KEY="eyJ..."
export FRONTEND_URL="http://localhost:8080"

# Run
python app.py

# Test health endpoint
curl http://localhost:5000/health
```

---

## Deployment

See `GUIDE.md` for full step-by-step deployment instructions including:
- Setting up all accounts (Render, Netlify, Supabase, OpenRouter)
- Detailed Supabase walkthrough with screenshots description
- Connecting frontend to backend
- Testing the full pipeline

---

## Rate Limits (Free OpenRouter Tier)

- 20 requests per minute per model
- 200 requests per day total
- Each blog post uses ~8-10 API calls
- **Daily capacity: ~20-25 blog posts for free**

The system auto-falls back to secondary models if a primary model is rate-limited.

---

## License

MIT — use freely, modify as needed.
