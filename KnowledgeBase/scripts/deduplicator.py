"""
Near-Duplicate Detection and Removal
=====================================
Identifies and removes duplicate or near-duplicate content from KB records.

Strategy:
- Exact duplicates: MD5 hash comparison on cleaned content
- Near-duplicates: Jaccard similarity on 3-gram shingles (threshold 0.85)
- Cross-source dedup: Same content appearing on multiple pages
- Keeps the version with higher quality score when duplicates found
"""

import json
import os
import hashlib
import logging
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def compute_hash(text: str) -> str:
    """Compute MD5 hash for exact duplicate detection."""
    normalized = " ".join(text.lower().split())
    return hashlib.md5(normalized.encode("utf-8")).hexdigest()


def get_shingles(text: str, n: int = 3) -> set:
    """Generate n-gram word shingles for near-duplicate detection."""
    words = text.lower().split()
    if len(words) < n:
        return {tuple(words)}
    return {tuple(words[i:i+n]) for i in range(len(words) - n + 1)}


def jaccard_similarity(set_a: set, set_b: set) -> float:
    """Compute Jaccard similarity between two shingle sets."""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def find_duplicates(records: list[dict], similarity_threshold: float = 0.85) -> dict:
    """Find exact and near-duplicate records."""
    # Phase 1: Exact duplicates (hash-based)
    hash_groups = defaultdict(list)
    for i, record in enumerate(records):
        content = record.get("redacted_content", record.get("cleaned_content", ""))
        h = compute_hash(content)
        hash_groups[h].append(i)

    exact_dupes = {h: indices for h, indices in hash_groups.items() if len(indices) > 1}

    # Phase 2: Near-duplicates (Jaccard on shingles)
    shingles_cache = {}
    for i, record in enumerate(records):
        content = record.get("redacted_content", record.get("cleaned_content", ""))
        shingles_cache[i] = get_shingles(content)

    near_dupes = []
    checked = set()
    for i in range(len(records)):
        for j in range(i + 1, len(records)):
            if (i, j) in checked:
                continue
            checked.add((i, j))

            # Skip if already found as exact duplicate
            h_i = compute_hash(records[i].get("redacted_content", records[i].get("cleaned_content", "")))
            h_j = compute_hash(records[j].get("redacted_content", records[j].get("cleaned_content", "")))
            if h_i == h_j:
                continue

            sim = jaccard_similarity(shingles_cache[i], shingles_cache[j])
            if sim >= similarity_threshold:
                near_dupes.append({
                    "index_a": i,
                    "index_b": j,
                    "title_a": records[i].get("page_title", ""),
                    "title_b": records[j].get("page_title", ""),
                    "similarity": round(sim, 3),
                })

    return {
        "exact_duplicates": exact_dupes,
        "near_duplicates": near_dupes,
    }


def deduplicate(records: list[dict], similarity_threshold: float = 0.85) -> list[dict]:
    """Remove duplicates, keeping the higher-quality version."""
    dupes = find_duplicates(records, similarity_threshold)
    indices_to_remove = set()

    # Handle exact duplicates
    for h, indices in dupes["exact_duplicates"].items():
        # Keep the one with highest quality score
        best_idx = max(indices, key=lambda i: records[i].get("quality", {}).get("quality_score", 0))
        for idx in indices:
            if idx != best_idx:
                indices_to_remove.add(idx)
                logger.info(
                    f"Exact duplicate removed: '{records[idx].get('page_title', '')}' "
                    f"(duplicate of '{records[best_idx].get('page_title', '')}')"
                )

    # Handle near-duplicates
    for dupe in dupes["near_duplicates"]:
        i, j = dupe["index_a"], dupe["index_b"]
        if i in indices_to_remove or j in indices_to_remove:
            continue

        score_i = records[i].get("quality", {}).get("quality_score", 0)
        score_j = records[j].get("quality", {}).get("quality_score", 0)
        remove_idx = j if score_i >= score_j else i
        keep_idx = i if remove_idx == j else j
        indices_to_remove.add(remove_idx)

        logger.info(
            f"Near-duplicate removed (similarity={dupe['similarity']}): "
            f"'{records[remove_idx].get('page_title', '')}' "
            f"(similar to '{records[keep_idx].get('page_title', '')}')"
        )

    deduplicated = [r for i, r in enumerate(records) if i not in indices_to_remove]

    logger.info(f"Deduplication: {len(records)} → {len(deduplicated)} records "
                f"({len(indices_to_remove)} removed)")

    return deduplicated, dupes


def run_deduplicator(input_path: str, output_path: str, threshold: float = 0.85):
    """Run deduplication on PII-processed records."""
    logger.info(f"Loading data from {input_path}")
    with open(input_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    deduplicated, dupe_report = deduplicate(records, threshold)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(deduplicated, f, indent=2, ensure_ascii=False)

    # Save dedup report
    report_path = output_path.replace(".json", "_dedup_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(dupe_report, f, indent=2, ensure_ascii=False)

    logger.info(f"Deduplicated output: {output_path}")
    logger.info(f"Dedup report: {report_path}")
    return deduplicated


if __name__ == "__main__":
    base_dir = os.path.join(os.path.dirname(__file__), "..")
    run_deduplicator(
        os.path.join(base_dir, "data", "cleaned", "pii_processed.json"),
        os.path.join(base_dir, "data", "cleaned", "deduplicated.json"),
    )
