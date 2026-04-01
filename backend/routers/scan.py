"""
/api/scan endpoint — routes content to the appropriate detection service(s)
and aggregates results into a unified ScanResult.

Text:  Claude API (claude-haiku-4-5)
Image: Sightengine
Audio: Hive
"""

from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from typing import Optional, Literal
import httpx

from models import ScanResult, SentenceHighlight
from services import sightengine, claude_text, hive

router = APIRouter(prefix="/api")


def _verdict(prob: float) -> Literal["likely_human", "uncertain", "likely_ai"]:
    if prob >= 0.65:
        return "likely_ai"
    if prob >= 0.40:
        return "uncertain"
    return "likely_human"


def _confidence(prob: float) -> Literal["low", "medium", "high"]:
    distance = abs(prob - 0.5)
    if distance >= 0.35:
        return "high"
    if distance >= 0.15:
        return "medium"
    return "low"


@router.post("/scan", response_model=ScanResult)
async def scan(
    text: Optional[str] = Form(None),
    image_url: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    audio: Optional[UploadFile] = File(None),
    audio_url: Optional[str] = Form(None),
    video_url: Optional[str] = Form(None),
):
    """
    Accepts one or more of: text, image_url, image upload, audio upload, audio_url, video_url.
    Returns a unified AI detection result.
    """
    if not text and not image_url and not image and not audio and not audio_url and not video_url:
        raise HTTPException(status_code=400, detail="Provide text, image_url, image, audio, audio_url, or video_url.")

    image_result = None
    text_result = None
    audio_result = None
    raw_combined = {}

    # --- Image scan (Sightengine) ---
    if image:
        image_bytes = await image.read()
        try:
            raw_img = await sightengine.check_image_bytes(image_bytes, image.filename or "upload.jpg")
            image_result = sightengine.parse_result(raw_img)
            raw_combined["sightengine"] = raw_img
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=502, detail=f"Sightengine error: {e.response.text}")

    elif image_url:
        try:
            raw_img = await sightengine.check_image_url(image_url)
            image_result = sightengine.parse_result(raw_img)
            raw_combined["sightengine"] = raw_img
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=502, detail=f"Sightengine error: {e.response.text}")

    # --- Text scan (Claude) ---
    if text and text.strip():
        try:
            text_result = await claude_text.check_text(text)
            raw_combined["claude"] = {"model": "claude-haiku-4-5-20251001"}
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Claude text detection error: {str(e)}")

    # --- Video scan (Sightengine) ---
    if video_url:
        try:
            raw_vid = await sightengine.check_video_url(video_url)
            image_result = sightengine.parse_video_result(raw_vid)
            raw_combined["sightengine_video"] = raw_vid
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=502, detail=f"Sightengine video error: {e.response.text}")

    # --- Audio scan (Hive) ---
    if audio:
        audio_bytes = await audio.read()
        try:
            raw_audio = await hive.check_audio_bytes(audio_bytes, audio.filename or "upload.mp3")
            audio_result = hive.parse_result(raw_audio)
            raw_combined["hive"] = raw_audio
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=502, detail=f"Hive error: {e.response.text}")

    elif audio_url:
        try:
            raw_audio = await hive.check_audio_url(audio_url)
            audio_result = hive.parse_result(raw_audio)
            raw_combined["hive"] = raw_audio
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=502, detail=f"Hive error: {e.response.text}")

    # --- Aggregate results ---
    active_results = [r for r in [image_result, text_result, audio_result] if r is not None]

    if not active_results:
        raise HTTPException(status_code=500, detail="No detection results returned.")

    # Weighted combination: image 50%, text 35%, audio 15%
    weights = {"image": 0.50, "text": 0.35, "audio": 0.15}
    total_weight = 0.0
    combined_prob = 0.0

    if image_result:
        combined_prob += image_result["ai_probability"] * weights["image"]
        total_weight += weights["image"]
    if text_result:
        combined_prob += text_result["ai_probability"] * weights["text"]
        total_weight += weights["text"]
    if audio_result:
        combined_prob += audio_result["ai_probability"] * weights["audio"]
        total_weight += weights["audio"]

    # Normalize to the actual weights used
    combined_prob = combined_prob / total_weight

    # Content type label
    types = []
    if image_result:
        types.append("video" if video_url else "image")
    if text_result:
        types.append("text")
    if audio_result:
        types.append("audio")
    content_type = "mixed" if len(types) > 1 else types[0]

    # Build explanation
    parts = []
    if image_result:
        parts.append(f"Image: {image_result['explanation']}")
    if text_result:
        parts.append(f"Text: {text_result['explanation']}")
    if audio_result:
        parts.append(f"Audio: {audio_result['explanation']}")
    explanation = " | ".join(parts)

    # Suspected source — prefer image result, then text
    suspected = None
    for r in [image_result, text_result, audio_result]:
        if r and r.get("suspected_source"):
            suspected = r["suspected_source"]
            break

    # Sentence highlights from text result
    highlights = None
    if text_result and text_result.get("sentence_highlights"):
        highlights = [SentenceHighlight(**h) for h in text_result["sentence_highlights"]]

    return ScanResult(
        content_type=content_type,
        verdict=_verdict(combined_prob),
        ai_probability=round(combined_prob, 4),
        confidence=_confidence(combined_prob),
        explanation=explanation,
        suspected_source=suspected,
        sentence_highlights=highlights if highlights else None,
        raw=raw_combined,
    )
