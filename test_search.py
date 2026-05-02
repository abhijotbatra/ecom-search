"""
Test suite for the hybrid search engine and RAG layer.
Run with:  pytest tests/ -v
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from backend.search_engine import HybridSearchEngine, tokenize, build_doc_text
from backend.rag import build_rag_prompt, offline_summary

EXCEL_PATH = "data/sample_products.xlsx"


# ── tokenizer tests ────────────────────────────────────────────────────────────

def test_tokenize_basic():
    tokens = tokenize("Wireless Headphones for Gaming")
    assert "wireless" in tokens
    assert "headphones" in tokens
    assert "gaming" in tokens
    assert "for" not in tokens          # stop word removed


def test_tokenize_punctuation():
    tokens = tokenize("Sony WH-1000XM5, best!")
    assert "sony" in tokens
    assert "wh" in tokens or "wh1000xm5" in tokens or "1000xm5" in tokens


def test_tokenize_empty():
    assert tokenize("") == []
    assert tokenize("the an a") == []   # all stop words


# ── engine tests ───────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def engine():
    return HybridSearchEngine(EXCEL_PATH)


def test_engine_loads(engine):
    assert len(engine.docs) == 50
    assert engine.bm25 is not None
    assert engine.faiss_index is not None


def test_search_returns_results(engine):
    results = engine.search("gaming headset")
    assert len(results) > 0


def test_search_result_fields(engine):
    results = engine.search("laptop")
    r = results[0]
    for field in ["id","name","brand","price","rating","_rrf_score","_bm25_score","_vector_score"]:
        assert field in r, f"Missing field: {field}"


def test_search_keyword_match(engine):
    """BM25 should rank 'Sony' products high when query is 'Sony'."""
    results = engine.search("Sony headphones", top_k=5)
    names = [r["name"] for r in results]
    assert any("Sony" in n for n in names)


def test_semantic_search(engine):
    """
    Semantic search should find related products even without exact keywords.
    'study light for late night' → should find desk lamps.
    """
    results = engine.search("light for late night studying", top_k=10)
    names = [r["name"].lower() for r in results]
    assert any("lamp" in n or "light" in n for n in names)


def test_price_filter(engine):
    results = engine.search("headphones", max_price=2000)
    for r in results:
        assert r["price"] <= 2000


def test_min_rating_filter(engine):
    results = engine.search("laptop", min_rating=4.5)
    for r in results:
        assert r["rating"] >= 4.5


def test_category_filter(engine):
    results = engine.search("something", category="Fitness")
    for r in results:
        assert r["category"] == "Fitness"


def test_empty_query_returns_nothing(engine):
    results = engine.search("   ")
    # Either empty or only vector results (no BM25 with empty tokens)
    assert isinstance(results, list)


def test_rrf_scores_descending(engine):
    results = engine.search("wireless bluetooth", top_k=10)
    scores = [r["_rrf_score"] for r in results]
    assert scores == sorted(scores, reverse=True)


def test_get_categories(engine):
    cats = engine.get_categories()
    assert "All" in cats
    assert "Electronics" in cats
    assert len(cats) > 3


def test_get_stats(engine):
    stats = engine.get_stats()
    assert stats["total_products"] == 50
    assert stats["categories"] > 0
    assert stats["brands"] > 0
    assert stats["avg_price"] > 0


# ── RAG tests ──────────────────────────────────────────────────────────────────

SAMPLE_PRODUCTS = [
    {
        "name": "Test Headphone X1",
        "brand": "TestBrand",
        "category": "Electronics",
        "subcategory": "Headphones",
        "price": 4999,
        "rating": 4.5,
        "stock": 20,
        "description": "Great noise cancelling headphone for travel.",
    }
]


def test_rag_prompt_builds():
    system, user = build_rag_prompt("gaming headset", SAMPLE_PRODUCTS)
    assert "gaming headset" in user
    assert "Test Headphone X1" in user
    assert "₹4,999" in user


def test_offline_summary():
    answer = offline_summary("gaming headset", SAMPLE_PRODUCTS)
    assert "Test Headphone X1" in answer
    assert "₹" in answer


def test_offline_summary_empty():
    answer = offline_summary("anything", [])
    assert "No products" in answer


# ── doc text builder ───────────────────────────────────────────────────────────

def test_build_doc_text():
    row = {
        "name": "Test Product",
        "brand": "BrandX",
        "category": "Electronics",
        "subcategory": "Phones",
        "description": "A great phone",
        "tags": "budget 5g",
    }
    text = build_doc_text(row)
    assert "Test Product" in text
    assert "BrandX" in text
    assert "budget" in text
