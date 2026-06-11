"""
generate_articles.py
Reads pending entities from SQLite, generates wiki articles via Groq API,
saves markdown files to docs/articles/
Compatible: Python 3.7+
"""

import os
import re
import time
import sqlite3
import logging
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

DB_PATH       = os.path.join(os.path.dirname(__file__), "..", "entities.db")
ARTICLES_DIR  = os.path.join(os.path.dirname(__file__), "..", "docs", "articles")
GROQ_API_KEY  = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL    = "llama-3.3-70b-versatile"
GROQ_URL      = "https://api.groq.com/openai/v1/chat/completions"
MAX_PER_RUN   = int(os.environ.get("MAX_ARTICLES_PER_RUN", "30"))

os.makedirs(ARTICLES_DIR, exist_ok=True)


# ── Prompt ────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert Indian NGO consultant and CSR law specialist.
Write clear, accurate, practical wiki reference articles for NGO professionals,
grant writers, and CSR managers in India.

Rules:
- Write in plain English, accessible to non-lawyers
- Focus on practical, actionable information
- Always mention relevant Indian laws, forms, and portals by name
- Include specific steps, timelines, or amounts wherever applicable
- Do NOT use placeholder text like [insert here] — write real content
- Do NOT add disclaimers like "consult a lawyer" — this is a reference wiki
- Length: 400-600 words per article
- Format: valid Markdown with ## subheadings, bullet points where helpful
"""

ARTICLE_TEMPLATE = """Write a wiki reference article on: **{name}**

Category: {etype}
Brief: {description}
Additional context: {context}

Structure the article with:
1. A 2-3 sentence intro explaining what this is
2. ## Key Details  (specifics — numbers, dates, thresholds, forms)
3. ## Who Needs This  (which NGOs / companies this applies to)
4. ## Step-by-Step Process  (if applicable)
5. ## Important Deadlines / Penalties  (if applicable)
6. ## Related Topics  (3-5 related concepts as bullet links)

Return only the article markdown. Start directly with the article title as # heading.
"""


# ── Groq call ─────────────────────────────────────────────────────────────────

def call_groq(prompt):
    headers = {
        "Authorization": "Bearer " + GROQ_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": prompt}
        ],
        "temperature": 0.4,
        "max_tokens": 1024
    }
    r = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()


# ── Helpers ───────────────────────────────────────────────────────────────────

def slugify(name):
    slug = name.lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug.strip())
    slug = re.sub(r"-+", "-", slug)
    return slug[:80]


def article_exists(name):
    path = os.path.join(ARTICLES_DIR, slugify(name) + ".md")
    return os.path.exists(path)


def save_article(name, content):
    slug = slugify(name)
    path = os.path.join(ARTICLES_DIR, slug + ".md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    log.info("  Saved: %s.md", slug)
    return slug


def mark_done(entity_id):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE entities SET status='done' WHERE id=?", (entity_id,))
    conn.commit()
    conn.close()


def mark_failed(entity_id):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE entities SET status='failed' WHERE id=?", (entity_id,))
    conn.commit()
    conn.close()


def get_pending_entities():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT id, name, type, description, crawled_context
        FROM entities
        WHERE status='pending'
        ORDER BY
            CASE type
                WHEN 'regulation' THEN 1
                WHEN 'form'       THEN 2
                WHEN 'concept'    THEN 3
                WHEN 'guide'      THEN 4
                WHEN 'sector'     THEN 5
                WHEN 'company'    THEN 6
                WHEN 'scheme'     THEN 7
                WHEN 'state'      THEN 8
                ELSE 9
            END,
            id
        LIMIT ?
    """, (MAX_PER_RUN,))
    rows = c.fetchall()
    conn.close()
    return rows


# ── Front matter ──────────────────────────────────────────────────────────────

def wrap_frontmatter(name, etype, slug, content):
    fm = "---\n"
    fm += 'title: "{}"\n'.format(name.replace('"', "'"))
    fm += 'category: "{}"\n'.format(etype)
    fm += 'slug: "{}"\n'.format(slug)
    fm += 'layout: article\n'
    fm += "---\n\n"
    return fm + content


# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    if not GROQ_API_KEY:
        log.error("GROQ_API_KEY not set. Aborting.")
        raise SystemExit(1)

    entities = get_pending_entities()
    log.info("Found %d pending entities (max %d per run)", len(entities), MAX_PER_RUN)

    generated = 0
    skipped   = 0

    for eid, name, etype, description, context in entities:
        if article_exists(name):
            log.info("  Skip (exists): %s", name)
            mark_done(eid)
            skipped += 1
            continue

        log.info("Generating: %s [%s]", name, etype)
        prompt = ARTICLE_TEMPLATE.format(
            name=name,
            etype=etype,
            description=description or "",
            context=(context or "")[:500]
        )

        try:
            content = call_groq(prompt)
            slug    = save_article(name, wrap_frontmatter(name, etype, slugify(name), content))
            mark_done(eid)
            generated += 1
            time.sleep(1.2)   # Groq rate limit buffer
        except Exception as e:
            log.warning("Failed %s: %s", name, e)
            mark_failed(eid)
            time.sleep(3)

    log.info("Done. Generated: %d | Skipped: %d", generated, skipped)


if __name__ == "__main__":
    run()
