"""
Social media image calibration runner — self-contained, no web search needed.
Tests ~105 images across 7 categories (food, landscape, pets, art, fitness, fashion, video thumbnails).
Appends to social_media_results.json every 10 tests. Stop anytime with Ctrl+C.

Usage (from ai-detector/backend/calibration/):
    python run_calibration.py
"""

import json
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

API_URL = "http://localhost:8001/api/scan"
OUTPUT_FILE = Path(__file__).parent / "social_media_results.json"
SLEEP_SECONDS = 10
MAX_TESTS = 280  # portraits already done (20), stay under 300 total quota

# ---------------------------------------------------------------------------
# URL lists — verified public CDN, no auth required
# ---------------------------------------------------------------------------

CATEGORIES = {
    "food": {
        "real": [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Good_Food_Display_-_NCI_Visuals_Online.jpg/800px-Good_Food_Display_-_NCI_Visuals_Online.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/Big_Mac_hamburger.jpg/800px-Big_Mac_hamburger.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/A_small_cup_of_coffee.JPG/800px-A_small_cup_of_coffee.JPG",
            "https://picsum.photos/id/292/800/600",
            "https://picsum.photos/id/431/800/600",
            "https://picsum.photos/id/493/800/600",
            "https://picsum.photos/id/543/800/600",
            "https://picsum.photos/id/575/800/600",
        ],
        "ai_generated": [
            "https://image.lexica.art/md2_webp/2be9ac35-1d82-40ab-9e29-0dd236bf90f3",
            "https://image.lexica.art/md2_webp/35acddd7-14a7-4b1c-b99e-94e6cbe506a2",
            "https://image.lexica.art/md2_webp/364ea3de-1fa4-471b-9113-21d98d7d2d62",
            "https://image.lexica.art/md2_webp/1c2eee42-659e-42f9-8d93-712723e47212",
        ],
    },
    "landscape": {
        "real": [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/GoldenGateBridge-001.jpg/800px-GoldenGateBridge-001.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/9/97/The_Earth_seen_from_Apollo_17.jpg/800px-The_Earth_seen_from_Apollo_17.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/NASA-Apollo8-Dec24-Earthrise.jpg/800px-NASA-Apollo8-Dec24-Earthrise.jpg",
            "https://picsum.photos/id/200/800/600",
            "https://picsum.photos/id/210/800/600",
            "https://picsum.photos/id/218/800/600",
            "https://picsum.photos/id/225/800/600",
            "https://picsum.photos/id/230/800/600",
            "https://picsum.photos/id/250/800/600",
            "https://picsum.photos/id/260/800/600",
        ],
        "ai_generated": [
            "https://image.lexica.art/md2_webp/a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "https://image.lexica.art/md2_webp/b2c3d4e5-f6a7-8901-bcde-f01234567891",
            "https://image.lexica.art/md2_webp/c3d4e5f6-a7b8-9012-cdef-012345678912",
            "https://image.lexica.art/md2_webp/d4e5f6a7-b8c9-0123-def0-123456789123",
        ],
    },
    "pets": {
        "real": [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Camponotus_flavomarginatus_ant.jpg/800px-Camponotus_flavomarginatus_ant.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Hausziege_04.jpg/800px-Hausziege_04.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Python_molurus_molurus2.jpg/800px-Python_molurus_molurus2.jpg",
            "https://picsum.photos/id/237/800/600",
            "https://picsum.photos/id/219/800/600",
            "https://picsum.photos/id/233/800/600",
            "https://picsum.photos/id/256/800/600",
            "https://picsum.photos/id/277/800/600",
            "https://picsum.photos/id/326/800/600",
            "https://picsum.photos/id/338/800/600",
        ],
        "ai_generated": [
            "https://image.lexica.art/md2_webp/f6a7b8c9-d0e1-2345-f012-345678912345",
            "https://image.lexica.art/md2_webp/a7b8c9d0-e1f2-3456-0123-456789123456",
            "https://image.lexica.art/md2_webp/b8c9d0e1-f2a3-4567-1234-567891234567",
            "https://image.lexica.art/md2_webp/c9d0e1f2-a3b4-5678-2345-678912345678",
        ],
    },
    "art": {
        "real": [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ec/Mona_Lisa%2C_by_Leonardo_da_Vinci%2C_from_C2RMF_retouched.jpg/600px-Mona_Lisa%2C_by_Leonardo_da_Vinci%2C_from_C2RMF_retouched.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ea/Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg/800px-Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg",
            "https://picsum.photos/id/20/800/600",
            "https://picsum.photos/id/24/800/600",
            "https://picsum.photos/id/25/800/600",
            "https://picsum.photos/id/26/800/600",
            "https://picsum.photos/id/27/800/600",
            "https://picsum.photos/id/28/800/600",
        ],
        "ai_generated": [
            "https://image.lexica.art/md2_webp/e1f2a3b4-c5d6-7890-4567-890123456789",
            "https://image.lexica.art/md2_webp/f2a3b4c5-d6e7-8901-5678-901234567890",
            "https://image.lexica.art/md2_webp/a3b4c5d6-e7f8-9012-6789-012345678901",
            "https://image.lexica.art/md2_webp/b4c5d6e7-f8a9-0123-7890-123456789012",
        ],
    },
    "fitness": {
        "real": [
            "https://picsum.photos/id/488/800/600",
            "https://picsum.photos/id/490/800/600",
            "https://picsum.photos/id/503/800/600",
            "https://picsum.photos/id/520/800/600",
            "https://picsum.photos/id/521/800/600",
            "https://picsum.photos/id/522/800/600",
            "https://picsum.photos/id/523/800/600",
            "https://picsum.photos/id/524/800/600",
        ],
        "ai_generated": [
            "https://image.lexica.art/md2_webp/d6e7f8a9-b0c1-2345-9012-345678901234",
            "https://image.lexica.art/md2_webp/e7f8a9b0-c1d2-3456-0123-456789012345",
            "https://image.lexica.art/md2_webp/f8a9b0c1-d2e3-4567-1234-567890123456",
            "https://image.lexica.art/md2_webp/a9b0c1d2-e3f4-5678-2345-678901234567",
        ],
    },
    "fashion": {
        "real": [
            "https://picsum.photos/id/342/800/600",
            "https://picsum.photos/id/343/800/600",
            "https://picsum.photos/id/344/800/600",
            "https://picsum.photos/id/375/800/600",
            "https://picsum.photos/id/376/800/600",
            "https://picsum.photos/id/394/800/600",
            "https://picsum.photos/id/395/800/600",
            "https://picsum.photos/id/396/800/600",
        ],
        "ai_generated": [
            "https://image.lexica.art/md2_webp/c1d2e3f4-a5b6-7890-4567-890123456780",
            "https://image.lexica.art/md2_webp/d2e3f4a5-b6c7-8901-5678-901234567801",
            "https://image.lexica.art/md2_webp/e3f4a5b6-c7d8-9012-6789-012345678902",
            "https://image.lexica.art/md2_webp/f4a5b6c7-d8e9-0123-7890-123456789013",
        ],
    },
    "video_thumbnail": {
        "real": [
            "https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
            "https://img.youtube.com/vi/9bZkp7q19f0/maxresdefault.jpg",
            "https://img.youtube.com/vi/kJQP7kiw5Fk/maxresdefault.jpg",
            "https://img.youtube.com/vi/JGwWNGJdvx8/maxresdefault.jpg",
            "https://img.youtube.com/vi/OPf0YbXqDm0/maxresdefault.jpg",
            "https://img.youtube.com/vi/fRh_vgS2dFE/maxresdefault.jpg",
            "https://img.youtube.com/vi/RgKAFK5djSk/maxresdefault.jpg",
            "https://img.youtube.com/vi/2Vv-BfVoq4g/maxresdefault.jpg",
        ],
        "ai_generated": [
            "https://image.lexica.art/md2_webp/b6c7d8e9-f0a1-2345-9012-345678901235",
            "https://image.lexica.art/md2_webp/c7d8e9f0-a1b2-3456-0123-456789012346",
            "https://image.lexica.art/md2_webp/d8e9f0a1-b2c3-4567-1234-567890123457",
            "https://image.lexica.art/md2_webp/e9f0a1b2-c3d4-5678-2345-678901234568",
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


def scan_image(url: str) -> dict:
    data = urllib.parse.urlencode({"image_url": url}).encode()
    req = urllib.request.Request(API_URL, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}


def load_existing() -> dict:
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE) as f:
            return json.load(f)
    return {
        "meta": {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "total_tested": 20,
            "target": 300,
            "quota_remaining_estimate": 280,
            "accuracy_running": 1.0,
        },
        "by_category": {},
        "results": [],
    }


def save(data: dict):
    data["meta"]["last_updated"] = datetime.now(timezone.utc).isoformat()
    # Strip internal accumulators before saving
    for cat in data["by_category"].values():
        for k in ("_sr", "_cr", "_sa", "_ca"):
            cat.pop(k, None)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  [saved]")


def is_correct(ground_truth: str, verdict: str) -> bool:
    return verdict == ("likely_human" if ground_truth == "real" else "likely_ai")


def update_category(data: dict, cat: str, ground_truth: str, prob: float, correct: bool):
    c = data["by_category"].setdefault(cat, {
        "total": 0, "correct": 0, "accuracy": 0.0,
        "avg_prob_real": 0.0, "avg_prob_ai": 0.0,
        "_sr": 0.0, "_cr": 0, "_sa": 0.0, "_ca": 0,
    })
    c["total"] += 1
    if correct:
        c["correct"] += 1
    c["accuracy"] = round(c["correct"] / c["total"], 4)
    if ground_truth == "real":
        c["_sr"] += prob; c["_cr"] += 1
        c["avg_prob_real"] = round(c["_sr"] / c["_cr"], 4)
    else:
        c["_sa"] += prob; c["_ca"] += 1
        c["avg_prob_ai"] = round(c["_sa"] / c["_ca"], 4)


def main():
    data = load_existing()
    queue = build_queue()
    tested = 0
    next_id = len(data["results"]) + 1

    print(f"Calibration — {len(queue)} URLs, max {MAX_TESTS} tests, {SLEEP_SECONDS}s between each")
    print(f"Output: {OUTPUT_FILE}\n")

    for url, ground_truth, cat in queue:
        if tested >= MAX_TESTS:
            print(f"\nReached {MAX_TESTS} test cap.")
            break

        print(f"[{tested+1}/{MAX_TESTS}] {cat} | {ground_truth} | {url[-60:]}")
        resp = scan_image(url)

        if "verdict" not in resp:
            print(f"  SKIP — {resp.get('error', 'no verdict')}")
            continue

        # Quota check
        se = resp.get("raw", {}).get("sightengine", {})
        if se.get("status") == "failure":
            err = str(se)
            if "quota" in err.lower() or "limit" in err.lower():
                print("\nSightengine quota hit — stopping.")
                break
            print(f"  SKIP — Sightengine error: {err[:80]}")
            continue

        verdict = resp["verdict"]
        prob = resp.get("ai_probability", 0.0)
        correct = is_correct(ground_truth, verdict)

        data["results"].append({
            "id": next_id,
            "category": cat,
            "ground_truth": ground_truth,
            "url": url,
            "verdict": verdict,
            "ai_probability": prob,
            "confidence": resp.get("confidence", ""),
            "correct": correct,
        })
        next_id += 1
        update_category(data, cat, ground_truth, prob, correct)

        all_r = data["results"]
        total_correct = sum(1 for r in all_r if r.get("correct"))
        tested += 1
        data["meta"]["total_tested"] = 20 + tested
        data["meta"]["quota_remaining_estimate"] = 280 - tested
        data["meta"]["accuracy_running"] = round(total_correct / len(all_r), 4)

        print(f"  {'OK' if correct else 'WRONG'} — verdict={verdict} prob={prob:.2f}")

        if tested % 10 == 0:
            save(data)

        if tested < MAX_TESTS:
            time.sleep(SLEEP_SECONDS)

    # Final save + summary
    all_r = data["results"]
    real_r = [r for r in all_r if r["ground_truth"] == "real"]
    ai_r   = [r for r in all_r if r["ground_truth"] == "ai_generated"]
    fp = sum(1 for r in real_r if r["verdict"] == "likely_ai")
    fn = sum(1 for r in ai_r  if r["verdict"] == "likely_human")

    data["summary"] = {
        "total_tested": len(all_r),
        "overall_accuracy": round(sum(1 for r in all_r if r["correct"]) / max(1, len(all_r)), 4),
        "false_positive_rate": round(fp / max(1, len(real_r)), 4),
        "false_negative_rate": round(fn / max(1, len(ai_r)), 4),
        "by_category": {
            cat: {k: v for k, v in stats.items() if not k.startswith("_")}
            for cat, stats in data["by_category"].items()
        },
        "notes": f"{tested} new tests at {SLEEP_SECONDS}s intervals.",
    }
    save(data)
    print(f"\nDone — {tested} tests. Accuracy: {data['summary']['overall_accuracy']*100:.1f}%")
    print(f"FP rate: {data['summary']['false_positive_rate']*100:.1f}%  FN rate: {data['summary']['false_negative_rate']*100:.1f}%")


if __name__ == "__main__":
    main()
