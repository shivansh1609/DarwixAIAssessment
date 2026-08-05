"""
Intelligent Chunking Engine
============================
Splits cleaned records into semantically meaningful chunks for embedding.

Chunking strategies:
1. Section-based: Split on headings (##, Q:, numbered items)
2. FAQ-pair: Keep Q&A pairs as single chunks
3. Table-preserving: Keep tables intact
4. Sliding window: For long prose, use overlap windows

Each chunk gets:
- Unique record_id
- Parent context (section heading, page title)
- Full metadata for retrieval filtering
- Category and subcategory from taxonomy
"""

import json
import re
import os
import uuid
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


# ─── Taxonomy Classification ────────────────────────────────────────────────

TAXONOMY_RULES = [
    # (keyword patterns in content, category, subcategory)
    (r"(?:job description|key responsibilities|qualifications|experience.*years|salary range)",
     "jobs", "job_listings"),
    (r"(?:frequently asked|FAQ|Q:|A:)", "faq", "general_faq"),
    (r"(?:screening process|step \d|initial.*screening|technical assessment)",
     "process", "screening_process"),
    (r"(?:qualification.*score|hot lead|warm lead|cold lead|disqualification)",
     "qualification", "scoring_rules"),
    (r"(?:notice period|salary negotiation|referral bonus)",
     "qualification", "screening_policies"),
    (r"(?:objection|response strategy|too low|don't want|long notice)",
     "objections", "objection_handling"),
    (r"(?:health insurance|paid leave|stock option|ESOP|learning budget|benefits)",
     "benefits", "employee_benefits"),
    (r"(?:our culture|core values|diversity|engineering culture)",
     "company", "culture_values"),
    (r"(?:about talentbridge|our mission|our process|office location)",
     "company", "about"),
    (r"(?:tech stack|backend|frontend|infrastructure|AI/ML)",
     "company", "technology"),
    (r"(?:interview tips|prepare|coding challenge|case study)",
     "process", "interview_preparation"),
    (r"(?:checklist|pre-call|during call|post-call|information to collect)",
     "process", "screening_checklist"),
    (r"(?:candidate.*record|database.*sample|PII.*test)",
     "internal", "test_data"),
    (r"(?:customer support|BPO|rotational shift)",
     "jobs", "support_roles"),
]


def classify_content(text: str, page_title: str = "") -> tuple[str, str]:
    """Classify content into taxonomy categories."""
    combined = f"{page_title} {text}".lower()
    for pattern, category, subcategory in TAXONOMY_RULES:
        if re.search(pattern, combined, re.IGNORECASE):
            return category, subcategory
    return "general", "uncategorized"


# ─── Chunking Strategies ────────────────────────────────────────────────────

def chunk_by_faq(text: str) -> list[dict]:
    """Split FAQ content into Q&A pairs."""
    chunks = []
    # Pattern: "Q: ... A: ..." or "Question\nAnswer"
    qa_pattern = re.compile(
        r"(?:^|\n)Q:\s*(.*?)(?:\n)A:\s*(.*?)(?=\nQ:|\n\n[A-Z]|\Z)",
        re.DOTALL
    )
    matches = list(qa_pattern.finditer(text))

    if matches:
        for match in matches:
            question = match.group(1).strip()
            answer = match.group(2).strip()
            chunks.append({
                "content": f"Q: {question}\nA: {answer}",
                "chunk_type": "faq_pair",
                "heading": question[:100],
            })
    else:
        # Fallback: split by blank lines for non-standard FAQ format
        chunks = chunk_by_sections(text)

    return chunks


def chunk_by_sections(text: str) -> list[dict]:
    """Split content by headings and logical sections."""
    chunks = []
    # Split on heading-like patterns
    section_pattern = re.compile(
        r"(?:^|\n)(?:#{1,3}\s+|(?:[A-Z][A-Za-z\s&]+)\n[-=]+\n|(?:^[A-Z][A-Za-z\s&/]{5,60}$))",
        re.MULTILINE
    )

    # Find all heading positions
    heading_positions = [(m.start(), m.group().strip()) for m in section_pattern.finditer(text)]

    if not heading_positions:
        # No clear headings — use sliding window
        return chunk_by_window(text)

    for i, (pos, heading) in enumerate(heading_positions):
        end_pos = heading_positions[i + 1][0] if i + 1 < len(heading_positions) else len(text)
        section_content = text[pos:end_pos].strip()

        if len(section_content.split()) < 10:
            continue  # Skip very short sections

        chunks.append({
            "content": section_content,
            "chunk_type": "section",
            "heading": heading.strip("#").strip()[:100],
        })

    # If no chunks were created, fall back to window
    if not chunks:
        return chunk_by_window(text)

    return chunks


def chunk_by_window(text: str, max_words: int = 400, overlap_words: int = 80) -> list[dict]:
    """Sliding window chunking for long prose."""
    words = text.split()
    chunks = []

    if len(words) <= max_words:
        return [{
            "content": text,
            "chunk_type": "full_document",
            "heading": "",
        }]

    start = 0
    while start < len(words):
        end = min(start + max_words, len(words))
        chunk_text = " ".join(words[start:end])
        chunks.append({
            "content": chunk_text,
            "chunk_type": "window",
            "heading": "",
        })
        if end >= len(words):
            break
        start = end - overlap_words

    return chunks


def chunk_job_listing(text: str) -> list[dict]:
    """Special chunking for job listings — keep structured sections together."""
    chunks = []

    # Extract key sections
    sections = {
        "overview": r"(.*?)(?=Key Responsibilities|Responsibilities|Requirements)",
        "responsibilities": r"(?:Key Responsibilities|Responsibilities)\s*(.*?)(?=Required Qualifications|Qualifications|Requirements|Preferred)",
        "qualifications": r"(?:Required Qualifications|Qualifications|Requirements)\s*(.*?)(?=Preferred|Benefits|Apply|$)",
        "preferred": r"(?:Preferred\s*(?:Qualifications)?)\s*(.*?)(?=Benefits|Apply|$)",
        "benefits": r"(?:Benefits)\s*(.*?)(?=Apply|Application|Contact|$)",
    }

    for section_name, pattern in sections.items():
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            content = match.group(1).strip() if match.lastindex else match.group(0).strip()
            if content and len(content.split()) > 10:
                chunks.append({
                    "content": content,
                    "chunk_type": f"job_{section_name}",
                    "heading": section_name.replace("_", " ").title(),
                })

    if not chunks:
        return chunk_by_sections(text)

    return chunks


def chunk_record(record: dict) -> list[dict]:
    """Choose the best chunking strategy for a record and generate KB records."""
    content = record.get("redacted_content", record.get("cleaned_content", ""))
    page_title = record.get("page_title", "")
    source_url = record.get("source_url", "")
    source_type = record.get("source_type", "unknown")

    # Determine category
    category, subcategory = classify_content(content, page_title)

    # Choose chunking strategy
    if category == "faq":
        raw_chunks = chunk_by_faq(content)
    elif category == "jobs" and subcategory == "job_listings":
        raw_chunks = chunk_job_listing(content)
    elif len(content.split()) > 500:
        raw_chunks = chunk_by_sections(content)
    else:
        raw_chunks = chunk_by_window(content)

    # Build KB records from chunks
    kb_records = []
    parent_id = f"kb_{category}_{uuid.uuid4().hex[:8]}"

    for i, chunk in enumerate(raw_chunks):
        record_id = f"{parent_id}_c{i:02d}"
        kb_record = {
            "record_id": record_id,
            "title": chunk["heading"] or page_title,
            "content": chunk["content"],
            "content_type": chunk["chunk_type"],
            "category": category,
            "subcategory": subcategory,
            "source_url": source_url,
            "source_type": source_type,
            "source_page_title": page_title,
            "extraction_date": record.get("extraction_date", ""),
            "version": "1.0",
            "pii_flag": record.get("pii_flag", False),
            "chunk_index": i,
            "total_chunks": len(raw_chunks),
            "parent_record_id": parent_id,
            "tags": extract_tags(chunk["content"], category),
            "last_verified": record.get("extraction_date", ""),
            "quality_score": record.get("quality", {}).get("quality_score", 1.0),
            "language": "en",
        }
        kb_records.append(kb_record)

    return kb_records


def extract_tags(content: str, category: str) -> list[str]:
    """Extract relevant tags from content."""
    tags = [category]
    content_lower = content.lower()

    tag_keywords = {
        "engineering": ["engineer", "developer", "coding", "backend", "frontend"],
        "data": ["data analyst", "sql", "dashboard", "analytics", "data science"],
        "product": ["product manager", "roadmap", "prd", "user stories"],
        "remote": ["remote", "work from home", "wfh"],
        "hybrid": ["hybrid", "days in office"],
        "benefits": ["insurance", "leave", "stock", "esop", "bonus"],
        "salary": ["salary", "compensation", "ctc", "lpa"],
        "screening": ["screening", "qualification", "interview"],
        "objection": ["objection", "concern", "hesitat"],
        "bangalore": ["bangalore", "bengaluru"],
        "manila": ["manila", "philippines"],
        "jakarta": ["jakarta", "indonesia"],
        "singapore": ["singapore"],
    }

    for tag, keywords in tag_keywords.items():
        if any(kw in content_lower for kw in keywords):
            tags.append(tag)

    return list(set(tags))[:10]  # Cap at 10 tags


def run_chunker(input_path: str, output_path: str):
    """Run chunking on all deduplicated records."""
    logger.info(f"Loading data from {input_path}")
    with open(input_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    logger.info(f"Chunking {len(records)} records...")
    all_kb_records = []
    for record in records:
        chunks = chunk_record(record)
        all_kb_records.extend(chunks)
        logger.info(f"  '{record.get('page_title', 'unknown')}' → {len(chunks)} chunks")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_kb_records, f, indent=2, ensure_ascii=False)

    # Category distribution
    categories = {}
    for r in all_kb_records:
        cat = r["category"]
        categories[cat] = categories.get(cat, 0) + 1

    logger.info(f"Chunking complete: {len(records)} records → {len(all_kb_records)} KB chunks")
    logger.info(f"Category distribution: {json.dumps(categories, indent=2)}")
    logger.info(f"Output saved to {output_path}")
    return all_kb_records


if __name__ == "__main__":
    base_dir = os.path.join(os.path.dirname(__file__), "..")
    run_chunker(
        os.path.join(base_dir, "data", "cleaned", "deduplicated.json"),
        os.path.join(base_dir, "data", "cleaned", "kb_records.json"),
    )
