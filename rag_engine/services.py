"""
RAG Engine Services — LlamaIndex + FAISS + SentenceTransformers
Provides semantic retrieval of pricing intelligence for AI context injection.
"""

import os
import json
import logging
import hashlib
from pathlib import Path

from django.conf import settings

logger = logging.getLogger(__name__)

# Singleton caches to avoid re-initialization
_index = None
_embed_model = None
_index_hash = None


def _get_index_dir():
    """Get the directory for storing FAISS index files."""
    index_dir = Path(settings.BASE_DIR) / 'rag_engine' / 'faiss_index'
    index_dir.mkdir(parents=True, exist_ok=True)
    return str(index_dir)


def _get_knowledge_hash():
    """Hash the knowledge base to detect changes and trigger re-indexing."""
    from rag_engine.knowledge_base import PRICING_KNOWLEDGE
    content = json.dumps(PRICING_KNOWLEDGE, sort_keys=True)
    return hashlib.md5(content.encode()).hexdigest()


def _get_embed_model():
    """Get or create the SentenceTransformer embedding model (cached singleton)."""
    global _embed_model
    if _embed_model is not None:
        return _embed_model

    try:
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding
        _embed_model = HuggingFaceEmbedding(model_name="all-MiniLM-L6-v2")
        logger.info("SentenceTransformer embedding model loaded: all-MiniLM-L6-v2")
        return _embed_model
    except ImportError:
        logger.warning("llama_index.embeddings.huggingface not available, trying sentence_transformers directly")
        try:
            from sentence_transformers import SentenceTransformer
            # Wrap in a simple adapter
            _embed_model = _SentenceTransformerAdapter("all-MiniLM-L6-v2")
            return _embed_model
        except ImportError:
            logger.error("Neither llama_index HuggingFace embeddings nor sentence_transformers available")
            return None


class _SentenceTransformerAdapter:
    """Minimal adapter wrapping SentenceTransformer for direct use when LlamaIndex HF embeddings unavailable."""

    def __init__(self, model_name):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name

    def get_text_embedding(self, text):
        return self.model.encode(text).tolist()

    def get_text_embedding_batch(self, texts):
        return self.model.encode(texts).tolist()

    def get_query_embedding(self, query):
        return self.model.encode(query).tolist()


def _build_documents():
    """Convert knowledge base entries into LlamaIndex Documents."""
    from rag_engine.knowledge_base import PRICING_KNOWLEDGE

    try:
        from llama_index.core import Document
    except ImportError:
        from llama_index.core.schema import Document

    documents = []
    for entry in PRICING_KNOWLEDGE:
        # Create a rich text representation for embedding
        text = (
            f"Item: {entry['item']}\n"
            f"Category: {entry['category']}\n"
            f"City: {entry['city']}\n"
            f"Normal Price Range: {entry['normal_range']}\n"
            f"Tourist Area Price Range: {entry['tourist_range']}\n"
            f"Details: {entry['description']}"
        )
        metadata = {
            "item": entry["item"],
            "category": entry["category"],
            "city": entry["city"],
            "normal_range": entry["normal_range"],
            "tourist_range": entry["tourist_range"],
        }
        documents.append(Document(text=text, metadata=metadata))

    return documents


def build_index(force=False):
    """Build or load the FAISS vector index from the knowledge base."""
    global _index, _index_hash

    current_hash = _get_knowledge_hash()
    index_dir = _get_index_dir()
    hash_file = os.path.join(index_dir, 'kb_hash.txt')

    # Check if index already cached in memory with same hash
    if _index is not None and _index_hash == current_hash and not force:
        return _index

    # Check if saved index exists on disk and matches current knowledge base
    saved_hash = None
    if os.path.exists(hash_file):
        with open(hash_file, 'r') as f:
            saved_hash = f.read().strip()

    faiss_path = os.path.join(index_dir, 'default__vector_store.json')

    if not force and saved_hash == current_hash and os.path.exists(faiss_path):
        # Load existing index from disk
        try:
            embed_model = _get_embed_model()
            if embed_model is None:
                return None

            from llama_index.core import StorageContext, load_index_from_storage, Settings

            Settings.embed_model = embed_model

            storage_context = StorageContext.from_defaults(persist_dir=index_dir)
            _index = load_index_from_storage(storage_context)
            _index_hash = current_hash
            logger.info("FAISS index loaded from disk")
            return _index
        except Exception as e:
            logger.warning(f"Failed to load saved index, rebuilding: {e}")

    # Build fresh index
    try:
        embed_model = _get_embed_model()
        if embed_model is None:
            logger.error("Cannot build index: no embedding model available")
            return None

        from llama_index.core import VectorStoreIndex, Settings

        Settings.embed_model = embed_model

        documents = _build_documents()
        logger.info(f"Building FAISS index from {len(documents)} documents...")

        _index = VectorStoreIndex.from_documents(documents)

        # Persist to disk
        _index.storage_context.persist(persist_dir=index_dir)
        with open(hash_file, 'w') as f:
            f.write(current_hash)

        _index_hash = current_hash
        logger.info(f"FAISS index built and saved ({len(documents)} documents)")
        return _index

    except Exception as e:
        logger.error(f"Failed to build RAG index: {e}")
        return None


def retrieve_context(query, city=None, top_k=5):
    """
    Retrieve relevant pricing context for a query using semantic search.

    Args:
        query: The user's price query (e.g., "tea price in Kochi")
        city: Optional city to boost location-specific results
        top_k: Number of top results to retrieve

    Returns:
        List of dicts with retrieved pricing intelligence, or empty list on failure.
    """
    index = build_index()
    if index is None:
        return _fallback_keyword_search(query, city)

    try:
        # Build a rich query string incorporating city context
        search_query = query
        if city:
            search_query = f"{query} in {city}"

        retriever = index.as_retriever(similarity_top_k=top_k)
        nodes = retriever.retrieve(search_query)

        results = []
        for node in nodes:
            # Only include reasonably relevant results (similarity > 0.3)
            if hasattr(node, 'score') and node.score is not None and node.score < 0.3:
                continue

            results.append({
                "text": node.text,
                "score": round(node.score, 4) if hasattr(node, 'score') and node.score else 0,
                "metadata": node.metadata if hasattr(node, 'metadata') else {},
            })

        # If city was specified, boost city-specific results
        if city and results:
            city_lower = city.lower()
            results.sort(
                key=lambda r: (
                    # City match gets highest priority
                    2 if r.get('metadata', {}).get('city', '').lower() == city_lower else
                    1 if r.get('metadata', {}).get('city', '').lower() == 'general' else 0,
                    r.get('score', 0)
                ),
                reverse=True
            )

        logger.info(f"RAG retrieved {len(results)} results for query: '{search_query}'")
        return results[:top_k]

    except Exception as e:
        logger.error(f"RAG retrieval failed: {e}")
        return _fallback_keyword_search(query, city)


def _fallback_keyword_search(query, city=None):
    """Simple keyword-based fallback when vector search is unavailable."""
    from rag_engine.knowledge_base import PRICING_KNOWLEDGE

    query_lower = query.lower()
    city_lower = city.lower() if city else ""

    results = []
    for entry in PRICING_KNOWLEDGE:
        score = 0
        item_lower = entry['item'].lower()
        cat_lower = entry['category'].lower()
        desc_lower = entry['description'].lower()
        entry_city = entry['city'].lower()

        # Check item name match
        query_words = query_lower.split()
        for word in query_words:
            if len(word) > 2:
                if word in item_lower:
                    score += 3
                if word in desc_lower:
                    score += 1
                if word in cat_lower:
                    score += 2

        # City match bonus
        if city_lower and (entry_city == city_lower or entry_city == 'general'):
            score += 2

        if score > 0:
            text = (
                f"Item: {entry['item']}\n"
                f"Category: {entry['category']}\n"
                f"City: {entry['city']}\n"
                f"Normal Price Range: {entry['normal_range']}\n"
                f"Tourist Area Price Range: {entry['tourist_range']}\n"
                f"Details: {entry['description']}"
            )
            results.append({
                "text": text,
                "score": score,
                "metadata": {
                    "item": entry["item"],
                    "category": entry["category"],
                    "city": entry["city"],
                    "normal_range": entry["normal_range"],
                    "tourist_range": entry["tourist_range"],
                },
            })

    results.sort(key=lambda r: r['score'], reverse=True)
    return results[:5]


def format_context_for_prompt(retrieved_results):
    """
    Format retrieved RAG results into a clean context block for AI prompt injection.

    Returns a string that can be directly inserted into Groq prompts.
    """
    if not retrieved_results:
        return ""

    lines = ["=== RETRIEVED PRICING INTELLIGENCE (use this data for accurate analysis) ==="]

    for i, result in enumerate(retrieved_results[:4], 1):
        meta = result.get('metadata', {})
        lines.append(f"\n--- Reference #{i} (Relevance: {result.get('score', 'N/A')}) ---")
        if meta.get('item'):
            lines.append(f"Item: {meta['item']}")
        if meta.get('city'):
            lines.append(f"City: {meta['city']}")
        if meta.get('normal_range'):
            lines.append(f"Normal Price Range: {meta['normal_range']}")
        if meta.get('tourist_range'):
            lines.append(f"Tourist Area Range: {meta['tourist_range']}")
        # Include full text for detailed context
        text = result.get('text', '')
        if 'Details:' in text:
            details = text.split('Details:')[1].strip()
            lines.append(f"Details: {details}")

    lines.append("\n=== END OF PRICING INTELLIGENCE ===")
    lines.append("Use the above data to ground your analysis. If the queried item closely matches a reference, use those ranges.")

    return "\n".join(lines)


def get_rag_context(query, city=None, top_k=4):
    """
    High-level function: retrieve + format context for AI prompt injection.
    This is the main entry point used by ai_engine/services.py.

    Args:
        query: Item/service description
        city: City/location name
        top_k: Number of results to retrieve

    Returns:
        Formatted context string ready for prompt injection, or empty string.
    """
    try:
        results = retrieve_context(query, city=city, top_k=top_k)
        return format_context_for_prompt(results)
    except Exception as e:
        logger.error(f"RAG context generation failed: {e}")
        return ""
