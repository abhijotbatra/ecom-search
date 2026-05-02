"""
RAG (Retrieval-Augmented Generation) Layer
===========================================
Takes the top-K retrieved products and the original query,
builds a structured prompt, and calls the LLM to generate
a grounded, human-friendly answer.

Works with:
  - OpenAI GPT-4o / GPT-3.5-turbo  (if OPENAI_API_KEY is set)
  - Anthropic Claude                (if ANTHROPIC_API_KEY is set)
  - Offline fallback                (rule-based summary, no API key needed)
"""

import os
import json
import logging
from typing import Optional

log = logging.getLogger(__name__)


# ── prompt builder ─────────────────────────────────────────────────────────────

def build_rag_prompt(query: str, products: list[dict]) -> str:
    """
    Construct the RAG prompt.
    The LLM receives the query + top retrieved products as context.
    It is instructed to answer ONLY from the given context (grounded generation).
    """
    if not products:
        return ""

    # Format each product as structured context
    context_lines = []
    for i, p in enumerate(products, 1):
        context_lines.append(
            f"[Product {i}]\n"
            f"  Name     : {p.get('name','')}\n"
            f"  Brand    : {p.get('brand','')}\n"
            f"  Category : {p.get('category','')} > {p.get('subcategory','')}\n"
            f"  Price    : ₹{p.get('price',0):,}\n"
            f"  Rating   : {p.get('rating',0)}/5.0\n"
            f"  Stock    : {p.get('stock',0)} units\n"
            f"  About    : {p.get('description','')}\n"
        )

    context_block = "\n".join(context_lines)

    system_prompt = """You are a helpful e-commerce shopping assistant. 
Your job is to analyse the retrieved products and give the user a clear, 
concise, and friendly recommendation based ONLY on the provided product data.

Rules:
- Only reference products from the context below. Never invent products.
- Mention specific prices, ratings, and key features.
- Highlight the best option and briefly explain why.
- If multiple products suit different needs, say so clearly.
- Keep the answer under 150 words. Be warm, helpful, and direct.
- End with one practical buying tip if relevant.
"""

    user_prompt = f"""User is searching for: "{query}"

Retrieved products from our catalogue:
{context_block}

Based on these products, give the user a smart shopping recommendation."""

    return system_prompt, user_prompt


# ── LLM callers ────────────────────────────────────────────────────────────────

def call_openai(system: str, user: str, model: str = "gpt-4o-mini") -> str:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            max_tokens=400,
            temperature=0.3,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        log.error(f"OpenAI error: {e}")
        return None


def call_anthropic(system: str, user: str) -> str:
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=400,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return resp.content[0].text.strip()
    except Exception as e:
        log.error(f"Anthropic error: {e}")
        return None


def offline_summary(query: str, products: list[dict]) -> str:
    """
    Rule-based fallback when no API key is available.
    Still gives a useful structured summary.
    """
    if not products:
        return "No products found matching your search."

    top = products[0]
    lines = [
        f"Top match: **{top['name']}** by {top['brand']} at ₹{top['price']:,} (rated {top['rating']}/5).",
        f"{top['description'][:120]}...",
        "",
    ]

    if len(products) > 1:
        lines.append(f"Also consider ({len(products)-1} more results shown below):")
        for p in products[1:3]:
            lines.append(f"  • {p['name']} — ₹{p['price']:,} | ⭐ {p['rating']}")

    lines.append("\n💡 *Tip: Use filters on the left to narrow by price or rating.*")
    lines.append("\n_(AI summary unavailable — add OPENAI_API_KEY or ANTHROPIC_API_KEY to .env for smart answers)_")
    return "\n".join(lines)


# ── public API ─────────────────────────────────────────────────────────────────

def generate_rag_answer(
    query: str,
    products: list[dict],
    llm_provider: str = "auto",          # "auto" | "openai" | "anthropic" | "offline"
) -> dict:
    """
    Returns:
      {
        "answer"  : str,
        "provider": str,   # which LLM was used
        "grounded": bool,  # True if answer came from LLM
      }
    """
    if not products:
        return {
            "answer": "No products found for your query. Try different keywords or adjust the filters.",
            "provider": "none",
            "grounded": False,
        }

    system_prompt, user_prompt = build_rag_prompt(query, products[:5])  # cap at 5 for context

    answer = None
    provider = "offline"

    if llm_provider in ("auto", "openai") and os.getenv("OPENAI_API_KEY"):
        answer = call_openai(system_prompt, user_prompt)
        if answer:
            provider = "openai"

    if answer is None and llm_provider in ("auto", "anthropic") and os.getenv("ANTHROPIC_API_KEY"):
        answer = call_anthropic(system_prompt, user_prompt)
        if answer:
            provider = "anthropic"

    if answer is None:
        answer = offline_summary(query, products)
        provider = "offline"

    return {
        "answer": answer,
        "provider": provider,
        "grounded": provider != "offline",
    }
