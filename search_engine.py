"""
Hybrid Search Engine
====================
BM25 (keyword) + TF-IDF vectors in FAISS (semantic proxy) + Reciprocal Rank Fusion

Works in ALL environments with zero torch / GPU dependency.
When sentence-transformers IS available (production), swap _HashEmbed for it.

Flow:
  Excel -> parse -> build BM25 index + FAISS TF-IDF index
  Query -> tokenize -> BM25 top-K + Vector top-K -> RRF merge -> top results
"""

import re
import pickle
import logging
import hashlib
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import faiss
from rank_bm25 import BM25Okapi

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger(__name__)

# constants
EMBED_DIM        = 512
INDEX_CACHE_DIR  = Path(".cache")
BM25_CACHE       = INDEX_CACHE_DIR / "bm25.pkl"
FAISS_CACHE      = INDEX_CACHE_DIR / "faiss.index"
DOCS_CACHE       = INDEX_CACHE_DIR / "docs.pkl"
VOCAB_CACHE      = INDEX_CACHE_DIR / "vocab.pkl"

STOP_WORDS = {
    "a","an","the","is","in","it","of","to","and","or","for",
    "with","on","at","by","from","this","that","are","was","be",
    "as","its","into","has","have","had","not","but","what","how",
    "which","who","do","does","did","will","would","can","could",
    "should","may","might","shall","very","just","also","than",
    "then","so","if","more","any","all","one","i","me","my","we",
}


def tokenize(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    tokens = text.split()
    return [t for t in tokens if t not in STOP_WORDS and len(t) > 1]


def build_doc_text(row):
    parts = [
        str(row.get("name", "")),
        str(row.get("brand", "")),
        str(row.get("category", "")),
        str(row.get("subcategory", "")),
        str(row.get("description", "")),
        str(row.get("tags", "")),
    ]
    return " ".join(p for p in parts if p and p != "nan")


class TFIDFVectoriser:
    """
    Lightweight TF-IDF vectoriser producing fixed-dim dense vectors
    via vocabulary hashing. No external ML library needed.
    """

    def __init__(self, dim=EMBED_DIM):
        self.dim = dim
        self.idf = {}
        self._vocab = {}

    def _tok2idx(self, token):
        if token not in self._vocab:
            h = int(hashlib.md5(token.encode()).hexdigest(), 16)
            self._vocab[token] = h % self.dim
        return self._vocab[token]

    def fit(self, corpus):
        n = len(corpus)
        df = {}
        for tokens in corpus:
            for t in set(tokens):
                df[t] = df.get(t, 0) + 1
        self.idf = {t: np.log((n + 1) / (cnt + 1)) + 1 for t, cnt in df.items()}
        return self

    def transform(self, corpus):
        mat = np.zeros((len(corpus), self.dim), dtype=np.float32)
        for i, tokens in enumerate(corpus):
            if not tokens:
                continue
            tf = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            total = len(tokens)
            for t, cnt in tf.items():
                score = (cnt / total) * self.idf.get(t, 1.0)
                mat[i, self._tok2idx(t)] += score
            norm = np.linalg.norm(mat[i])
            if norm > 0:
                mat[i] /= norm
        return mat

    def transform_query(self, tokens):
        return self.transform([tokens])


class HybridSearchEngine:
    """
    Three-stage retrieval:
      1. BM25  - exact/keyword relevance
      2. FAISS - TF-IDF vector cosine similarity
      3. RRF   - rank-level fusion of both
    """

    def __init__(self, excel_path, force_reindex=False):
        self.excel_path   = Path(excel_path)
        self.docs         = []
        self.bm25         = None
        self.faiss_index  = None
        self.vectoriser   = TFIDFVectoriser(EMBED_DIM)

        INDEX_CACHE_DIR.mkdir(exist_ok=True)

        if not force_reindex and self._cache_valid():
            log.info("Loading indices from cache...")
            self._load_cache()
        else:
            log.info("Building indices from Excel...")
            self._build_indices()
            self._save_cache()

        log.info(f"Engine ready — {len(self.docs)} products indexed.")

    def _build_indices(self):
        df = pd.read_excel(self.excel_path).fillna("")
        self.docs = df.to_dict(orient="records")

        corpus_texts = [build_doc_text(d) for d in self.docs]
        tokenized    = [tokenize(t) for t in corpus_texts]

        # BM25
        self.bm25 = BM25Okapi(tokenized)

        # TF-IDF -> FAISS
        log.info("Fitting TF-IDF vectoriser...")
        self.vectoriser.fit(tokenized)
        embeddings = self.vectoriser.transform(tokenized)
        faiss.normalize_L2(embeddings)

        self.faiss_index = faiss.IndexFlatIP(EMBED_DIM)
        self.faiss_index.add(embeddings)
        log.info(f"FAISS: {self.faiss_index.ntotal} vectors @ {EMBED_DIM}d")

    def _cache_valid(self):
        needed = [BM25_CACHE, FAISS_CACHE, DOCS_CACHE, VOCAB_CACHE]
        if not all(p.exists() for p in needed):
            return False
        return self.excel_path.stat().st_mtime <= DOCS_CACHE.stat().st_mtime

    def _save_cache(self):
        with open(BM25_CACHE,  "wb") as f: pickle.dump(self.bm25,        f)
        with open(DOCS_CACHE,  "wb") as f: pickle.dump(self.docs,         f)
        with open(VOCAB_CACHE, "wb") as f: pickle.dump(self.vectoriser,   f)
        faiss.write_index(self.faiss_index, str(FAISS_CACHE))
        log.info("Indices saved to .cache/")

    def _load_cache(self):
        with open(BM25_CACHE,  "rb") as f: self.bm25        = pickle.load(f)
        with open(DOCS_CACHE,  "rb") as f: self.docs         = pickle.load(f)
        with open(VOCAB_CACHE, "rb") as f: self.vectoriser   = pickle.load(f)
        self.faiss_index = faiss.read_index(str(FAISS_CACHE))

    def _bm25_search(self, query, top_k):
        tokens = tokenize(query)
        if not tokens:
            return []
        scores = self.bm25.get_scores(tokens)
        ranked = np.argsort(scores)[::-1][:top_k]
        return [(int(i), float(scores[i])) for i in ranked if scores[i] > 0]

    def _vector_search(self, query, top_k):
        tokens = tokenize(query)
        if not tokens:
            return []
        q_vec = self.vectoriser.transform_query(tokens).astype("float32")
        faiss.normalize_L2(q_vec)
        scores, indices = self.faiss_index.search(q_vec, top_k)
        return [(int(idx), float(score))
                for idx, score in zip(indices[0], scores[0]) if idx >= 0]

    @staticmethod
    def _rrf(ranked_lists, k=60):
        scores = {}
        for ranked in ranked_lists:
            for rank, (doc_id, _) in enumerate(ranked, start=1):
                scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)

    def search(self, query, top_k=8, min_price=None, max_price=None,
               min_rating=None, category=None):
        fetch_k = min(top_k * 4, len(self.docs))

        bm25_results   = self._bm25_search(query, fetch_k)
        vector_results = self._vector_search(query, fetch_k)
        fused          = self._rrf([bm25_results, vector_results])

        results = []
        for doc_id, rrf_score in fused:
            doc    = self.docs[doc_id].copy()
            price  = float(doc.get("price",  0))
            rating = float(doc.get("rating", 0))
            cat    = str(doc.get("category", ""))

            if min_price  is not None and price  < min_price:  continue
            if max_price  is not None and price  > max_price:  continue
            if min_rating is not None and rating < min_rating: continue
            if category and category != "All" and cat != category: continue

            b_rank  = next((r+1 for r,(i,_) in enumerate(bm25_results)   if i==doc_id), None)
            v_rank  = next((r+1 for r,(i,_) in enumerate(vector_results) if i==doc_id), None)
            b_score = next((s   for i,s   in bm25_results   if i==doc_id), 0.0)
            v_score = next((s   for i,s   in vector_results if i==doc_id), 0.0)

            doc["_rrf_score"]    = round(rrf_score, 6)
            doc["_bm25_score"]   = round(b_score,   4)
            doc["_vector_score"] = round(v_score,   4)
            doc["_bm25_rank"]    = b_rank
            doc["_vector_rank"]  = v_rank

            results.append(doc)
            if len(results) >= top_k:
                break

        return results

    def get_categories(self):
        cats = sorted({d.get("category","") for d in self.docs if d.get("category","")})
        return ["All"] + cats

    def get_stats(self):
        df = pd.DataFrame(self.docs)
        return {
            "total_products": len(self.docs),
            "categories":     int(df["category"].nunique()),
            "brands":         int(df["brand"].nunique()),
            "avg_price":      round(float(df["price"].mean()), 2),
            "avg_rating":     round(float(df["rating"].mean()), 2),
        }
