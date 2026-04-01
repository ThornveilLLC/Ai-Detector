"""
GPTZero API integration — AI-generated text detection.
Docs: https://gptzero.me/api-reference
"""

import os
import httpx
from typing import Optional


GPTZERO_API_KEY = os.getenv("GPTZERO_API_KEY", "")
BASE_URL = "https://api.gptzero.me/v2/predict"


async def check_text(text: str) -> dict:
    """Check text for AI generation. Returns raw GPTZero response."""
    headers = {
        "x-api-key": GPTZERO_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {
        "document": text,
        "multiscan": False,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(f"{BASE_URL}/text", headers=headers, json=payload)
        response.raise_for_status()
        return response.json()


def parse_result(raw: dict) -> dict:
    """
    Parse GPTZero response into normalized fields.
    Returns: { ai_probability, suspected_source, explanation, sentence_highlights }
    """
    doc = raw.get("documents", [{}])[0]
    classification = doc.get("completely_generated_prob", 0.0)
    class_label = doc.get("predicted_class", "UNKNOWN")  # HUMAN_ONLY | MIXED | AI_ONLY

    # sentence-level highlights
    sentences = doc.get("sentences", [])
    highlights = []
    for s in sentences:
        prob = s.get("generated_prob", 0.0)
        if prob > 0.5:
            highlights.append({
                "sentence": s.get("sentence", ""),
                "ai_probability": prob,
            })

    # suspected source (GPTZero returns likely model sometimes)
    suspected = _map_source(doc.get("predicted_generated_score_info", {}))

    explanation = _build_text_explanation(classification, class_label)
    return {
        "ai_probability": classification,
        "suspected_source": suspected,
        "explanation": explanation,
        "sentence_highlights": highlights,
    }


def _map_source(score_info: dict) -> Optional[str]:
    if not score_info:
        return None
    # GPTZero may include model-specific breakdown in some plans
    models = score_info.get("top_generated_models", [])
    if models:
        return models[0]
    return None


def _build_text_explanation(score: float, label: str) -> str:
    if label == "AI_ONLY" or score >= 0.85:
        base = "This text shows strong indicators of AI generation."
    elif label == "MIXED" or score >= 0.4:
        base = "This text appears to be a mix of human and AI-written content."
    else:
        base = "This text reads as likely human-written."

    base += f" AI probability: {round(score * 100)}%."
    return base
