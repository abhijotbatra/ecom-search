"""
FastAPI Backend
===============
REST API that exposes the hybrid search engine + RAG layer.

Endpoints:
  GET  /                  → health check
  GET  /stats             → catalogue stats
  GET  /categories        → list of categories
  POST /search            → hybrid search
  POST /search/rag        → hybrid search + RAG answer
  POST /reindex           → force rebuild indices

Run with:
  uvicorn backend.api:app --reload --port 8000
"""

import os
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.search_engine import HybridSearchEngine
from backend.rag import generate_rag_answer

# ── config ─────────────────────────────────────────────────────────────────────
EXCEL_PATH = os.getenv("EXCEL_PATH", "data/sample_products.xlsx")

engine: Optional[HybridSearchEngine] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine
    engine = HybridSearchEngine(EXCEL_PATH)
    yield
    # cleanup if needed
    engine = None


app = FastAPI(
    title="E-Commerce Hybrid Search API",
    description="BM25 + Vector Search + RAG for product discovery",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── request / response models ──────────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=300, example="wireless headphones for gaming")
    top_k: int = Field(default=8, ge=1, le=20)
    min_price: Optional[float] = Field(default=None, ge=0)
    max_price: Optional[float] = Field(default=None, ge=0)
    min_rating: Optional[float] = Field(default=None, ge=0, le=5)
    category: Optional[str] = Field(default=None)


class RAGSearchRequest(SearchRequest):
    llm_provider: str = Field(default="auto", description="auto | openai | anthropic | offline")


class ProductResult(BaseModel):
    id: str
    name: str
    brand: str
    category: str
    subcategory: str
    price: float
    rating: float
    stock: int
    description: str
    tags: str
    _rrf_score: float
    _bm25_score: float
    _vector_score: float
    _bm25_rank: Optional[int]
    _vector_rank: Optional[int]


class SearchResponse(BaseModel):
    query: str
    total_results: int
    results: list[dict]


class RAGSearchResponse(SearchResponse):
    rag_answer: str
    llm_provider: str
    grounded: bool


# ── endpoints ──────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "message": "E-Commerce Hybrid Search API is running"}


@app.get("/stats", tags=["Catalogue"])
def get_stats():
    """Catalogue statistics."""
    if not engine:
        raise HTTPException(503, "Engine not ready")
    return engine.get_stats()


@app.get("/categories", tags=["Catalogue"])
def get_categories():
    """All available product categories."""
    if not engine:
        raise HTTPException(503, "Engine not ready")
    return {"categories": engine.get_categories()}


@app.post("/search", response_model=SearchResponse, tags=["Search"])
def search(req: SearchRequest):
    """
    Hybrid BM25 + Vector search with optional filters.
    Returns ranked product list with score metadata.
    """
    if not engine:
        raise HTTPException(503, "Engine not ready")

    results = engine.search(
        query=req.query,
        top_k=req.top_k,
        min_price=req.min_price,
        max_price=req.max_price,
        min_rating=req.min_rating,
        category=req.category,
    )

    return SearchResponse(
        query=req.query,
        total_results=len(results),
        results=results,
    )


@app.post("/search/rag", response_model=RAGSearchResponse, tags=["Search"])
def search_with_rag(req: RAGSearchRequest):
    """
    Hybrid search + RAG-generated natural language answer.
    Requires OPENAI_API_KEY or ANTHROPIC_API_KEY for full LLM response.
    Falls back to rule-based summary if no key is set.
    """
    if not engine:
        raise HTTPException(503, "Engine not ready")

    results = engine.search(
        query=req.query,
        top_k=req.top_k,
        min_price=req.min_price,
        max_price=req.max_price,
        min_rating=req.min_rating,
        category=req.category,
    )

    rag = generate_rag_answer(
        query=req.query,
        products=results,
        llm_provider=req.llm_provider,
    )

    return RAGSearchResponse(
        query=req.query,
        total_results=len(results),
        results=results,
        rag_answer=rag["answer"],
        llm_provider=rag["provider"],
        grounded=rag["grounded"],
    )


@app.post("/reindex", tags=["Admin"])
def reindex():
    """Force rebuild of all search indices (call after updating Excel)."""
    global engine
    engine = HybridSearchEngine(EXCEL_PATH, force_reindex=True)
    return {"status": "ok", "message": f"Reindexed {engine.get_stats()['total_products']} products"}
