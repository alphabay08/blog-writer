# Blog Writer AI — Complete Step-by-Step Execution Guide

Everything you need from zero to live. Follow each phase in order.
Estimated total time: 45–60 minutes.

---

# PHASE 0 — What You Need to Sign Up For

All of these are **100% free**. No credit card required for any of them.

| Service | What it does | Sign up link |
|---------|-------------|-------------|
| GitHub | Stores your code | https://github.com |
| Render | Runs your Python backend | https://render.com |
| Netlify | Hosts your frontend website | https://netlify.com |
| OpenRouter | Provides AI models | https://openrouter.ai |
| Supabase | Your PostgreSQL database | https://supabase.com |

Sign up for all 5 before continuing. Use your Google account for all of them
— it's fastest and you won't need to verify emails separately.

---

# PHASE 1 — OpenRouter API Key

You said you already have this. Just make sure you have the key saved somewhere.
It looks like: `sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

If you need to find it again:
1. Go to https://openrouter.ai
2. Click your avatar (top right) → **Settings**
3. Click **API Keys**
4. Copy your key

✅ Done when you have your `sk-or-v1-...` key saved.

---

# PHASE 2 — Supabase (Database Setup)

**What is Supabase?**
Supabase is a free online database service. Think of it like Google Sheets —
but it's a proper database that your app can store and retrieve data from.
You don't need to know SQL deeply. You just run one script and it sets everything up.

## Step 2.1 — Create Your Supabase Account

1. Go to https://supabase.com
2. Click **Start your project** (green button)
3. Click **Sign in with GitHub** (easiest option)
4. Authorize Supabase to access GitHub when it asks

## Step 2.2 — Create a New Project

After signing in, you land on the dashboard.

1. Click **New project** (green button, top right)
2. Fill in the form:
   - **Organization**: it probably already shows your GitHub username — leave it
   - **Project name**: type `blog-writer`
   - **Database Password**: click **Generate a password** → save this password somewhere (you won't use it often but good to have)
   - **Region**: pick the one closest to you
     - If you're in India → Southeast Asia (Singapore) or South Asia (Mumbai)
     - If you're in US → US East or US West
     - If you're in Europe → EU West
3. Click **Create new project**

⏳ Wait about 60 seconds. Supabase is creating your database.
You'll see a loading screen with spinning icons. This is normal.

## Step 2.3 — Get Your API Keys

Once the project is ready, you'll land on the project dashboard.

1. In the left sidebar, click **Settings** (gear icon at the bottom)
2. Click **API** in the settings menu
3. You'll see two things you need:

```
Project URL:    https://abcdefghijkl.supabase.co
                ↑ Copy this entire URL

anon / public:  eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc...
                ↑ Copy this entire long string (it's very long, that's normal)
```

4. Save both of these. You'll need them in Phase 4.

## Step 2.4 — Create the Database Table

This is the most important Supabase step. You run a script that creates
the table where your blog posts will be stored.

1. In the left sidebar, click **SQL Editor** (looks like a database cylinder icon)
2. Click **New query** (top left, the + button)
3. You'll see an empty text editor
4. **Copy the entire SQL below** and paste it into that editor:

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

5. Click the green **Run** button (or press Ctrl+Enter / Cmd+Enter)
6. You should see: `Success. No rows returned`

That means the table was created successfully.

## Step 2.5 — Verify the Table Was Created

1. In the left sidebar, click **Table Editor** (looks like a grid/table icon)
2. You should see `blog_posts` in the list on the left
3. Click it — you'll see an empty table with all the column names across the top
4. It will be empty right now. That's correct.

✅ Supabase is ready. You have:
- `SUPABASE_URL` = `https://xxxx.supabase.co`
- `SUPABASE_ANON_KEY` = `eyJ...` (the long string)

---

# PHASE 3 — GitHub Setup

You need two separate GitHub repositories:
- One for the **backend** (Python/Flask code → deployed to Render)
- One for the **frontend** (HTML file → deployed to Netlify)

## Step 3.1 — Create Backend Repository

1. Go to https://github.com
2. Click the **+** icon (top right) → **New repository**
3. Fill in:
   - Repository name: `blog-writer-backend`
   - Description: `Blog Writer AI Backend`
   - Visibility: **Public** (required for free Render deployment)
   - ✅ Check **Add a README file**
4. Click **Create repository**

## Step 3.2 — Upload Backend Files

1. In your new repository, click **uploading an existing file** (link in the middle)
   OR click **Add file** → **Upload files**
2. Extract the `blog-FINAL-backend.zip` file on your computer
3. You'll see a folder called `bfinal_back` — open it
4. Select ALL the files and folders inside it (agents/, utils/, routes/, app.py, etc.)
5. Drag them all into the GitHub upload area
6. Wait for all files to upload (the progress bars will fill)
7. At the bottom, in "Commit changes":
   - Leave the default message "Add files via upload"
   - Click **Commit changes**

Your repository should now show all these files:
```
agents/
routes/
utils/
app.py
requirements.txt
render.yaml
README.md
GUIDE.md
```

## Step 3.3 — Create Frontend Repository

1. Click **+** → **New repository** again
2. Fill in:
   - Repository name: `blog-writer-frontend`
   - Visibility: **Public**
   - ✅ Check **Add a README file**
3. Click **Create repository**
4. Upload the files from `bfinal_front` folder (just `index.html` and `netlify.toml`)
5. Commit changes

✅ GitHub is ready. You have two repositories.

---

# PHASE 4 — Deploy Backend on Render

## Step 4.1 — Create Render Account

1. Go to https://render.com
2. Click **Get Started** → **Sign up with GitHub**
3. Authorize Render when it asks

## Step 4.2 — Create Web Service

1. On the Render dashboard, click **New +** (top right)
2. Click **Web Service**
3. Click **Connect a repository**
4. You'll see your GitHub repos listed → click **Connect** next to `blog-writer-backend`
5. Render reads your `render.yaml` automatically
6. On the next screen, confirm these settings:
   - **Name**: `blog-writer-backend` (or whatever you want)
   - **Region**: Choose closest to you
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --timeout 300 --workers 1 --threads 2`
   - **Plan**: Free
7. **DO NOT click Deploy yet** — first add environment variables below

## Step 4.3 — Add Environment Variables

Still on the same screen, scroll down to **Environment Variables**.

Click **Add Environment Variable** for each of these:

| Key | Value |
|-----|-------|
| `OPENROUTER_API_KEY` | `sk-or-v1-...` (your OpenRouter key) |
| `SUPABASE_URL` | `https://xxxx.supabase.co` (from Phase 2.3) |
| `SUPABASE_ANON_KEY` | `eyJ...` (the long key from Phase 2.3) |
| `FRONTEND_URL` | `*` (put asterisk for now, update after Phase 5) |

After adding all 4, click **Create Web Service**.

## Step 4.4 — Wait for Deployment

Render will now build and deploy your backend. This takes 3–5 minutes.

You'll see logs scrolling. Watch for:
```
Build successful 🎉
...
INFO  Starting gunicorn...
INFO  Listening at: http://0.0.0.0:XXXXX
```

## Step 4.5 — Copy Your Backend URL

Once deployed, at the top of the Render dashboard you'll see your URL:
```
https://blog-writer-backend-xxxx.onrender.com
```

Copy this URL. You need it in the next steps.

## Step 4.6 — Test the Backend

Open a new browser tab and visit:
```
https://blog-writer-backend-xxxx.onrender.com/health
```

You should see a JSON response like:
```json
{
  "status": "ok",
  "version": "3.1-free",
  "agents": 8,
  "models": ["nvidia/nemotron-3-nano-30b-a3b:free", ...]
}
```

If you see this — your backend is live. ✅

---

# PHASE 5 — Deploy Frontend on Netlify

## Step 5.1 — Edit the Backend URL in index.html

Before deploying, you need to tell the frontend where your backend lives.

**Option A — Edit on GitHub directly (easiest):**
1. Go to your `blog-writer-frontend` repository on GitHub
2. Click on `index.html`
3. Click the **pencil icon** (Edit this file) on the right
4. Press Ctrl+F (or Cmd+F) to open find
5. Search for: `YOUR_RENDER_BACKEND_URL`
6. Replace it with your actual Render URL:
   ```
   const API = "https://blog-writer-backend-xxxx.onrender.com";
   ```
7. Scroll down, click **Commit changes**

**Option B — Edit locally then re-upload:**
1. Open `index.html` in any text editor (Notepad, VS Code, etc.)
2. Find the line (near the bottom of the file, in the `<script>` section):
   ```javascript
   const API = "YOUR_RENDER_BACKEND_URL";
   ```
3. Replace it with your Render URL
4. Save the file, then re-upload to GitHub

## Step 5.2 — Deploy on Netlify

1. Go to https://netlify.com
2. Click **Add new site** → **Import an existing project**
3. Click **Deploy with GitHub**
4. Authorize Netlify when it asks
5. Find and select your `blog-writer-frontend` repository
6. On the next screen:
   - **Branch to deploy**: `main`
   - **Build command**: leave blank (empty)
   - **Publish directory**: `.` (just a dot)
7. Click **Deploy site**

Netlify deploys in about 30 seconds.

## Step 5.3 — Get Your Netlify URL

After deployment, Netlify gives you a URL like:
```
https://magical-name-123456.netlify.app
```

You can customize this: **Site settings** → **Domain management** → **Options** → **Edit site name**

## Step 5.4 — Update CORS on Render

Now that you have your Netlify URL, update the `FRONTEND_URL` on Render:

1. Go to Render dashboard → your service → **Environment**
2. Find `FRONTEND_URL`
3. Change the value from `*` to your Netlify URL:
   ```
   https://magical-name-123456.netlify.app
   ```
4. Click **Save Changes**
5. Render will automatically redeploy (takes 2-3 minutes)

✅ Frontend is live.

---

# PHASE 6 — Full End-to-End Test

Open your Netlify URL in a browser. Let's test everything works.

## Test 1 — Basic Connectivity

The page loads without errors. ✅

## Test 2 — Generate a Blog Post

1. Select a category: **AI / ML**
2. Select tone: **Casual**
3. Select length: **Short** (fastest for testing)
4. Add one keyword: type `artificial intelligence` + Enter
5. Leave "Your Own Topic" blank (let AI discover)
6. Leave "Your Name" blank for now
7. Click **✦ Discover Topic**

Watch the pipeline light up as agents run. Total time: 60–120 seconds.

## Test 3 — Verify All Outputs

After generation completes, check:
- ✅ Blog title appears
- ✅ Meta description shown
- ✅ Blog content visible (humanized writing)
- ✅ LinkedIn caption in the LinkedIn panel
- ✅ Hashtag chips clickable
- ✅ Header image displayed (or "Gemini generating..." if unavailable)
- ✅ Tweet thread in Social Content section
- ✅ **📋 Copy Caption + Tags** button works (paste in notepad to confirm)

## Test 4 — Download Test

Click **↓ Download Blog Image** — a PNG should download.
Click **↓ Download Header Image Only** — another PNG downloads.
Click **↓ TXT** — a text file downloads with full blog content.

## Test 5 — Check Supabase

1. Go to https://supabase.com → your project
2. Click **Table Editor** → **blog_posts**
3. You should see one row — your generated blog post
4. All columns should be filled in

✅ Everything is working.

---

# PHASE 7 — How to Post to LinkedIn Manually

This is your posting workflow going forward:

**Step 1:** Generate your blog post in the app

**Step 2:** Click **📋 Copy Caption + Tags** → caption + hashtags are copied to your clipboard

**Step 3:** Click **↓ Download Blog Image** → saves a PNG to your computer

**Step 4:** Go to https://linkedin.com → click the **Post** box at the top

**Step 5:** Paste (Ctrl+V) the caption. The description + hashtags appear.

**Step 6:** Click the **Image** icon in the LinkedIn post box → upload the PNG you downloaded

**Step 7:** Review the preview → click **Post**

Your LinkedIn post now has:
- Professional caption written by AI
- Relevant hashtags for reach
- A visual image that makes it stand out in the feed

---

# PHASE 8 — Keeping It Running (Important)

## Prevent Render Cold Starts

Render free tier "sleeps" your backend after 15 minutes of no activity.
The first request after sleeping takes 30-50 seconds. This is annoying.

Fix it for free with UptimeRobot:
1. Go to https://uptimerobot.com → Create free account
2. Click **Add New Monitor**
3. Monitor Type: **HTTP(s)**
4. Friendly Name: `Blog Writer Keep Alive`
5. URL: `https://your-render-url.onrender.com/health`
6. Monitoring Interval: **5 minutes**
7. Click **Create Monitor**

UptimeRobot pings your backend every 5 minutes. Render never sleeps. No more cold starts.

## Refresh Strategy

Your app is live. Here's what to check occasionally:
- **OpenRouter free models**: models are sometimes added/removed. Check https://openrouter.ai/models?q=free if you start seeing errors
- **Supabase**: check Table Editor occasionally to see your posts accumulating

---

# TROUBLESHOOTING

## "Failed to fetch" or CORS error
→ Check `FRONTEND_URL` in Render environment equals your exact Netlify URL
→ Redeploy Render after updating the env var

## "OPENROUTER_API_KEY not set" error
→ The env var wasn't saved on Render. Go to Environment tab, re-enter it, save.

## Blog generation hangs past 3 minutes
→ A free model may be overloaded. The app auto-retries with fallback models.
→ If it still fails, try again in a few minutes. Free tier models can get busy.

## Images show "no image available"
→ Gemini image generation on OpenRouter free tier has limited availability.
→ The blog still generates fully — image is optional. Try a different time of day.

## Supabase "permission denied" error
→ Go to Supabase → your table → click the lock icon → make sure anon role has insert+select access

## DOCX download fails
→ DOCX generation requires Node.js on Render. The first DOCX request installs the `docx` npm package which takes ~60 seconds. Subsequent requests are instant.

---

# QUICK REFERENCE — All Your URLs and Keys

Fill this in as you complete each phase:

```
OPENROUTER_API_KEY  = sk-or-v1-...
SUPABASE_URL        = https://__________.supabase.co
SUPABASE_ANON_KEY   = eyJ...
RENDER_BACKEND_URL  = https://blog-writer-backend-____.onrender.com
NETLIFY_URL         = https://______________.netlify.app
```

Keep this saved somewhere safe. You'll need these if you ever need to
redeploy or update the app.
