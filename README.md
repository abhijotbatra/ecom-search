# 🛒 ShopSearch AI — Hybrid Search + RAG on Excel

> **BM25 keyword search + FAISS semantic vector search + Reciprocal Rank Fusion + RAG-powered answers** — all running on a simple Excel product catalogue.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![Streamlit](https://img.shields.io/badge/Streamlit-1.41-red)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 🧠 What This Project Does

Most e-commerce search is dumb — it only matches exact keywords. This project builds a **three-layer search engine**:

| Layer | Technology | What it solves |
|---|---|---|
| Keyword search | BM25 (rank-bm25) | Exact word matches, product names, brands |
| Semantic search | FAISS + sentence-transformers | Meaning-based matches, synonyms, intent |
| Fusion | Reciprocal Rank Fusion (RRF) | Combines both rankings fairly |
| AI answer | RAG via OpenAI / Anthropic | Generates a human-friendly recommendation |

**Example:** A user types `"something comfortable for gaming all night"` — BM25 finds nothing (no keyword overlap), but vector search finds gaming chairs, ergonomic chairs, and headsets. RAG then writes: *"For all-night gaming, the Green Soul Monster chair at ₹18,990 is your best bet — it has 4D armrests and reclines to 180°..."*

---

## 📁 Project Structure

```
ecom-search/
│
├── backend/
│   ├── search_engine.py   # BM25 + FAISS + RRF fusion engine
│   ├── rag.py             # RAG layer — prompt builder + LLM caller
│   └── api.py             # FastAPI REST endpoints
│
├── frontend/
│   └── app.py             # Streamlit UI
│
├── data/
│   ├── generate_data.py   # Generates sample_products.xlsx (50 products)
│   └── sample_products.xlsx
│
├── tests/
│   └── test_search.py     # 20+ pytest tests
│
├── .github/
│   └── workflows/ci.yml   # GitHub Actions CI
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

## ⚡ Quick Start (5 minutes)

### 1. Clone & install

```bash
git clone https://github.com/YOUR_USERNAME/ecom-search.git
cd ecom-search

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Generate sample data

```bash
python data/generate_data.py
# → creates data/sample_products.xlsx with 50 products
```

### 3. Set up environment (optional — for AI answers)

```bash
cp .env.example .env
# Edit .env and add your API key:
# OPENAI_API_KEY=sk-...
# or
# ANTHROPIC_API_KEY=sk-ant-...
```

> **No API key?** The app still works fully — it falls back to a rule-based summary. You only need a key for GPT/Claude-powered answers.

### 4. Run the Streamlit app

```bash
streamlit run frontend/app.py
# → open http://localhost:8501
```

### 5. (Optional) Run the FastAPI backend separately

```bash
uvicorn backend.api:app --reload --port 8000
# → API docs at http://localhost:8000/docs
```

---

## 🐳 Docker

```bash
# Copy and configure env
cp .env.example .env

# Run everything
docker-compose up --build

# Streamlit → http://localhost:8501
# FastAPI   → http://localhost:8000/docs
```

---

## 🔌 REST API Reference

### `POST /search` — Hybrid search

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "gaming headset under 10000",
    "top_k": 5,
    "max_price": 10000,
    "min_rating": 4.0
  }'
```

### `POST /search/rag` — Search + AI answer

```bash
curl -X POST http://localhost:8000/search/rag \
  -H "Content-Type: application/json" \
  -d '{
    "query": "best wireless headphones for travel",
    "top_k": 5,
    "llm_provider": "auto"
  }'
```

### `GET /stats` — Catalogue statistics

```bash
curl http://localhost:8000/stats
```

### `GET /categories` — All categories

```bash
curl http://localhost:8000/categories
```

### `POST /reindex` — Rebuild indices after updating Excel

```bash
curl -X POST http://localhost:8000/reindex
```

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

Tests cover:
- Tokenizer (stop words, punctuation, edge cases)
- BM25 keyword matching
- Vector semantic matching
- Price / rating / category filters
- RRF score ordering
- RAG prompt building
- Offline fallback summary

---

## 🔧 Using Your Own Excel File

Your Excel file must have these columns (extra columns are ignored):

| Column | Type | Example |
|---|---|---|
| `id` | string | P001 |
| `name` | string | Sony WH-1000XM5 |
| `brand` | string | Sony |
| `category` | string | Electronics |
| `subcategory` | string | Headphones |
| `price` | number | 29990 |
| `rating` | number | 4.8 |
| `stock` | number | 45 |
| `description` | string | Industry-leading noise cancelling... |
| `tags` | string | wireless bluetooth noise-cancelling |

Then update `.env`:
```
EXCEL_PATH=data/your_file.xlsx
```

After updating the file, call `POST /reindex` or restart the app.

---

## 🏗️ Architecture Deep Dive

### How BM25 works here

Each product's `name + brand + category + description + tags` is concatenated into one text document. At startup, all 50 documents are tokenized and indexed into a BM25Okapi model. At query time, the query is tokenized, scores are computed for all documents, and the top-K are returned.

**Strength:** Very fast, great for exact brand/model name queries.
**Weakness:** Vocabulary mismatch — "comfortable chair" won't match "ergonomic seat".

### How vector search works here

The same concatenated text is passed through `all-MiniLM-L6-v2` (a 384-dimensional sentence transformer) to produce dense embeddings. These are stored in a FAISS `IndexFlatIP` (inner product = cosine similarity after L2 normalisation). At query time, the query is also embedded and the nearest neighbours are retrieved via ANN search.

**Strength:** Finds semantically similar products even with zero word overlap.
**Weakness:** Less precise for exact model names / numbers.

### How RRF fusion works

```
RRF_score(doc) = Σ  1 / (60 + rank_i)
```

Both ranked lists (BM25 and vector) are merged using this formula. A document appearing in position 1 on both lists scores `1/61 + 1/61 ≈ 0.0328`. A document appearing only on one list scores at most `1/61 ≈ 0.0164`. The constant `60` prevents top-ranked documents from dominating too much. This approach requires no score normalisation — it only cares about rank positions.

### How RAG works

1. Top-5 retrieved products are serialised into a structured context block
2. A system prompt instructs the LLM to answer only from the provided context
3. The LLM generates a grounded recommendation (no hallucination of products)
4. If no API key, a rule-based summary is returned instead

---

## 🚀 Deployment Options

### Streamlit Cloud (free)
1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo → set `frontend/app.py` as the main file
4. Add secrets in the Streamlit dashboard

### Railway / Render (free tier)
```bash
# Set start command to:
streamlit run frontend/app.py --server.port $PORT --server.address 0.0.0.0
```

### Self-hosted VPS
```bash
docker-compose up -d
```

---

## 🛣️ What to Build Next

| Feature | How |
|---|---|
| Upload your own Excel via UI | `st.file_uploader` + `/reindex` |
| Re-ranking with cross-encoder | Add `cross-encoder/ms-marco-MiniLM` |
| Query spell correction | `pyspellchecker` |
| Multi-language support | `paraphrase-multilingual-MiniLM-L12-v2` |
| Persistent vector DB | Replace FAISS with Qdrant or Pinecone |
| User analytics | Log queries + clicks to SQLite |
| A/B test BM25 vs hybrid | Track precision@K |

---

## 📄 License

MIT — use freely, build on top, give credit.
