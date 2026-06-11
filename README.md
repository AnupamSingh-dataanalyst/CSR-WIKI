# CSR Grant Wiki India
**by iPgraam IPR & NGO Consultancy**

Auto-generated reference wiki for NGOs, grant writers, and CSR managers in India.
Covers CSR law, FCRA, 12A/80G registration, proposal writing, company profiles, and more.

---

## How It Works

```
seed_crawler.py  →  entities.db  →  generate_articles.py  →  docs/articles/*.md
                                                                      ↓
                                                            build_site.py
                                                                      ↓
                                                            docs/index.html + articles/*.html
                                                                      ↓
                                                            GitHub Pages (auto-deploy)
```

**Runs automatically every Sunday at 7:30 AM IST via GitHub Actions.**

---

## Setup (One Time)

### 1. Fork / clone this repo

```bash
git clone https://github.com/YOUR_USERNAME/csr-wiki.git
cd csr-wiki
```

### 2. Add GROQ_API_KEY secret

- Go to repo **Settings → Secrets and variables → Actions**
- Click **New repository secret**
- Name: `GROQ_API_KEY`
- Value: your Groq API key from console.groq.com

### 3. Enable GitHub Pages

- Go to repo **Settings → Pages**
- Source: **Deploy from a branch**
- Branch: `gh-pages` / `/ (root)`
- Save

### 4. Update your contact details in build_site.py

```python
CTA_WHATSAPP = "https://wa.me/91XXXXXXXXXX"   # your WhatsApp number
CTA_EMAIL    = "mailto:info@ipgraam.com"        # your email
```

### 5. Trigger first run manually

- Go to **Actions → CSR Wiki — Crawl, Generate & Deploy**
- Click **Run workflow**
- Set max_articles to `50` for first run
- Watch it build!

---

## Manual Local Run (optional)

```bash
pip install -r requirements.txt
export GROQ_API_KEY="your_key_here"

python scripts/seed_crawler.py      # Crawl & populate entities.db
python scripts/generate_articles.py # Generate markdown articles
python scripts/build_site.py        # Build HTML site into docs/
```

Open `docs/index.html` in browser to preview.

---

## Repo Structure

```
csr-wiki/
├── .github/
│   └── workflows/
│       └── deploy.yml          ← GitHub Actions pipeline
├── scripts/
│   ├── seed_crawler.py         ← Crawls Wikipedia + seed list → entities.db
│   ├── generate_articles.py    ← Groq LLM → markdown articles
│   └── build_site.py           ← Markdown → static HTML site
├── docs/
│   ├── index.html              ← Generated homepage (GitHub Pages root)
│   ├── .nojekyll               ← Tells GitHub not to process with Jekyll
│   └── articles/               ← Generated article HTML pages
├── entities.db                 ← SQLite (gitignored, cached in Actions)
├── requirements.txt
└── README.md
```

---

## Adding More Seed Sources

Edit `seed_crawler.py`:

- Add URLs to `WIKIPEDIA_CATEGORIES` or `WIKIPEDIA_ARTICLES`
- Add entries to `SEED_ENTITIES` list directly
- The crawler deduplicates via SQLite `INSERT OR IGNORE`

---

## License

Content generated for reference purposes. Verify with official MCA, MHA, and IT department sources before acting on any information.

Built with ❤️ by iPgraam IPR & NGO Consultancy, Ahmedabad.
