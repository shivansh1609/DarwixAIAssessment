"""
Data Cleaning Pipeline
======================
Cleans raw scraped content: normalizes formatting, removes boilerplate,
standardizes terminology, and prepares records for chunking.

Pipeline steps:
1. Remove remaining boilerplate (nav, footer, cookie, social)
2. Normalize dates, currency, headings
3. Standardize terminology (job titles, levels)
4. Flag source errors (empty content, broken references)
5. Output cleaned records with quality scores
"""

import json
import re
import os
import logging
from datetime import datetime
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


# ─── Terminology Standardization ────────────────────────────────────────────

TERMINOLOGY_MAP = {
    # Salary format variations
    r"₹(\d+)L": r"₹\1,00,000",
    r"(\d+)\s*LPA": r"₹\1,00,000 per annum",
    r"(\d+)\s*PA\b": r"\1 per annum",

    # Job title normalization
    r"\bSr\.?\s": "Senior ",
    r"\bJr\.?\s": "Junior ",
    r"\bSDE\b": "Software Development Engineer",
    r"\bSWE\b": "Software Engineer",
    r"\bPM\b": "Product Manager",
    r"\bDS\b": "Data Scientist",
    r"\bDA\b": "Data Analyst",
    r"\bBA\b": "Business Analyst",

    # Education normalization
    r"\bBTech\b": "B.Tech",
    r"\bBE\b": "B.E.",
    r"\bMTech\b": "M.Tech",
    r"\bMBA\b": "M.B.A.",

    # Company shorthand
    r"\bWFH\b": "Work From Home",
    r"\bWFO\b": "Work From Office",
}

# Date normalization patterns
DATE_PATTERNS = [
    (r"(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*)\s+(\d{1,2}),?\s+(\d{4})",
     None),  # "August 31, 2026" — already good
    (r"(\d{1,2})/(\d{1,2})/(\d{4})",
     None),  # "07/22/1995" — normalize to ISO
    (r"(\b(?:Sep|Oct|Nov|Dec|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug)\w*)\s+(\d{1,2})\s+(\d{4})",
     None),  # "Sep 30 2026"
]

MONTH_MAP = {
    "jan": "01", "january": "01", "feb": "02", "february": "02",
    "mar": "03", "march": "03", "apr": "04", "april": "04",
    "may": "05", "jun": "06", "june": "06", "jul": "07", "july": "07",
    "aug": "08", "august": "08", "sep": "09", "september": "09",
    "oct": "10", "october": "10", "nov": "11", "november": "11",
    "dec": "12", "december": "12",
}


def normalize_dates(text: str) -> str:
    """Normalize dates to ISO 8601 format where possible."""
    # Pattern: "Month DD, YYYY" or "Month DD YYYY"
    def replace_month_day_year(match):
        month_str = match.group(1).lower()[:3]
        day = match.group(2).zfill(2)
        year = match.group(3)
        month = MONTH_MAP.get(month_str, "01")
        return f"{year}-{month}-{day}"

    text = re.sub(
        r"\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*)\s+(\d{1,2}),?\s+(\d{4})\b",
        replace_month_day_year, text, flags=re.IGNORECASE
    )

    # Pattern: "MM/DD/YYYY"
    def replace_slash_date(match):
        month = match.group(1).zfill(2)
        day = match.group(2).zfill(2)
        year = match.group(3)
        return f"{year}-{month}-{day}"

    text = re.sub(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", replace_slash_date, text)

    return text


def normalize_currency(text: str) -> str:
    """Standardize currency formatting."""
    # ₹25L → ₹25,00,000
    text = re.sub(r"₹\s*(\d+)\s*L\b", lambda m: f"₹{int(m.group(1)):,}00,000".replace(",", ","), text)
    # Add commas to large INR numbers
    text = re.sub(r"₹\s*(\d{1,3})((?:\d{2})*\d{3})\b",
                  lambda m: f"₹{m.group(1)},{','.join(re.findall(r'\d{2}', m.group(2)[:-3]))},{m.group(2)[-3:]}" if len(m.group(2)) > 3 else f"₹{m.group(1)},{m.group(2)}",
                  text)
    return text


def standardize_terminology(text: str) -> str:
    """Apply terminology standardization mappings."""
    for pattern, replacement in TERMINOLOGY_MAP.items():
        text = re.sub(pattern, replacement, text)
    return text


def normalize_headings(text: str) -> str:
    """Ensure consistent heading formatting."""
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        stripped = line.strip()
        # If a line is short, ALL CAPS, and not a common abbreviation, title-case it
        if (stripped.isupper() and len(stripped) > 3 and len(stripped) < 80
                and stripped not in ("CONFIDENTIAL", "FAQ", "Q&A", "PDF", "PII")):
            stripped = stripped.title()
        cleaned.append(stripped)
    return "\n".join(cleaned)


def remove_excessive_whitespace(text: str) -> str:
    """Collapse multiple blank lines and trailing whitespace."""
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def assess_quality(text: str, source_url: str) -> dict:
    """Assess content quality and flag issues."""
    issues = []
    quality_score = 1.0

    if len(text.strip()) < 50:
        issues.append("Content too short (<50 chars)")
        quality_score -= 0.5

    if text.count("□") > 5:
        issues.append("Contains checklist formatting (may be internal doc)")

    if "CONFIDENTIAL" in text.upper() or "INTERNAL USE ONLY" in text.upper():
        issues.append("Contains confidentiality markers")
        quality_score -= 0.1

    if "TODO" in text or "FIXME" in text:
        issues.append("Contains unfinished markers")
        quality_score -= 0.2

    if re.search(r"(https?://\S+broken|404|page not found)", text, re.IGNORECASE):
        issues.append("Contains broken reference indicators")
        quality_score -= 0.3

    # Check for obvious contradictions within the same document
    if "fully remote" in text.lower() and "3 days in office" in text.lower():
        issues.append("Potential contradiction: mentions both remote and in-office")

    return {
        "quality_score": max(0.0, round(quality_score, 2)),
        "issues": issues,
        "word_count": len(text.split()),
        "has_tables": "|" in text and text.count("|") > 4,
        "has_lists": bool(re.search(r"^[\-\•\*□]\s", text, re.MULTILINE)),
    }


def clean_record(raw_record: dict) -> dict:
    """Clean a single raw record through the full pipeline."""
    text = raw_record.get("raw_html_stripped", "")
    source_url = raw_record.get("source_url", "")

    # Step 1: Normalize headings
    text = normalize_headings(text)

    # Step 2: Normalize dates
    text = normalize_dates(text)

    # Step 3: Standardize terminology
    text = standardize_terminology(text)

    # Step 4: Normalize currency (basic)
    text = normalize_currency(text)

    # Step 5: Remove excessive whitespace
    text = remove_excessive_whitespace(text)

    # Step 6: Quality assessment
    quality = assess_quality(text, source_url)

    return {
        "source_url": source_url,
        "source_type": raw_record.get("source_type", "unknown"),
        "page_title": raw_record.get("page_title", "").strip(),
        "extraction_date": raw_record.get("extraction_date", datetime.now().strftime("%Y-%m-%d")),
        "cleaned_content": text,
        "quality": quality,
    }


def run_cleaner(input_path: str, output_path: str):
    """Run the cleaning pipeline on all raw records."""
    logger.info(f"Loading raw data from {input_path}")
    with open(input_path, "r", encoding="utf-8") as f:
        raw_records = json.load(f)

    logger.info(f"Cleaning {len(raw_records)} records...")
    cleaned = []
    for i, record in enumerate(raw_records):
        cleaned_record = clean_record(record)
        cleaned.append(cleaned_record)

        issues = cleaned_record["quality"]["issues"]
        if issues:
            logger.warning(f"Record {i} ({record.get('page_title', 'unknown')}): {issues}")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, indent=2, ensure_ascii=False)

    good = sum(1 for r in cleaned if r["quality"]["quality_score"] >= 0.8)
    warn = sum(1 for r in cleaned if 0.5 <= r["quality"]["quality_score"] < 0.8)
    bad = sum(1 for r in cleaned if r["quality"]["quality_score"] < 0.5)

    logger.info(f"Cleaning complete: {good} good, {warn} warnings, {bad} poor quality")
    logger.info(f"Output saved to {output_path}")
    return cleaned


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Clean raw scraped data")
    parser.add_argument("--input", default="data/raw/scraped_pages.json")
    parser.add_argument("--output", default="data/cleaned/cleaned_records.json")
    args = parser.parse_args()

    base_dir = os.path.join(os.path.dirname(__file__), "..")
    run_cleaner(
        os.path.join(base_dir, args.input),
        os.path.join(base_dir, args.output),
    )
