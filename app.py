"""
E-Commerce Hybrid Search — Streamlit Frontend
=============================================
Run with:
  streamlit run frontend/app.py
"""

import sys
import os
import time
from pathlib import Path

# Add project root to path so backend imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

from backend.search_engine import HybridSearchEngine
from backend.rag import generate_rag_answer

# ── page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ShopSearch AI",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* Main search bar */
  .stTextInput > div > div > input {
    font-size: 18px !important;
    padding: 12px 16px !important;
    border-radius: 10px !important;
  }
  /* Product cards */
  .product-card {
    background: #ffffff;
    border: 1px solid #e8e8e8;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 12px;
    transition: box-shadow 0.2s;
  }
  .product-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
  .product-name { font-size: 15px; font-weight: 600; color: #1a1a1a; margin-bottom: 4px; }
  .product-brand { font-size: 12px; color: #888; margin-bottom: 8px; }
  .product-price { font-size: 20px; font-weight: 700; color: #e44d26; }
  .product-rating { font-size: 13px; color: #f39c12; }
  .product-desc { font-size: 12px; color: #555; margin-top: 8px; line-height: 1.5; }
  .score-badge {
    display: inline-block;
    background: #f0f2ff;
    color: #4a4aff;
    font-size: 10px;
    padding: 2px 7px;
    border-radius: 20px;
    margin-right: 4px;
  }
  /* RAG answer box */
  .rag-box {
    background: linear-gradient(135deg, #667eea11, #764ba211);
    border: 1px solid #667eea33;
    border-radius: 12px;
    padding: 18px 20px;
    margin-bottom: 20px;
  }
  .rag-title { font-size: 14px; font-weight: 600; color: #667eea; margin-bottom: 8px; }
  /* Stat cards */
  .stat-card {
    background: #f8f9ff;
    border-radius: 10px;
    padding: 12px 16px;
    text-align: center;
  }
  .stat-value { font-size: 22px; font-weight: 700; color: #333; }
  .stat-label { font-size: 11px; color: #888; margin-top: 2px; }
  /* Tag pills */
  .tag-pill {
    display: inline-block;
    background: #eef0ff;
    color: #5557aa;
    font-size: 10px;
    padding: 2px 8px;
    border-radius: 20px;
    margin: 2px;
  }
  /* Hide streamlit default elements */
  #MainMenu {visibility: hidden;}
  footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ── engine loading (cached) ────────────────────────────────────────────────────

@st.cache_resource(show_spinner="Building search indices… (first run only)")
def load_engine():
    excel_path = os.getenv("EXCEL_PATH", "data/sample_products.xlsx")
    return HybridSearchEngine(excel_path)


engine = load_engine()


# ── helpers ────────────────────────────────────────────────────────────────────

def stars(rating: float) -> str:
    full = int(rating)
    half = 1 if rating - full >= 0.5 else 0
    return "★" * full + ("½" if half else "") + "☆" * (5 - full - half)


def fmt_price(p: float) -> str:
    return f"₹{p:,.0f}"


def render_product_card(p: dict, rank: int):
    in_stock = int(p.get("stock", 0)) > 0
    stock_label = f"✅ {p['stock']} in stock" if in_stock else "❌ Out of stock"

    tags_html = " ".join(
        f'<span class="tag-pill">{t}</span>'
        for t in str(p.get("tags", "")).split()[:6]
    )

    bm25_r  = p.get("_bm25_rank",  "—")
    vec_r   = p.get("_vector_rank","—")
    rrf_s   = p.get("_rrf_score",  0)

    st.markdown(f"""
    <div class="product-card">
      <div style="display:flex; justify-content:space-between; align-items:flex-start">
        <div style="flex:1">
          <div class="product-name">#{rank} {p['name']}</div>
          <div class="product-brand">{p['brand']} · {p['category']} › {p['subcategory']}</div>
        </div>
        <div style="text-align:right">
          <div class="product-price">{fmt_price(p['price'])}</div>
          <div class="product-rating">{stars(p['rating'])} {p['rating']}</div>
        </div>
      </div>
      <div class="product-desc">{p.get('description','')[:200]}…</div>
      <div style="margin-top:8px">{tags_html}</div>
      <div style="margin-top:10px; display:flex; align-items:center; gap:8px; flex-wrap:wrap">
        <span style="font-size:12px; color:#666">{stock_label}</span>
        <span class="score-badge">BM25 rank #{bm25_r}</span>
        <span class="score-badge">Vector rank #{vec_r}</span>
        <span class="score-badge">RRF {rrf_s:.4f}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)


def render_rag_answer(answer: str, provider: str, grounded: bool, query: str):
    icon = "🤖" if grounded else "📋"
    provider_label = {"openai": "GPT-4o", "anthropic": "Claude", "offline": "Rule-based"}.get(provider, provider)
    st.markdown(f"""
    <div class="rag-box">
      <div class="rag-title">{icon} AI Shopping Assistant  <span style="font-size:10px;color:#aaa;font-weight:400">via {provider_label}</span></div>
      <div style="font-size:14px; color:#333; line-height:1.7">{answer.replace(chr(10),'<br>')}</div>
    </div>
    """, unsafe_allow_html=True)


# ── sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🛒 ShopSearch AI")
    st.markdown("*Hybrid BM25 + Vector + RAG*")
    st.divider()

    # Stats
    stats = engine.get_stats()
    cols = st.columns(2)
    with cols[0]:
        st.markdown(f'<div class="stat-card"><div class="stat-value">{stats["total_products"]}</div><div class="stat-label">Products</div></div>', unsafe_allow_html=True)
    with cols[1]:
        st.markdown(f'<div class="stat-card"><div class="stat-value">{stats["brands"]}</div><div class="stat-label">Brands</div></div>', unsafe_allow_html=True)
    st.markdown("")

    st.markdown("### Filters")

    category = st.selectbox("Category", engine.get_categories())

    price_range = st.slider(
        "Price range (₹)",
        min_value=0, max_value=150000,
        value=(0, 150000), step=500,
        format="₹%d",
    )

    min_rating = st.slider("Minimum rating", 0.0, 5.0, 3.5, 0.1)

    top_k = st.slider("Results to show", 3, 15, 8)

    st.divider()
    st.markdown("### AI Answer")
    enable_rag = st.toggle("Enable AI summary", value=True)

    llm_provider = "auto"
    if enable_rag:
        has_openai    = bool(os.getenv("OPENAI_API_KEY"))
        has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))

        if has_openai or has_anthropic:
            options = []
            if has_openai:    options.append("openai")
            if has_anthropic: options.append("anthropic")
            options.append("offline")
            llm_provider = st.selectbox("LLM provider", options)
            st.success(f"{'🔑' if llm_provider != 'offline' else '📋'} Using {llm_provider}")
        else:
            st.warning("No API key found.\nAdd OPENAI_API_KEY or ANTHROPIC_API_KEY to `.env` for smart AI answers.\n\nUsing rule-based summary for now.")
            llm_provider = "offline"

    st.divider()
    if st.button("🔄 Reindex catalogue", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()


# ── main area ──────────────────────────────────────────────────────────────────

st.markdown("# 🛒 ShopSearch AI")
st.markdown("Search using natural language — powered by BM25 + Semantic Search + RAG")

# Search bar
query = st.text_input(
    "",
    placeholder='Try: "wireless headphones for gaming under 10000" or "something for late night studying"',
    label_visibility="collapsed",
)

# Example queries
st.markdown("**Try these:**")
example_cols = st.columns(4)
examples = [
    "noise cancelling headphones",
    "budget phone under 25000",
    "gaming setup with RGB",
    "home workout equipment",
    "something for a student studying late night",
    "best laptop for programming",
    "healthy cooking appliances",
    "waterproof earphones for gym",
]
for i, ex in enumerate(examples):
    with example_cols[i % 4]:
        if st.button(ex, use_container_width=True, key=f"ex_{i}"):
            query = ex

st.divider()

# ── search execution ───────────────────────────────────────────────────────────

if query:
    start = time.perf_counter()

    with st.spinner("Searching…"):
        results = engine.search(
            query=query,
            top_k=top_k,
            min_price=float(price_range[0]) if price_range[0] > 0 else None,
            max_price=float(price_range[1]) if price_range[1] < 150000 else None,
            min_rating=float(min_rating) if min_rating > 0 else None,
            category=category if category != "All" else None,
        )

    elapsed = time.perf_counter() - start

    # ── RAG answer ─────────────────────────────────────────────────────────────
    if enable_rag and results:
        with st.spinner("Generating AI recommendation…"):
            rag = generate_rag_answer(query, results, llm_provider)
        render_rag_answer(rag["answer"], rag["provider"], rag["grounded"], query)

    # ── result header ──────────────────────────────────────────────────────────
    c1, c2, c3 = st.columns([3, 2, 2])
    with c1:
        st.markdown(f"### Found **{len(results)}** results for *\"{query}\"*")
    with c2:
        st.markdown(f"<div style='text-align:right; color:#888; padding-top:8px; font-size:13px'>⚡ {elapsed*1000:.0f} ms</div>", unsafe_allow_html=True)
    with c3:
        view_mode = st.radio("View", ["Cards", "Table"], horizontal=True, label_visibility="collapsed")

    if not results:
        st.info("No products found. Try different keywords or adjust the filters.")
    elif view_mode == "Table":
        # Clean dataframe view
        df_view = pd.DataFrame(results)[[
            "id","name","brand","category","price","rating","stock",
            "_bm25_rank","_vector_rank","_rrf_score"
        ]]
        df_view.columns = ["ID","Name","Brand","Category","Price (₹)","Rating","Stock",
                           "BM25 rank","Vector rank","RRF score"]
        st.dataframe(df_view, use_container_width=True, hide_index=True)
    else:
        # Cards view - 2 columns
        left, right = st.columns(2)
        for i, product in enumerate(results):
            with (left if i % 2 == 0 else right):
                render_product_card(product, i + 1)

    # ── score transparency expander ────────────────────────────────────────────
    with st.expander("🔍 How did each result score? (score breakdown)"):
        st.markdown("Each product is scored by **two** methods, then combined by **Reciprocal Rank Fusion**.")
        rows = []
        for i, p in enumerate(results):
            rows.append({
                "Rank": i+1,
                "Product": p["name"][:45],
                "BM25 rank": p.get("_bm25_rank","—"),
                "BM25 score": round(p.get("_bm25_score",0), 3),
                "Vector rank": p.get("_vector_rank","—"),
                "Vector score": round(p.get("_vector_score",0), 3),
                "RRF score": round(p.get("_rrf_score",0), 5),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

else:
    # Landing state
    st.markdown("""
    <div style="text-align:center; padding:60px 20px; color:#aaa">
      <div style="font-size:64px">🔍</div>
      <div style="font-size:18px; margin-top:16px; color:#666">Type anything above to search 50 products</div>
      <div style="font-size:13px; margin-top:8px">Powered by BM25 · FAISS Semantic Search · RAG</div>
    </div>
    """, unsafe_allow_html=True)
