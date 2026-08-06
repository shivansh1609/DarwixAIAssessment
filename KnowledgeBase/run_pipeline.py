

import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Add scripts dir to path
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "scripts")
sys.path.insert(0, SCRIPTS_DIR)

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
CLEANED_DIR = os.path.join(DATA_DIR, "cleaned")
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")


def run_pipeline(skip_index: bool = False):
    """Execute the full KB pipeline."""
    logger.info("=" * 60)
    logger.info("TalentBridge Knowledge Base Pipeline")
    logger.info("=" * 60)

    # Step 1: Load raw data (demo)
    logger.info("\n[1/6] Loading raw data...")
    from scraper import load_demo_data
    raw_data = load_demo_data(RAW_DIR)
    logger.info(f"Loaded {len(raw_data)} raw pages")

    # Step 2: Clean
    logger.info("\n[2/6] Cleaning records...")
    from cleaner import run_cleaner
    cleaned_path = os.path.join(CLEANED_DIR, "cleaned_records.json")
    os.makedirs(CLEANED_DIR, exist_ok=True)
    run_cleaner(
        os.path.join(RAW_DIR, "scraped_pages.json"),
        cleaned_path,
    )

    # Step 3: PII Detection
    logger.info("\n[3/6] Detecting PII...")
    from pii_detector import run_pii_detector
    pii_path = os.path.join(CLEANED_DIR, "pii_processed.json")
    run_pii_detector(cleaned_path, pii_path)

    # Step 4: Deduplication
    logger.info("\n[4/6] Deduplicating...")
    from deduplicator import run_deduplicator
    dedup_path = os.path.join(CLEANED_DIR, "deduplicated.json")
    run_deduplicator(pii_path, dedup_path)

    # Step 5: Chunking
    logger.info("\n[5/6] Chunking records...")
    from chunker import run_chunker
    kb_path = os.path.join(CLEANED_DIR, "kb_records.json")
    run_chunker(dedup_path, kb_path)

    # Step 6: Indexing
    if skip_index:
        logger.info("\n[6/6] Skipping indexing (--skip-index)")
    else:
        logger.info("\n[6/6] Indexing into ChromaDB...")
        from indexer import run_indexer
        run_indexer(kb_path, CHROMA_DIR)

    logger.info("\n" + "=" * 60)
    logger.info("Pipeline complete!")
    logger.info(f"KB records: {kb_path}")
    if not skip_index:
        logger.info(f"ChromaDB: {CHROMA_DIR}")
    logger.info("=" * 60)


if __name__ == "__main__":
    skip = "--skip-index" in sys.argv
    run_pipeline(skip_index=skip)
