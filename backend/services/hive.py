"""
Hive AI Detection — V3 API (Hive Models product)
Model: hive/ai-generated-and-deepfake-content-detection
Docs:  https://thehive.ai/playground/hive/ai-generated-and-deepfake-content-detection

Auth:     Authorization: Bearer <HIVE_SECRET_KEY>
Endpoint: POST https://api.thehive.ai/api/v3/hive/ai-generated-and-deepfake-content-detection
Request:  multipart form-data with "media" (file bytes) or "url" (string)
Response: { "task_id": "...", "output": [{ "classes": [{"class": "...", "value": 0.0}] }] }

Audio classes:
  "ai_generated_audio"     — probability audio is AI-generated TTS/synthetic
  "not_ai_generated_audio" — probability audio is real human speech

Note: HIVE_ACCESS_KEY_ID is a rotation key (for key management). HIVE_SECRET_KEY is the
active bearer token. Both env vars come from the Hive Models portal project dashboard.
"""

import os
import httpx

HIVE_SECRET_KEY = os.getenv("HIVE_SECRET_KEY", "")
MODEL_ENDPOINT = (
    "https://api.thehive.ai/api/v3/hive/ai-generated-and-deepfake-content-detection"
)


def _auth_headers() -> dict:
    return {
        "Accept": "application/json",
        "Authorization": f"Bearer {HIVE_SECRET_KEY}",
    }


def _mime_type(filename: str) -> str:
    """Return the correct MIME type based on file extension."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return {
        "wav":  "audio/wav",
        "mp3":  "audio/mpeg",
        "ogg":  "audio/ogg",
        "flac": "audio/flac",
        "m4a":  "audio/mp4",
        "webm": "audio/webm",
    }.get(ext, "audio/mpeg")


async def check_audio_url(audio_url: str) -> dict:
    """Check a publicly accessible audio URL for AI generation."""
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            MODEL_ENDPOINT,
            headers=_auth_headers(),
            data={"url": audio_url},
        )
        response.raise_for_status()
        return response.json()


async def check_audio_bytes(audio_bytes: bytes, filename: str = "audio.mp3") -> dict:
    """Check an uploaded audio file for AI generation."""
    files = {"media": (filename, audio_bytes, _mime_type(filename))}
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            MODEL_ENDPOINT,
            headers=_auth_headers(),
            files=files,
        )
        response.raise_for_status()
        return response.json()


def parse_result(raw: dict) -> dict:
    """
    Parse Hive V3 response into normalized fields.

    V3 response shape:
      { "output": [{ "classes": [{"class": "ai_generated_audio", "value": 0.0}, ...] }] }

    Each output item is a 10-second chunk. We take the max ai_generated_audio score
    across all chunks (worst-case aggregation — flag if any chunk looks AI-generated).
    """
    try:
        chunks = raw["output"]
        ai_scores = []
        for chunk in chunks:
            classes = chunk.get("classes", [])
            score = next(
                (c["value"] for c in classes if c["class"] == "ai_generated_audio"),
                None,
            )
            if score is not None:
                ai_scores.append(score)

        ai_score = max(ai_scores) if ai_scores else 0.0
    except (KeyError, TypeError, ValueError):
        ai_score = 0.0

    explanation = _build_explanation(ai_score)
    return {
        "ai_probability": ai_score,
        "suspected_source": None,  # Hive audio doesn't identify TTS source model
        "explanation": explanation,
        "sentence_highlights": [],
    }


def _build_explanation(score: float) -> str:
    if score >= 0.85:
        return f"This audio shows strong indicators of AI generation. AI probability: {round(score * 100)}%."
    elif score >= 0.55:
        return f"This audio has some characteristics consistent with AI generation, but the signal is mixed. AI probability: {round(score * 100)}%."
    else:
        return f"This audio appears consistent with a real human recording. AI probability: {round(score * 100)}%."
