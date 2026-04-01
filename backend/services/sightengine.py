"""
Sightengine API integration — image and video AI detection.
Docs: https://sightengine.com/docs/api-image-moderation
"""

import os
import httpx
from typing import Optional


SIGHTENGINE_API_USER = os.getenv("SIGHTENGINE_API_USER", "")
SIGHTENGINE_API_SECRET = os.getenv("SIGHTENGINE_API_SECRET", "")
BASE_URL = "https://api.sightengine.com/1.0"


async def check_image_url(image_url: str) -> dict:
    """Check a publicly accessible image URL for AI generation."""
    params = {
        "url": image_url,
        "models": "genai",
        "api_user": SIGHTENGINE_API_USER,
        "api_secret": SIGHTENGINE_API_SECRET,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(f"{BASE_URL}/check.json", params=params)
        response.raise_for_status()
        return response.json()


async def check_image_bytes(image_bytes: bytes, filename: str = "image.jpg") -> dict:
    """Check an uploaded image for AI generation."""
    params = {
        "models": "genai",
        "api_user": SIGHTENGINE_API_USER,
        "api_secret": SIGHTENGINE_API_SECRET,
    }
    files = {"media": (filename, image_bytes, "image/jpeg")}
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{BASE_URL}/check.json",
            params=params,
            files=files,
        )
        response.raise_for_status()
        return response.json()


def parse_result(raw: dict) -> dict:
    """
    Parse Sightengine response into normalized fields.
    Returns: { ai_probability, suspected_source, explanation }
    """
    # Sightengine returns type.ai_generated as a float (e.g. 0.97), not a dict
    genai_raw = raw.get("type", {}).get("ai_generated", raw.get("ai_generated", 0.0))
    if isinstance(genai_raw, (int, float)):
        score = float(genai_raw)
    elif isinstance(genai_raw, dict):
        score = float(genai_raw.get("score", 0.0))
    else:
        score = 0.0

    # Sightengine sometimes names the suspected model
    suspected = None
    if "type" in raw:
        t = raw["type"]
        for key in ("midjourney", "dalle", "stable_diffusion", "firefly"):
            if t.get(key, 0) > 0.5:
                suspected = key.replace("_", " ").title()
                break

    explanation = _build_image_explanation(score, suspected)
    return {
        "ai_probability": score,
        "suspected_source": suspected,
        "explanation": explanation,
    }


async def check_video_url(video_url: str) -> dict:
    """
    Submit a public video URL to Sightengine for AI generation detection.
    Sightengine samples frames and returns per-frame + aggregate scores.
    """
    params = {
        "stream_url": video_url,
        "models": "genai",
        "api_user": SIGHTENGINE_API_USER,
        "api_secret": SIGHTENGINE_API_SECRET,
    }
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.get(f"{BASE_URL}/video/check.json", params=params)
        response.raise_for_status()
        return response.json()


def parse_video_result(raw: dict) -> dict:
    """
    Parse Sightengine video response. The API returns per-frame data under 'data.frames'.
    We average the ai_generated scores across all frames.
    """
    frames = raw.get("data", {}).get("frames", [])
    if not frames:
        # Fallback: some responses return top-level type field same as image
        return parse_result(raw)

    scores = []
    for frame in frames:
        genai_raw = frame.get("type", {}).get("ai_generated", 0.0)
        if isinstance(genai_raw, (int, float)):
            scores.append(float(genai_raw))
        elif isinstance(genai_raw, dict):
            scores.append(float(genai_raw.get("score", 0.0)))

    score = sum(scores) / len(scores) if scores else 0.0
    explanation = _build_image_explanation(score, None)
    explanation = explanation.replace("image", "video")
    return {
        "ai_probability": score,
        "suspected_source": None,
        "explanation": explanation,
    }


def _build_image_explanation(score: float, suspected: Optional[str]) -> str:
    if score >= 0.85:
        base = "This image shows strong indicators of AI generation."
    elif score >= 0.55:
        base = "This image has some characteristics consistent with AI generation, but the signal is mixed."
    else:
        base = "This image appears consistent with a real photograph."

    if suspected:
        base += f" The visual style is consistent with {suspected}."

    base += f" AI probability: {round(score * 100)}%."
    return base
