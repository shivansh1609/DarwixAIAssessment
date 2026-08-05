"""
Web Scraper for TalentBridge Recruitment Content
=================================================
Extracts content from website pages and PDFs for the knowledge base.

Approach:
- Sitemap/page discovery via robots.txt and manual URL list
- BeautifulSoup for HTML parsing, pdfplumber for PDFs
- Navigation, headers, footers, and boilerplate stripped
- Raw content saved as JSON with metadata for downstream processing

Usage:
    python scraper.py --url https://example.com --output data/raw/
    python scraper.py --urls urls.txt --output data/raw/
    python scraper.py --demo  # Use pre-built demo data
"""

import json
import os
import re
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict

# Optional imports — graceful fallback if not installed
try:
    import requests
    from bs4 import BeautifulSoup
    HAS_WEB = True
except ImportError:
    HAS_WEB = False

try:
    import pdfplumber
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class ScrapedPage:
    """Represents a single scraped page or document."""
    source_url: str
    source_type: str  # website, pdf, internal_document
    page_title: str
    extraction_date: str
    raw_html_stripped: str
    content_hash: str = ""
    extraction_status: str = "success"
    extraction_error: Optional[str] = None

    def __post_init__(self):
        if not self.content_hash:
            self.content_hash = hashlib.md5(self.raw_html_stripped.encode()).hexdigest()


# ─── Boilerplate patterns to remove ────────────────────────────────────────
BOILERPLATE_PATTERNS = [
    r"Skip to content.*?\n",
    r"Cookie Notice:.*?\n",
    r"©\s*\d{4}.*?\n",
    r"Follow us:.*?\n",
    r"Footer:.*?\n",
    r"Navigation:.*?\n",
    r"Social:.*?\n",
    r"Related Jobs:.*?\n",
    r"Similar Roles:.*?\n",
    r"Accept \| Decline\n?",
    r"\| Privacy Policy \| Terms of Service",
    r"Share this job",
]

NAV_KEYWORDS = [
    "skip to content", "cookie notice", "accept | decline",
    "follow us:", "footer:", "social:", "privacy policy",
    "terms of service", "© 2026", "© 2025",
]


def strip_boilerplate(text: str) -> str:
    """Remove navigation, footer, cookie banners, and other boilerplate."""
    for pattern in BOILERPLATE_PATTERNS:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        lower = line.strip().lower()
        if any(kw in lower for kw in NAV_KEYWORDS):
            continue
        if lower in ("", "home", "about", "careers", "contact", "login"):
            continue
        # Skip lines that are just nav links (e.g., "Home | About | Careers")
        if re.match(r"^(\w+\s*\|\s*)+\w+$", line.strip()) and len(line.strip()) < 80:
            continue
        cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()


def scrape_url(url: str, timeout: int = 30) -> Optional[ScrapedPage]:
    """Scrape a single URL and extract main content."""
    if not HAS_WEB:
        logger.error("requests/beautifulsoup4 not installed. Run: pip install requests beautifulsoup4")
        return None

    try:
        headers = {"User-Agent": "TalentBridge-KB-Scraper/1.0"}
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove script, style, nav, footer, header elements
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
            tag.decompose()

        # Try to find main content area
        main = soup.find("main") or soup.find("article") or soup.find("div", {"class": "content"})
        if main:
            text = main.get_text(separator="\n", strip=True)
        else:
            text = soup.get_text(separator="\n", strip=True)

        title = soup.title.string if soup.title else url
        text = strip_boilerplate(text)

        return ScrapedPage(
            source_url=url,
            source_type="website",
            page_title=title.strip(),
            extraction_date=datetime.now().strftime("%Y-%m-%d"),
            raw_html_stripped=text,
        )

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to scrape {url}: {e}")
        return ScrapedPage(
            source_url=url,
            source_type="website",
            page_title="",
            extraction_date=datetime.now().strftime("%Y-%m-%d"),
            raw_html_stripped="",
            extraction_status="failed",
            extraction_error=str(e),
        )


def parse_pdf(filepath: str) -> Optional[ScrapedPage]:
    """Extract text from a PDF file preserving tables where possible."""
    if not HAS_PDF:
        logger.error("pdfplumber not installed. Run: pip install pdfplumber")
        return None

    try:
        text_parts = []
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                # Try to extract tables first
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        for row in table:
                            cleaned_row = [str(cell).strip() if cell else "" for cell in row]
                            text_parts.append(" | ".join(cleaned_row))
                        text_parts.append("")  # blank line after table

                # Extract remaining text
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

        full_text = "\n".join(text_parts)
        return ScrapedPage(
            source_url=f"file://{filepath}",
            source_type="pdf",
            page_title=Path(filepath).stem,
            extraction_date=datetime.now().strftime("%Y-%m-%d"),
            raw_html_stripped=strip_boilerplate(full_text),
        )

    except Exception as e:
        logger.error(f"Failed to parse PDF {filepath}: {e}")
        return ScrapedPage(
            source_url=f"file://{filepath}",
            source_type="pdf",
            page_title=Path(filepath).stem,
            extraction_date=datetime.now().strftime("%Y-%m-%d"),
            raw_html_stripped="",
            extraction_status="failed",
            extraction_error=str(e),
        )


def load_demo_data(raw_dir: str = None) -> list[dict]:
    """Load pre-built demo data from scraped_pages.json."""
    if raw_dir is None:
        raw_dir = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
    filepath = os.path.join(raw_dir, "scraped_pages.json")
    logger.info(f"Loading demo data from {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        pages = json.load(f)
    logger.info(f"Loaded {len(pages)} raw pages")
    return pages


def run_scraper(urls: list[str] = None, pdf_paths: list[str] = None, output_dir: str = "data/raw"):
    """Run the full scraping pipeline."""
    results = []

    if urls:
        for url in urls:
            logger.info(f"Scraping: {url}")
            page = scrape_url(url)
            if page:
                results.append(asdict(page))

    if pdf_paths:
        for pdf_path in pdf_paths:
            logger.info(f"Parsing PDF: {pdf_path}")
            page = parse_pdf(pdf_path)
            if page:
                results.append(asdict(page))

    if not results:
        logger.info("No URLs or PDFs provided. Loading demo data.")
        results = load_demo_data()

    # Save results
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "scraped_pages.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved {len(results)} pages to {output_path}")
    success = sum(1 for r in results if r.get("extraction_status", "success") == "success")
    failed = len(results) - success
    logger.info(f"Results: {success} successful, {failed} failed")

    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="TalentBridge KB Scraper")
    parser.add_argument("--url", nargs="*", help="URLs to scrape")
    parser.add_argument("--pdf", nargs="*", help="PDF files to parse")
    parser.add_argument("--output", default="data/raw", help="Output directory")
    parser.add_argument("--demo", action="store_true", help="Use demo data")
    args = parser.parse_args()

    if args.demo or (not args.url and not args.pdf):
        data = load_demo_data()
        print(f"Loaded {len(data)} demo pages")
    else:
        run_scraper(urls=args.url, pdf_paths=args.pdf, output_dir=args.output)
