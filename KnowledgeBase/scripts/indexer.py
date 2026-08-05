"""
Knowledge Base Indexer — Pure Python Version
=============================================
Embeds KB records using sentence-transformers (FREE, local) and stores 
in a simple NumPy/JSON file to avoid any C++ build errors on Windows.

No API keys needed. Everything runs locally and installs instantly!
"""

import json
import os
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    logger.error("numpy not installed. Run: pip install numpy")

try:
    from sentence_transformers import SentenceTransformer
    HAS_ST = True
except ImportError:
    HAS_ST = False
    logger.warning("sentence-transformers not installed. Run: pip install sentence-transformers")


# ─── Free Local Embedder ────────────────────────────────────────────────────

class LocalEmbedder:
    """Generates embeddings using sentence-transformers (FREE, no API key)."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        if not HAS_ST:
            raise ImportError("sentence-transformers required. Run: pip install sentence-transformers")
        logger.info(f"Loading embedding model: {model_name} (first run downloads ~80MB)...")
        self.model = SentenceTransformer(model_name)
        logger.info("Embedding model loaded successfully")

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts."""
        embeddings = self.model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
        return embeddings.tolist()


def cosine_similarity(query_vec, doc_vecs):
    """Compute cosine similarity between query and all docs."""
    if not HAS_NUMPY:
        return [0] * len(doc_vecs)
    q = np.array(query_vec)
    d = np.array(doc_vecs)
    # Cosine similarity = dot(a, b) / (norm(a) * norm(b))
    dot_product = np.dot(d, q)
    norm_q = np.linalg.norm(q)
    norm_d = np.linalg.norm(d, axis=1)
    # Prevent division by zero
    norm_d[norm_d == 0] = 1e-10
    norm_q = 1e-10 if norm_q == 0 else norm_q
    
    similarities = dot_product / (norm_d * norm_q)
    return similarities.tolist()


# ─── Pure NumPy Index ───────────────────────────────────────────────────────

class KnowledgeBaseIndex:
    """Pure Python knowledge base with free local embeddings. No C++ compiler needed!"""

    def __init__(self, persist_dir: str = None):
        if not HAS_NUMPY:
            raise ImportError("numpy is required. Run: pip install numpy")

        if persist_dir is None:
            persist_dir = os.path.join(os.path.dirname(__file__), "..", "chroma_db")

        os.makedirs(persist_dir, exist_ok=True)
        self.persist_dir = persist_dir
        self.index_path = os.path.join(persist_dir, "numpy_index.json")
        
        self.documents = []
        self.embeddings = []
        
        # Load existing index if it exists
        if os.path.exists(self.index_path):
            try:
                with open(self.index_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.documents = data.get("documents", [])
                    self.embeddings = data.get("embeddings", [])
                logger.info(f"Loaded existing index with {len(self.documents)} records")
            except Exception as e:
                logger.error(f"Failed to load index: {e}")

        # Initialize embedder
        try:
            self.embedder = LocalEmbedder()
        except Exception as e:
            logger.error(f"Failed to load embedder: {e}")
            self.embedder = None

    def index_records(self, records: list[dict]):
        """Index all KB records into memory and save to JSON."""
        if not records:
            logger.warning("No records to index")
            return

        self.documents = []
        texts_to_embed = []

        for record in records:
            doc_text = f"{record.get('title', '')}. {record['content']}"

            metadata = {
                "record_id": record["record_id"],
                "title": record.get("title", "")[:200],
                "category": record.get("category", "general"),
                "subcategory": record.get("subcategory", "uncategorized"),
                "source_url": record.get("source_url", ""),
                "source_type": record.get("source_type", "unknown"),
                "content_type": record.get("content_type", "text"),
                "pii_flag": record.get("pii_flag", False),
                "version": record.get("version", "1.0"),
                "quality_score": record.get("quality_score", 1.0),
                "chunk_index": record.get("chunk_index", 0),
                "total_chunks": record.get("total_chunks", 1),
                "tags": ",".join(record.get("tags", [])),
                "content": doc_text
            }

            self.documents.append(metadata)
            texts_to_embed.append(doc_text)

        # Embed with local model
        if self.embedder:
            logger.info(f"Generating embeddings for {len(self.documents)} records (local, free)...")
            self.embeddings = self.embedder.embed(texts_to_embed)
        else:
            logger.warning("No embedder available! Using zero embeddings.")
            self.embeddings = [[0.0] * 384 for _ in self.documents]

        # Save to disk
        self._save_index()
        logger.info(f"Indexed {len(records)} records into pure NumPy index")

    def _save_index(self):
        """Save index to JSON."""
        data = {
            "documents": self.documents,
            "embeddings": self.embeddings
        }
        with open(self.index_path, 'w', encoding='utf-8') as f:
            json.dump(data, f)

    def search(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None,
        min_quality: float = 0.5,
    ) -> list[dict]:
        """Search the knowledge base with optional filtering using cosine similarity."""
        if not self.documents or not self.embeddings:
            return []

        # Embed query
        if not self.embedder:
            return []
            
        query_embedding = self.embedder.embed([query])[0]
        
        # Calculate similarities
        similarities = cosine_similarity(query_embedding, self.embeddings)
        
        # Create results list with scores
        results = []
        for i, doc in enumerate(self.documents):
            score = similarities[i]
            
            # Apply filters
            if category and doc.get("category") != category:
                continue
            if doc.get("quality_score", 1.0) < min_quality:
                continue
            if doc.get("pii_flag", False):
                continue
                
            results.append({
                "record_id": doc["record_id"],
                "content": doc["content"],
                "metadata": doc,
                "similarity_score": round(score, 4),
                "source_url": doc.get("source_url", ""),
                "title": doc.get("title", ""),
                "category": doc.get("category", ""),
            })
            
        # Sort by similarity score descending
        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results[:top_k]

    def get_stats(self) -> dict:
        """Get index statistics."""
        return {
            "total_records": len(self.documents),
            "collection_name": "numpy_kb",
            "embedding_model": "all-MiniLM-L6-v2 (free, local)",
            "persist_dir": self.persist_dir,
            "type": "pure-python-numpy"
        }


def run_indexer(kb_records_path: str, persist_dir: str = None):
    """Load KB records and index them."""
    logger.info(f"Loading KB records from {kb_records_path}")
    with open(kb_records_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    index = KnowledgeBaseIndex(persist_dir=persist_dir)

    index.index_records(records)
    stats = index.get_stats()
    logger.info(f"Indexing complete: {json.dumps(stats, indent=2)}")

    # Run sample queries
    test_queries = [
        ("What does the Senior Software Engineer role require?", "jobs"),
        ("What benefits does TalentBridge offer?", "benefits"),
        ("How does the screening process work?", "process"),
        ("What if a candidate says the salary is too low?", "objections"),
        ("Do you offer remote work?", None),
        ("What is the notice period policy?", "qualification"),
        ("Tell me about the company culture", "company"),
    ]

    logger.info("\n" + "=" * 60)
    logger.info("RETRIEVAL TEST RESULTS")
    logger.info("=" * 60)

    for query, category in test_queries:
        results = index.search(query, top_k=3, category=category)
        logger.info(f"\nQuery: '{query}' (category={category})")
        if results:
            for r in results[:2]:
                logger.info(f"  ✅ [{r['record_id']}] {r['title']} (score={r['similarity_score']})")
                logger.info(f"     Preview: {r['content'][:150]}...")
        else:
            logger.info("  ❌ No results found")

    return index


if __name__ == "__main__":
    base_dir = os.path.join(os.path.dirname(__file__), "..")
    run_indexer(
        os.path.join(base_dir, "data", "cleaned", "kb_records.json"),
        os.path.join(base_dir, "chroma_db"),
    )
