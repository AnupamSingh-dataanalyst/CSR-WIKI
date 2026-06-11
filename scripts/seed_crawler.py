"""
seed_crawler.py
Crawls Wikipedia CSR/NGO categories + other Indian CSR sources
Extracts entity names and saves to SQLite for article generation.
Compatible: Python 3.7+
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
import time
import json
import re
import os
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "entities.db")

HEADERS = {
    "User-Agent": "CSRWikiBot/1.0 (educational reference site; contact: your@email.com)"
}

# ── Seed sources ──────────────────────────────────────────────────────────────

WIKIPEDIA_CATEGORIES = [
    "Corporate_social_responsibility_in_India",
    "Non-governmental_organizations_in_India",
    "Indian_company_law",
    "Charities_based_in_India",
    "Social_welfare_in_India",
]

WIKIPEDIA_ARTICLES = [
    ("Section 135 Companies Act 2013", "https://en.wikipedia.org/wiki/Corporate_social_responsibility_in_India"),
    ("FCRA 2010", "https://en.wikipedia.org/wiki/Foreign_Contribution_(Regulation)_Act,_2010"),
    ("80G Tax Exemption", "https://en.wikipedia.org/wiki/Income_tax_in_India"),
    ("Schedule VII Companies Act", "https://en.wikipedia.org/wiki/Companies_Act_2013"),
    ("NGO Darpan", "https://en.wikipedia.org/wiki/Niti_Aayog"),
    ("CSR-1 Form", "https://en.wikipedia.org/wiki/Ministry_of_Corporate_Affairs_(India)"),
]

# Predefined high-value entities — these always get generated
SEED_ENTITIES = [
    # Legal / Regulatory
    {"name": "Section 135 Companies Act 2013", "type": "regulation", "description": "Mandatory CSR provision for eligible companies in India"},
    {"name": "Schedule VII Companies Act 2013", "type": "regulation", "description": "List of activities eligible for CSR spending"},
    {"name": "CSR-1 Form", "type": "form", "description": "Registration form for NGOs to receive CSR funds"},
    {"name": "CSR-2 Form", "type": "form", "description": "Annual CSR report filed by companies with MCA"},
    {"name": "FCRA Registration", "type": "registration", "description": "Foreign Contribution Regulation Act registration for NGOs"},
    {"name": "12A Registration", "type": "registration", "description": "Income tax exemption registration for NGOs"},
    {"name": "80G Registration", "type": "registration", "description": "Donor tax deduction certificate for NGOs"},
    {"name": "DARPAN Registration", "type": "registration", "description": "NITI Aayog portal registration for NGOs"},
    {"name": "12AA Registration", "type": "registration", "description": "Permanent income tax exemption for charitable trusts"},
    {"name": "FCRA 2010 Compliance", "type": "compliance", "description": "Annual compliance requirements under Foreign Contribution Regulation Act"},
    # CSR Concepts
    {"name": "CSR Policy India", "type": "concept", "description": "Overview of India's mandatory CSR framework under Companies Act 2013"},
    {"name": "CSR Committee", "type": "concept", "description": "Board-level CSR committee required under Section 135"},
    {"name": "CSR Expenditure Calculation", "type": "concept", "description": "How to calculate 2% net profit obligation for CSR"},
    {"name": "Unspent CSR Amount", "type": "concept", "description": "Rules for unspent CSR funds — transfer to PM CARES or Scheduled VII funds"},
    {"name": "CSR Impact Assessment", "type": "concept", "description": "Mandatory third-party impact assessment for large CSR projects"},
    {"name": "CSR Implementing Agency", "type": "concept", "description": "NGOs and foundations that implement CSR projects on behalf of companies"},
    # Sectors under Schedule VII
    {"name": "Education CSR India", "type": "sector", "description": "CSR activities in education — schools, scholarships, digital literacy"},
    {"name": "Healthcare CSR India", "type": "sector", "description": "CSR activities in healthcare — hospitals, camps, medicines"},
    {"name": "Environment CSR India", "type": "sector", "description": "CSR activities in environment — afforestation, clean energy, waste management"},
    {"name": "Women Empowerment CSR", "type": "sector", "description": "CSR activities for women — SHGs, skill training, gender equality"},
    {"name": "Rural Development CSR", "type": "sector", "description": "CSR activities for rural areas — infrastructure, sanitation, livelihoods"},
    {"name": "Skill Development CSR", "type": "sector", "description": "CSR activities for vocational training and employment"},
    {"name": "Swachh Bharat CSR", "type": "scheme", "description": "Sanitation and cleanliness projects eligible under CSR"},
    {"name": "PM CARES Fund CSR", "type": "scheme", "description": "Prime Minister's Citizen Assistance fund — eligible CSR destination"},
    # Processes
    {"name": "CSR Proposal Writing India", "type": "guide", "description": "How to write a winning CSR grant proposal for Indian companies"},
    {"name": "CSR Due Diligence", "type": "guide", "description": "How companies evaluate NGOs before CSR partnership"},
    {"name": "CSR MOU Agreement", "type": "guide", "description": "Memorandum of understanding between NGO and CSR company"},
    {"name": "NGO Annual Report", "type": "guide", "description": "Components of a credible NGO annual report for CSR donors"},
    {"name": "CSR Utilization Certificate", "type": "guide", "description": "Document certifying proper use of CSR funds by implementing NGO"},
    # Top CSR Companies
    {"name": "Tata Group CSR", "type": "company", "description": "Tata Trusts and Tata group CSR programs and focus areas"},
    {"name": "Reliance Foundation CSR", "type": "company", "description": "Reliance Industries CSR through Reliance Foundation"},
    {"name": "Infosys Foundation CSR", "type": "company", "description": "Infosys CSR programs through Infosys Foundation"},
    {"name": "HDFC Bank CSR", "type": "company", "description": "HDFC Bank CSR initiatives — Parivartan program"},
    {"name": "Wipro CSR", "type": "company", "description": "Wipro's CSR focus areas — education, ecology, community"},
    {"name": "Mahindra CSR", "type": "company", "description": "Mahindra Group CSR through Mahindra Foundation"},
    {"name": "ITC CSR", "type": "company", "description": "ITC Limited CSR — e-Choupal, watershed, women empowerment"},
    {"name": "ONGC CSR", "type": "company", "description": "ONGC PSU CSR programs — one of India's top CSR spenders"},
    # State specific
    {"name": "Gujarat CSR Landscape", "type": "state", "description": "CSR programs and major donors active in Gujarat"},
    {"name": "Maharashtra CSR Landscape", "type": "state", "description": "CSR programs and major donors active in Maharashtra"},
    {"name": "Karnataka CSR Landscape", "type": "state", "description": "CSR programs and major donors active in Karnataka"},
    # Portals
    {"name": "MCA CSR Portal", "type": "portal", "description": "Ministry of Corporate Affairs portal for CSR filings and disclosures"},
    {"name": "CSR Box Platform", "type": "portal", "description": "Online platform connecting NGOs with CSR donors"},
    {"name": "GuideStar India", "type": "portal", "description": "NGO transparency and accountability platform"},
    {"name": "NGO Darpan Portal", "type": "portal", "description": "NITI Aayog's portal for NGO registration and government grants"},
]


# ── Database ──────────────────────────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            type TEXT,
            description TEXT,
            source TEXT,
            crawled_context TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()
    log.info("DB initialised at %s", DB_PATH)


def save_entity(name, etype, description, source, context=""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("""
            INSERT OR IGNORE INTO entities (name, type, description, source, crawled_context)
            VALUES (?, ?, ?, ?, ?)
        """, (name.strip(), etype, description.strip(), source, context[:2000]))
        conn.commit()
        if c.rowcount:
            log.info("  + Saved: %s [%s]", name, etype)
    except Exception as e:
        log.warning("Could not save %s: %s", name, e)
    finally:
        conn.close()


def get_pending_count():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM entities WHERE status='pending'")
    n = c.fetchone()[0]
    conn.close()
    return n


# ── Crawlers ──────────────────────────────────────────────────────────────────

def crawl_wikipedia_category(category_name):
    url = "https://en.wikipedia.org/wiki/Category:" + category_name
    log.info("Crawling Wikipedia category: %s", category_name)
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        # Article links inside the category
        for a in soup.select("#mw-pages a"):
            title = a.get_text(strip=True)
            if len(title) > 5 and not title.startswith("Category:"):
                save_entity(
                    name=title,
                    etype="wikipedia",
                    description="Wikipedia article on " + title,
                    source=url
                )
        time.sleep(2)
    except Exception as e:
        log.warning("Category crawl failed %s: %s", category_name, e)


def crawl_wikipedia_article(name, url):
    log.info("Crawling Wikipedia article: %s", name)
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        # First paragraph as context
        paras = soup.select("#mw-content-text p")
        context = ""
        for p in paras[:3]:
            text = p.get_text(strip=True)
            if len(text) > 80:
                context = text
                break
        # Internal links as sub-entities
        for a in soup.select("#mw-content-text a[href^='/wiki/']"):
            title = a.get_text(strip=True)
            href = a.get("href", "")
            if (len(title) > 5
                    and ":" not in href
                    and any(kw in title.lower() for kw in [
                        "csr", "ngo", "trust", "foundation", "grant",
                        "charity", "welfare", "fcra", "donation", "tax",
                        "corporate", "social", "india", "ministry", "fund"
                    ])):
                save_entity(
                    name=title,
                    etype="wikipedia_link",
                    description="Related concept: " + title,
                    source=url,
                    context=context
                )
        save_entity(name=name, etype="regulation", description=context[:200], source=url, context=context)
        time.sleep(2)
    except Exception as e:
        log.warning("Article crawl failed %s: %s", name, e)


def load_seed_entities():
    log.info("Loading %d predefined seed entities...", len(SEED_ENTITIES))
    for e in SEED_ENTITIES:
        save_entity(
            name=e["name"],
            etype=e["type"],
            description=e["description"],
            source="seed_list"
        )


# ── Main ──────────────────────────────────────────────────────────────────────

def run():
    init_db()

    # 1. Load hardcoded seed entities (always reliable)
    load_seed_entities()

    # 2. Crawl Wikipedia categories
    for cat in WIKIPEDIA_CATEGORIES:
        crawl_wikipedia_category(cat)
        time.sleep(1)

    # 3. Crawl specific Wikipedia articles for richer context
    for name, url in WIKIPEDIA_ARTICLES:
        crawl_wikipedia_article(name, url)
        time.sleep(1)

    pending = get_pending_count()
    log.info("Crawl complete. %d entities pending article generation.", pending)


if __name__ == "__main__":
    run()
