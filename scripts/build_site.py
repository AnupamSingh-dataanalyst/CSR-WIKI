"""
build_site.py
Reads markdown articles from docs/articles/
Generates index.html + per-article HTML pages → docs/
Compatible: Python 3.7+
Requires: pip install markdown
"""

import os
import re
import glob
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

try:
    import markdown
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False
    log.warning("markdown not installed. Run: pip install markdown")

ARTICLES_DIR = os.path.join(os.path.dirname(__file__), "..", "docs", "articles")
DOCS_DIR     = os.path.join(os.path.dirname(__file__), "..", "docs")

SITE_TITLE   = "CSR Grant Wiki India"
SITE_TAGLINE = "Free reference for NGOs, grant writers & CSR managers"
BRAND_COLOR  = "#1a4a6b"   # deep navy
ACCENT       = "#c8962e"   # gold
CTA_WHATSAPP = "https://wa.me/919898186715"  # replace with your number
CTA_EMAIL    = "mailto:ipgraam@gmail.com"

CATEGORIES = {
    "regulation": "Laws & Regulations",
    "form":       "Forms & Filings",
    "concept":    "CSR Concepts",
    "guide":      "How-To Guides",
    "sector":     "CSR Sectors",
    "company":    "Company Profiles",
    "scheme":     "Government Schemes",
    "state":      "State Guides",
    "portal":     "Portals & Platforms",
    "registration": "Registrations",
    "compliance": "Compliance",
    "wikipedia":  "Reference",
    "wikipedia_link": "Reference",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def parse_frontmatter(text):
    meta = {"title": "", "category": "", "slug": ""}
    if not text.startswith("---"):
        return meta, text
    end = text.find("---", 3)
    if end == -1:
        return meta, text
    fm_block = text[3:end].strip()
    body     = text[end+3:].strip()
    for line in fm_block.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"').strip("'")
    return meta, body


def slugify(name):
    slug = name.lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug.strip())
    return re.sub(r"-+", "-", slug)[:80]


def md_to_html(text):
    if HAS_MARKDOWN:
        return markdown.markdown(text, extensions=["tables", "fenced_code"])
    # Minimal fallback
    lines = []
    for line in text.splitlines():
        if line.startswith("## "):
            lines.append("<h2>{}</h2>".format(line[3:]))
        elif line.startswith("# "):
            lines.append("<h1>{}</h1>".format(line[2:]))
        elif line.startswith("- "):
            lines.append("<li>{}</li>".format(line[2:]))
        elif line.strip() == "":
            lines.append("<br>")
        else:
            lines.append("<p>{}</p>".format(line))
    return "\n".join(lines)


# ── HTML templates ────────────────────────────────────────────────────────────

def base_style():
    return """
    <style>
      :root {{ --brand:{brand}; --accent:{accent}; }}
      * {{ box-sizing:border-box; margin:0; padding:0; }}
      body {{ font-family:'Segoe UI',Arial,sans-serif; color:#222; background:#f7f8fa; }}
      header {{ background:var(--brand); color:#fff; padding:1rem 2rem; display:flex; align-items:center; justify-content:space-between; }}
      header a {{ color:#fff; text-decoration:none; font-size:1.3rem; font-weight:700; }}
      header .tagline {{ font-size:.85rem; opacity:.8; }}
      nav {{ background:#fff; border-bottom:2px solid var(--accent); padding:.5rem 2rem; }}
      nav a {{ color:var(--brand); text-decoration:none; margin-right:1.2rem; font-size:.9rem; }}
      nav a:hover {{ text-decoration:underline; }}
      .container {{ max-width:960px; margin:2rem auto; padding:0 1rem; }}
      .cta-box {{ background:var(--accent); color:#fff; border-radius:8px; padding:1.2rem 1.5rem; margin:2rem 0; }}
      .cta-box a {{ color:#fff; font-weight:700; }}
      footer {{ background:var(--brand); color:#aac; text-align:center; padding:1rem; margin-top:3rem; font-size:.8rem; }}
      .badge {{ display:inline-block; background:#e8f0fe; color:var(--brand); border-radius:4px; padding:.2rem .6rem; font-size:.75rem; margin-bottom:.5rem; }}
      article h1 {{ color:var(--brand); margin-bottom:.5rem; }}
      article h2 {{ color:var(--brand); margin:1.5rem 0 .5rem; border-left:3px solid var(--accent); padding-left:.6rem; }}
      article p  {{ line-height:1.7; margin:.6rem 0; }}
      article ul {{ margin:.5rem 0 .5rem 1.5rem; line-height:1.7; }}
      article li {{ margin:.3rem 0; }}
      .card-grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(240px,1fr)); gap:1rem; margin:1.5rem 0; }}
      .card {{ background:#fff; border-radius:8px; padding:1rem; box-shadow:0 1px 4px rgba(0,0,0,.08); text-decoration:none; color:#222; display:block; border-top:3px solid var(--accent); }}
      .card:hover {{ box-shadow:0 3px 10px rgba(0,0,0,.15); }}
      .card h3 {{ font-size:.95rem; color:var(--brand); margin-bottom:.3rem; }}
      .card p  {{ font-size:.8rem; color:#555; line-height:1.4; }}
      .search-box {{ width:100%; padding:.7rem 1rem; font-size:1rem; border:2px solid var(--brand); border-radius:6px; margin:1rem 0; }}
      h2.section-head {{ color:var(--brand); border-bottom:2px solid var(--accent); padding-bottom:.3rem; margin:2rem 0 1rem; }}
    </style>
    """.format(brand=BRAND_COLOR, accent=ACCENT)


def nav_html():
    return """
    <nav>
      <a href="/CSR-WIKI/">Home</a>
      <a href="/CSR-WIKI/articles/">All Articles</a>
      <a href="/CSR-WIKI/categories.html">Categories</a>
      <a href="{cta}">📞 Get Consultancy</a>
    </nav>
    """.format(cta=CTA_WHATSAPP)


def header_html():
    return """
    <header>
      <div>
        <a href="/CSR-WIKI/">CSR Grant Wiki India</a>
        <div class="tagline">by iPgraam IPR &amp; NGO Consultancy</div>
      </div>
      <div style="font-size:.85rem;opacity:.8;">{date}</div>
    </header>
    """.format(date=datetime.now().strftime("%B %Y"))


def footer_html():
    return """
    <footer>
      &copy; {year} iPgraam IPR &amp; NGO Consultancy &nbsp;|&nbsp;
      <a href="{email}" style="color:#aac;">Contact Us</a> &nbsp;|&nbsp;
      Auto-generated reference wiki. Verify with official sources.
    </footer>
    """.format(year=datetime.now().year, email=CTA_EMAIL)


def cta_box():
    return """
    <div class="cta-box">
      💼 <strong>Need expert help with CSR grants or NGO compliance?</strong>
      &nbsp;<a href="{wa}">WhatsApp iPgraam</a> &nbsp;or&nbsp;
      <a href="{em}">Email Us</a> — free initial consultation.
    </div>
    """.format(wa=CTA_WHATSAPP, em=CTA_EMAIL)


# ── Page builders ─────────────────────────────────────────────────────────────

def build_article_page(meta, body_html, slug):
    cat_label = CATEGORIES.get(meta.get("category", ""), "Reference")
    html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{title} | {site}</title>
  <meta name="description" content="India CSR wiki: {title} — practical reference for NGOs and grant writers.">
  {style}
</head>
<body>
{header}
{nav}
<div class="container">
  <span class="badge">{cat}</span>
  <article>
    {body}
  </article>
  {cta}
  <p><a href="/CSR-WIKI/">&larr; Back to Home</a></p>
</div>
{footer}
</body>
</html>""".format(
        title=meta.get("title", "Article"),
        site=SITE_TITLE,
        style=base_style(),
        header=header_html(),
        nav=nav_html(),
        cat=cat_label,
        body=body_html,
        cta=cta_box(),
        footer=footer_html()
    )
    return html


def build_index(articles):
    # Group by category
    by_cat = {}
    for a in articles:
        cat = a.get("category", "reference")
        by_cat.setdefault(cat, []).append(a)

    cards_html = ""
    for cat, items in sorted(by_cat.items()):
        label = CATEGORIES.get(cat, cat.title())
        cards_html += '<h2 class="section-head">{}</h2>\n<div class="card-grid">\n'.format(label)
        for a in sorted(items, key=lambda x: x["title"]):
            cards_html += """<a href="/CSR-WIKI/articles/{slug}.html" class="card">
  <h3>{title}</h3>
  <p>{desc}</p>
</a>\n""".format(slug=a["slug"], title=a["title"], desc=a.get("description", "")[:80])
        cards_html += "</div>\n"

    html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{site} | {tagline}</title>
  <meta name="description" content="Free reference wiki for CSR grants, NGO compliance, FCRA, 12A, 80G, Schedule VII and more.">
  {style}
</head>
<body>
{header}
{nav}
<div class="container">
  <h1 style="color:var(--brand);margin:1rem 0 .3rem">{site}</h1>
  <p style="color:#555;margin-bottom:1rem">{tagline} — {count} articles</p>
  <input class="search-box" type="text" id="search" placeholder="Search articles... e.g. FCRA, 80G, CSR proposal">
  {cta}
  <div id="content">
    {cards}
  </div>
</div>
{footer}
<script>
  var cards = document.querySelectorAll('.card');
  document.getElementById('search').addEventListener('input', function() {{
    var q = this.value.toLowerCase();
    cards.forEach(function(c) {{
      c.style.display = c.textContent.toLowerCase().includes(q) ? '' : 'none';
    }});
  }});
</script>
</body>
</html>""".format(
        site=SITE_TITLE,
        tagline=SITE_TAGLINE,
        count=len(articles),
        style=base_style(),
        header=header_html(),
        nav=nav_html(),
        cta=cta_box(),
        cards=cards_html,
        footer=footer_html()
    )
    return html


# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    md_files = glob.glob(os.path.join(ARTICLES_DIR, "*.md"))
    log.info("Found %d markdown articles", len(md_files))

    articles_meta = []
    article_html_dir = os.path.join(DOCS_DIR, "articles")
    os.makedirs(article_html_dir, exist_ok=True)

    for md_path in md_files:
        with open(md_path, encoding="utf-8") as f:
            raw = f.read()

        meta, body = parse_frontmatter(raw)
        if not meta.get("title"):
            meta["title"] = os.path.basename(md_path).replace(".md", "").replace("-", " ").title()
        if not meta.get("slug"):
            meta["slug"] = slugify(meta["title"])

        body_html = md_to_html(body)
        page_html = build_article_page(meta, body_html, meta["slug"])

        out_path = os.path.join(article_html_dir, meta["slug"] + ".html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(page_html)

        # First para as description
        first_para = re.sub(r"<[^>]+>", "", body_html)
        first_para = " ".join(first_para.split())[:120]
        meta["description"] = first_para

        articles_meta.append(meta)
        log.info("  Built: %s.html", meta["slug"])

    # Build index
    index_html = build_index(articles_meta)
    with open(os.path.join(DOCS_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)
    log.info("index.html written with %d articles", len(articles_meta))

    # Write Jekyll bypass
    nojekyll = os.path.join(DOCS_DIR, ".nojekyll")
    if not os.path.exists(nojekyll):
        open(nojekyll, "w").close()


if __name__ == "__main__":
    run()
