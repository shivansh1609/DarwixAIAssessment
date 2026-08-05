"""
PII Detection and Protection
==============================
Identifies and flags personally identifiable information in KB records.

Detected PII types:
- Email addresses
- Phone numbers (India, Philippines, Indonesia, international)
- Aadhaar numbers (India)
- SSS numbers (Philippines)
- KTP/NIK numbers (Indonesia)
- Names (heuristic-based)
- Dates of birth
- Salary figures tied to individuals
- Addresses

Strategy:
- Regex-based detection for structured PII (emails, phones, IDs)
- Pattern-based heuristic for names and DOB
- Flag PII fields in metadata, DO NOT delete (needed for audit)
- Provide redacted version for KB storage
"""

import re
import json
import os
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


# ─── PII Regex Patterns ─────────────────────────────────────────────────────

PII_PATTERNS = {
    "email": {
        "pattern": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "description": "Email address",
        "severity": "high",
    },
    "phone_india": {
        "pattern": r"\+91[-\s]?\d{5}[-\s]?\d{5}",
        "description": "Indian phone number",
        "severity": "high",
    },
    "phone_philippines": {
        "pattern": r"\+63[-\s]?\d{3}[-\s]?\d{3}[-\s]?\d{4}",
        "description": "Philippines phone number",
        "severity": "high",
    },
    "phone_indonesia": {
        "pattern": r"\+62[-\s]?\d{3}[-\s]?\d{4}[-\s]?\d{4}",
        "description": "Indonesian phone number",
        "severity": "high",
    },
    "phone_generic": {
        "pattern": r"\+\d{1,3}[-\s]?\d{3,5}[-\s]?\d{3,5}[-\s]?\d{0,5}",
        "description": "International phone number",
        "severity": "high",
    },
    "aadhaar": {
        "pattern": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
        "description": "Aadhaar number (India)",
        "severity": "critical",
    },
    "sss_philippines": {
        "pattern": r"\b\d{2}-\d{7}-\d{1}\b",
        "description": "SSS number (Philippines)",
        "severity": "critical",
    },
    "ktp_indonesia": {
        "pattern": r"\b\d{16}\b",
        "description": "KTP/NIK number (Indonesia) — 16-digit national ID",
        "severity": "critical",
    },
    "date_of_birth": {
        "pattern": r"(?:Date of Birth|DOB|Born)\s*:?\s*(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{4})",
        "description": "Date of birth",
        "severity": "high",
    },
    "salary_individual": {
        "pattern": r"(?:Current Salary|Salary)\s*:?\s*(?:₹|PHP|IDR|Rs\.?)\s*[\d,]+",
        "description": "Individual salary information",
        "severity": "medium",
    },
}

# Name detection heuristic — look for "Name:" label followed by capitalized words
NAME_PATTERN = re.compile(
    r"(?:Full\s*)?Name\s*:?\s*([A-Z][a-z]+(?: [A-Z][a-z]+){1,3})",
    re.IGNORECASE
)


def detect_pii(text: str) -> list[dict]:
    """Detect all PII instances in the given text."""
    findings = []

    for pii_type, config in PII_PATTERNS.items():
        matches = re.finditer(config["pattern"], text, re.IGNORECASE)
        for match in matches:
            findings.append({
                "type": pii_type,
                "value": match.group(0),
                "position": match.start(),
                "description": config["description"],
                "severity": config["severity"],
            })

    # Name detection
    for match in NAME_PATTERN.finditer(text):
        name = match.group(1)
        # Exclude common non-name patterns
        exclude = {"Product Manager", "Data Analyst", "Senior Software", "Customer Support",
                    "Business Analyst", "Data Engineer", "Staff Engineer", "Backend Engineer"}
        if name not in exclude and len(name.split()) >= 2:
            findings.append({
                "type": "person_name",
                "value": name,
                "position": match.start(),
                "description": "Person's name",
                "severity": "high",
            })

    return findings


def redact_pii(text: str, findings: list[dict]) -> str:
    """Redact PII from text, replacing with type-specific placeholders."""
    redacted = text
    # Sort by position descending to avoid offset issues
    for finding in sorted(findings, key=lambda x: x["position"], reverse=True):
        placeholder = f"[REDACTED_{finding['type'].upper()}]"
        redacted = redacted[:finding["position"]] + placeholder + redacted[finding["position"] + len(finding["value"]):]
    return redacted


def process_record(record: dict) -> dict:
    """Process a single record for PII detection."""
    text = record.get("cleaned_content", "")
    findings = detect_pii(text)

    pii_types = list(set(f["type"] for f in findings))
    has_pii = len(findings) > 0
    max_severity = "none"
    if findings:
        severity_order = {"critical": 3, "high": 2, "medium": 1, "low": 0}
        max_severity = max(findings, key=lambda f: severity_order.get(f["severity"], 0))["severity"]

    record["pii_flag"] = has_pii
    record["pii_types"] = pii_types
    record["pii_count"] = len(findings)
    record["pii_max_severity"] = max_severity
    record["pii_findings"] = findings

    # Generate redacted version for KB (original preserved for audit)
    if has_pii:
        record["redacted_content"] = redact_pii(text, findings)
        logger.warning(
            f"PII detected in '{record.get('page_title', 'unknown')}': "
            f"{len(findings)} instances ({', '.join(pii_types)})"
        )
    else:
        record["redacted_content"] = text

    return record


def run_pii_detector(input_path: str, output_path: str):
    """Run PII detection on all cleaned records."""
    logger.info(f"Loading cleaned data from {input_path}")
    with open(input_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    logger.info(f"Scanning {len(records)} records for PII...")
    processed = [process_record(record) for record in records]

    pii_records = sum(1 for r in processed if r["pii_flag"])
    total_findings = sum(r["pii_count"] for r in processed)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(processed, f, indent=2, ensure_ascii=False)

    logger.info(f"PII scan complete: {pii_records}/{len(processed)} records contain PII")
    logger.info(f"Total PII findings: {total_findings}")
    logger.info(f"Output saved to {output_path}")

    # Summary report
    if pii_records > 0:
        logger.info("─── PII Summary ───")
        for r in processed:
            if r["pii_flag"]:
                logger.info(f"  {r['page_title']}: {r['pii_count']} findings ({r['pii_max_severity']})")

    return processed


if __name__ == "__main__":
    base_dir = os.path.join(os.path.dirname(__file__), "..")
    run_pii_detector(
        os.path.join(base_dir, "data", "cleaned", "cleaned_records.json"),
        os.path.join(base_dir, "data", "cleaned", "pii_processed.json"),
    )
