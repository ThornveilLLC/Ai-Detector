"""
Claude API text detection — replaces GPTZero.
Uses claude-haiku-4-5 (cheapest/fastest) to analyze text for AI generation signals.
"""

import os
import json
import anthropic

_client = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return _client


SYSTEM_PROMPT = """You are an expert AI content detector. Analyze text and determine the probability it was AI-generated.

Respond with valid JSON only — no markdown, no explanation outside the JSON.

JSON format:
{
  "ai_probability": <float 0.0-1.0>,
  "suspected_source": <"ChatGPT" | "Claude" | "Gemini" | "Llama" | null>,
  "explanation": "<1-2 sentence plain English explanation>",
  "flagged_sentences": [
    { "sentence": "<sentence text>", "ai_probability": <float 0.0-1.0> }
  ]
}

STRONG signals of AI-generated text (raise probability significantly):
- Repeated transitional boilerplate in the same passage: "It is worth noting", "It is important to note", "In conclusion", "Furthermore", "Additionally" — especially when stacked together
- Generic, contentless framing: "On one hand / on the other hand" with no specific facts
- Closing summary sentences restating what was just said ("In conclusion, X is important because it is important")
- Lack of specific facts, names, dates, citations, or measurements — AI tends to be vague
- Uniform paragraph length and sentence rhythm throughout the entire passage
- "Both opportunities and challenges" / "requires careful consideration" type diplomatic hedging

NOT signals of AI (do NOT raise probability for these alone):
- Formal, academic, or encyclopedic writing style (e.g. Wikipedia, textbooks, journalism)
- Technical or scientific vocabulary
- Well-structured prose without typos
- Absence of contractions in professional/academic contexts
- Comprehensive topic coverage in an encyclopedia or educational context
- Passive voice in scientific or academic writing

CALIBRATION RULES:
- If the text looks like Wikipedia, a textbook, news article, or academic paper: start from 0.10, only raise for specific AI boilerplate signals
- Most text is human — default to low probability unless you see clear AI signatures
- "Uncertain" (0.40–0.74) means genuinely ambiguous, not "formal writing that could be AI"
- Only return > 0.75 when you see multiple strong AI signals together"""


async def check_text(text: str) -> dict:
    """Analyze text for AI generation using Claude. Returns normalized result dict."""
    client = _get_client()

    # Truncate to ~3000 words to control cost
    words = text.split()
    if len(words) > 3000:
        text = " ".join(words[:3000]) + " [truncated]"

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Analyze this text:\n\n{text}"}],
    )

    raw_text = message.content[0].text.strip()

    # Strip markdown code fences if present
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        # Fallback if Claude doesn't return clean JSON
        return {
            "ai_probability": 0.5,
            "suspected_source": None,
            "explanation": "Analysis inconclusive — could not parse detection result.",
            "sentence_highlights": [],
        }

    highlights = [
        {"sentence": s.get("sentence", ""), "ai_probability": s.get("ai_probability", 0.0)}
        for s in data.get("flagged_sentences", [])
        if s.get("ai_probability", 0.0) > 0.5
    ]

    return {
        "ai_probability": float(data.get("ai_probability", 0.5)),
        "suspected_source": data.get("suspected_source"),
        "explanation": data.get("explanation", ""),
        "sentence_highlights": highlights,
    }
