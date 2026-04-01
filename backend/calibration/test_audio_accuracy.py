"""
test_audio_accuracy.py — First-ever Hive audio AI detection calibration.
~20 samples (10 real human audio, 10 AI-generated TTS).
Saves raw Hive class scores for threshold analysis.

This is exploratory — the 0.65 verdict threshold was calibrated for images (bimodal
0.01/0.99). Audio may have a different score distribution. The summary will include
a threshold recommendation based on the actual score distributions.

Notes:
- Wikimedia pronunciation clips may be <1s. If Hive rejects them, they are skipped
  and logged as "too_short" — this does not abort the run.
- Do NOT add MIDI files to the real category — MIDI is synthesizer-generated.
- If a URL returns 404, it is skipped and logged. Imbalanced real/AI counts are
  documented in the summary.

Usage (from ai-detector/backend/calibration/):
    python test_audio_accuracy.py
    (backend must be running: uvicorn main:app --port 8001)
    (models.py must include "audio" in content_type Literal — fixed 2026-03-21)
"""

import json
import time
import urllib.request
import urllib.parse
import io
import email.mime.multipart
import email.mime.base
from datetime import datetime, timezone
from pathlib import Path

API_URL       = "http://localhost:8001/api/scan"
OUTPUT_FILE   = Path(__file__).parent / "audio_accuracy_results.json"
SLEEP_SECONDS = 15   # Hive rate limits are tighter than Sightengine
MAX_TESTS     = 25   # Cap above 20 to absorb dead URLs

# ---------------------------------------------------------------------------
# URL lists
# Real: Wikimedia Commons human speech recordings (OGG, no auth required)
# AI: Open-source TTS model sample outputs hosted on GitHub/HuggingFace
# ---------------------------------------------------------------------------

CATEGORIES = {
    "spoken_word": {
        "real": [
            # Open Speech Repository — Harvard sentences, real human speakers, 8kHz WAV
            # (verified 2026-03-22, voiptroubleshooter.com CDN, no auth required)
            "https://www.voiptroubleshooter.com/open_speech/american/OSR_us_000_0010_8k.wav",
            "https://www.voiptroubleshooter.com/open_speech/american/OSR_us_000_0011_8k.wav",
            "https://www.voiptroubleshooter.com/open_speech/american/OSR_us_000_0012_8k.wav",
            "https://www.voiptroubleshooter.com/open_speech/american/OSR_us_000_0013_8k.wav",
            "https://www.voiptroubleshooter.com/open_speech/american/OSR_us_000_0014_8k.wav",
            "https://www.voiptroubleshooter.com/open_speech/american/OSR_us_000_0015_8k.wav",
            "https://www.voiptroubleshooter.com/open_speech/american/OSR_us_000_0016_8k.wav",
            "https://www.voiptroubleshooter.com/open_speech/american/OSR_us_000_0017_8k.wav",
            "https://www.voiptroubleshooter.com/open_speech/american/OSR_us_000_0018_8k.wav",
            "https://www.voiptroubleshooter.com/open_speech/american/OSR_us_000_0019_8k.wav",
        ],
        "ai_generated": [
            # Kokoro-82M — English neural TTS model output (confirmed synthesized)
            # (verified 2026-03-22, HuggingFace LFS, no auth required)
            "https://huggingface.co/hexgrad/Kokoro-82M/resolve/main/samples/HEARME.wav",
            "https://huggingface.co/hexgrad/Kokoro-82M/resolve/main/samples/af_heart_0.wav",
            "https://huggingface.co/hexgrad/Kokoro-82M/resolve/main/samples/af_heart_1.wav",
            "https://huggingface.co/hexgrad/Kokoro-82M/resolve/main/samples/af_heart_2.wav",
            "https://huggingface.co/hexgrad/Kokoro-82M/resolve/main/samples/af_heart_3.wav",
            "https://huggingface.co/hexgrad/Kokoro-82M/resolve/main/samples/af_heart_4.wav",
            "https://huggingface.co/hexgrad/Kokoro-82M/resolve/main/samples/af_heart_5.wav",
            # Coqui XTTS-v2 — multilingual neural TTS model output samples
            # Note: these are TTS *output* samples from the model card, not conditioning audio
            "https://huggingface.co/coqui/XTTS-v2/resolve/main/samples/en_sample.wav",
            "https://huggingface.co/coqui/XTTS-v2/resolve/main/samples/fr_sample.wav",
            "https://huggingface.co/coqui/XTTS-v2/resolve/main/samples/de_sample.wav",
        ],
    },
}


def build_queue():
    queue = []
    for cat, groups in CATEGORIES.items():
        for ground_truth, urls in groups.items():
            for url in urls:
                queue.append((url, ground_truth, cat))
    return queue


def download_audio(url: str) -> tuple[bytes, str]:
    """Download audio bytes from URL. Returns (bytes, filename)."""
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "audio/wav, audio/mpeg, audio/ogg, audio/*, */*",
        "Accept-Encoding": "identity",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read(), url.split("/")[-1].split("?")[0] or "audio.wav"


def scan_audio(url: str) -> dict:
    """Download audio from URL, then POST as multipart bytes upload to /api/scan."""
    try:
        audio_bytes, filename = download_audio(url)
    except Exception as e:
        return {"error": f"Download failed: {e}"}

    # Build multipart/form-data body manually
    boundary = "----AudioCalibBoundary7a3f"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="audio"; filename="{filename}"\r\n'
        f"Content-Type: application/octet-stream\r\n\r\n"
    ).encode() + audio_bytes + f"\r\n--{boundary}--\r\n".encode()

    req = urllib.request.Request(API_URL, data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}


def is_rate_limited(resp: dict) -> bool:
    err = resp.get("error", "")
    if "429" in str(err) or "rate" in str(err).lower():
        return True
    hive_raw = resp.get("raw", {}).get("hive", {})
    return hive_raw.get("code") == 429


def load_existing() -> dict:
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE) as f:
            return json.load(f)
    return {
        "meta": {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "total_tested": 0,
            "target": 20,
            "accuracy_running": 0.0,
            "note": "First-ever Hive audio calibration run",
        },
        "by_category": {},
        "results": [],
        "skipped_urls": [],
    }


def save(data: dict):
    data["meta"]["last_updated"] = datetime.now(timezone.utc).isoformat()
    for cat in data["by_category"].values():
        for k in ("_sr", "_cr", "_sa", "_ca"):
            cat.pop(k, None)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print("  [saved]")


def is_correct(ground_truth: str, verdict: str) -> bool:
    return verdict == ("likely_human" if ground_truth == "real" else "likely_ai")


def update_category(data: dict, cat: str, ground_truth: str, prob: float, correct: bool):
    c = data["by_category"].setdefault(cat, {
        "total": 0, "correct": 0, "accuracy": 0.0,
        "avg_prob_real": 0.0, "avg_prob_ai": 0.0,
        "_sr": 0.0, "_cr": 0, "_sa": 0.0, "_ca": 0,
    })
    # Restore accumulators from saved results if missing (stripped on save)
    if "_cr" not in c:
        cat_r = [r for r in data["results"] if r["category"] == cat]
        real_r = [r for r in cat_r if r["ground_truth"] == "real"]
        ai_r   = [r for r in cat_r if r["ground_truth"] == "ai_generated"]
        c["_cr"] = len(real_r)
        c["_ca"] = len(ai_r)
        c["_sr"] = sum(r["ai_probability"] for r in real_r)
        c["_sa"] = sum(r["ai_probability"] for r in ai_r)
    c["total"] += 1
    if correct:
        c["correct"] += 1
    c["accuracy"] = round(c["correct"] / c["total"], 4)
    if ground_truth == "real":
        c["_sr"] += prob
        c["_cr"] += 1
        c["avg_prob_real"] = round(c["_sr"] / c["_cr"], 4)
    else:
        c["_sa"] += prob
        c["_ca"] += 1
        c["avg_prob_ai"] = round(c["_sa"] / c["_ca"], 4)


def extract_hive_scores(resp: dict):
    """Extract raw Hive ai_generated_audio and not_ai_generated_audio scores from V3 response."""
    try:
        # V3 path: raw.hive.output[0].classes[].value
        chunks = resp["raw"]["hive"]["output"]
        # Take max ai_generated_audio across all 10-second chunks (worst-case)
        ai_scores    = [next((c["value"] for c in ch["classes"] if c["class"] == "ai_generated_audio"),     None) for ch in chunks]
        human_scores = [next((c["value"] for c in ch["classes"] if c["class"] == "not_ai_generated_audio"), None) for ch in chunks]
        ai_scores    = [s for s in ai_scores    if s is not None]
        human_scores = [s for s in human_scores if s is not None]
        return (max(ai_scores) if ai_scores else None,
                min(human_scores) if human_scores else None)
    except (KeyError, IndexError, TypeError):
        return None, None


def infer_format(url: str) -> str:
    url_lower = url.lower()
    for ext in ("wav", "mp3", "ogg", "flac", "m4a"):
        if f".{ext}" in url_lower:
            return ext
    return "unknown"


def main():
    data = load_existing()
    queue = build_queue()
    tested = 0
    next_id = len(data["results"]) + 1

    print(f"Audio accuracy — {len(queue)} URLs, max {MAX_TESTS} tests, {SLEEP_SECONDS}s between each")
    print(f"Output: {OUTPUT_FILE}\n")

    for url, ground_truth, cat in queue:
        if tested >= MAX_TESTS:
            print(f"\nReached {MAX_TESTS} test cap.")
            break

        fmt = infer_format(url)
        print(f"[{tested+1}/{MAX_TESTS}] {cat} | {ground_truth} | {fmt} | ...{url[-55:]}")
        resp = scan_audio(url)

        if "verdict" not in resp:
            err = resp.get("error", "no verdict")
            err_type = "too_short" if "duration" in str(err).lower() else (
                "unsupported_format" if "format" in str(err).lower() or "unsupported" in str(err).lower() else
                "url_error"
            )
            print(f"  SKIP ({err_type}) — {str(err)[:80]}")
            data["skipped_urls"].append({
                "url": url, "ground_truth": ground_truth,
                "error_type": err_type, "error": str(err)[:200],
            })
            time.sleep(SLEEP_SECONDS)
            continue

        if is_rate_limited(resp):
            print("Hive rate limit hit — stopping.")
            break

        verdict = resp["verdict"]
        prob    = resp.get("ai_probability", 0.0)
        correct = is_correct(ground_truth, verdict)
        ai_score, human_score = extract_hive_scores(resp)

        data["results"].append({
            "id": next_id,
            "category": cat,
            "ground_truth": ground_truth,
            "url": url,
            "format": fmt,
            "verdict": verdict,
            "ai_probability": prob,
            "confidence": resp.get("confidence", ""),
            "correct": correct,
            "hive_ai_score": ai_score,
            "hive_human_score": human_score,
        })
        next_id += 1
        update_category(data, cat, ground_truth, prob, correct)

        all_r = data["results"]
        total_correct = sum(1 for r in all_r if r.get("correct"))
        tested += 1
        data["meta"]["total_tested"] = tested
        data["meta"]["accuracy_running"] = round(total_correct / len(all_r), 4)

        label = "OK   " if correct else "WRONG"
        print(f"  {label} — verdict={verdict} prob={prob:.2f}  "
              f"hive(ai={ai_score} human={human_score})")

        if tested % 5 == 0:
            save(data)

        if tested < MAX_TESTS:
            time.sleep(SLEEP_SECONDS)

    # Final save + summary
    all_r  = data["results"]
    real_r = [r for r in all_r if r["ground_truth"] == "real"]
    ai_r   = [r for r in all_r if r["ground_truth"] == "ai_generated"]
    fp     = sum(1 for r in real_r if r["verdict"] == "likely_ai")
    fn     = sum(1 for r in ai_r  if r["verdict"] == "likely_human")
    unc    = sum(1 for r in all_r if r["verdict"] == "uncertain")

    avg_real = round(sum(r["ai_probability"] for r in real_r) / max(1, len(real_r)), 4)
    avg_ai   = round(sum(r["ai_probability"] for r in ai_r)   / max(1, len(ai_r)), 4)

    hive_real = [r["hive_ai_score"] for r in real_r if r["hive_ai_score"] is not None]
    hive_ai   = [r["hive_ai_score"] for r in ai_r   if r["hive_ai_score"] is not None]
    avg_hive_real = round(sum(hive_real) / max(1, len(hive_real)), 4) if hive_real else None
    avg_hive_ai   = round(sum(hive_ai)   / max(1, len(hive_ai)), 4)   if hive_ai   else None

    # Threshold recommendation based on score distribution
    threshold_rec = "Insufficient data"
    if avg_hive_real is not None and avg_hive_ai is not None:
        midpoint = round((avg_hive_real + avg_hive_ai) / 2, 2)
        if avg_hive_ai < 0.65:
            threshold_rec = (
                f"Current 0.65 threshold may be TOO HIGH for audio. "
                f"AI avg={avg_hive_ai}, Real avg={avg_hive_real}. "
                f"Suggested threshold: {midpoint} (midpoint between averages)."
            )
        else:
            threshold_rec = (
                f"Current 0.65 threshold appears appropriate. "
                f"AI avg={avg_hive_ai}, Real avg={avg_hive_real}."
            )

    data["summary"] = {
        "total_tested": len(all_r),
        "skipped_count": len(data.get("skipped_urls", [])),
        "real_count": len(real_r),
        "ai_count": len(ai_r),
        "overall_accuracy": round(sum(1 for r in all_r if r["correct"]) / max(1, len(all_r)), 4),
        "false_positive_rate": round(fp / max(1, len(real_r)), 4),
        "false_negative_rate": round(fn / max(1, len(ai_r)), 4),
        "uncertain_rate": round(unc / max(1, len(all_r)), 4),
        "avg_prob_real": avg_real,
        "avg_prob_ai": avg_ai,
        "avg_hive_ai_score_on_real": avg_hive_real,
        "avg_hive_ai_score_on_ai": avg_hive_ai,
        "threshold_recommendation": threshold_rec,
        "threshold_note": (
            "The 0.65 'likely_ai' threshold in scan.py was calibrated for images "
            "(bimodal 0.01/0.99). Audio may need a different threshold."
        ),
        "by_category": {
            cat: {k: v for k, v in stats.items() if not k.startswith("_")}
            for cat, stats in data["by_category"].items()
        },
        "notes": f"First-ever Hive audio calibration. {tested} tests at {SLEEP_SECONDS}s intervals.",
    }
    save(data)

    print(f"\nDone — {tested} tests, {len(data.get('skipped_urls', []))} skipped.")
    print(f"Accuracy: {data['summary']['overall_accuracy']*100:.1f}%")
    print(f"FP rate:  {data['summary']['false_positive_rate']*100:.1f}%  "
          f"FN rate: {data['summary']['false_negative_rate']*100:.1f}%")
    print(f"Hive avg score — real: {avg_hive_real}  AI: {avg_hive_ai}")
    print(f"Threshold: {threshold_rec}")


if __name__ == "__main__":
    main()
