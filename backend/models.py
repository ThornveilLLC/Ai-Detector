from pydantic import BaseModel
from typing import Literal, Optional


class ScanRequest(BaseModel):
    text: Optional[str] = None
    image_url: Optional[str] = None
    # image bytes come via multipart upload, not JSON


class SentenceHighlight(BaseModel):
    sentence: str
    ai_probability: float


class ScanResult(BaseModel):
    content_type: Literal["text", "image", "video", "audio", "mixed"]
    verdict: Literal["likely_human", "uncertain", "likely_ai"]
    ai_probability: float          # 0.0 – 1.0
    confidence: Literal["low", "medium", "high"]
    explanation: str               # plain-English summary
    suspected_source: Optional[str] = None   # e.g. "Midjourney", "ChatGPT"
    sentence_highlights: Optional[list[SentenceHighlight]] = None  # text only
    raw: Optional[dict] = None     # raw API response for debugging
