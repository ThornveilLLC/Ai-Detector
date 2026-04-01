"""
test_image_accuracy.py — Expanded Sightengine image calibration v2.
Uses verified Lexica.art UUIDs (from continue_calibration.py) and Wikimedia real images.
100 samples across 5 categories (food, landscape, art, fitness, pets).
Saves to image_accuracy_v2_results.json every 10 tests.

Note: classic_art category is a key edge case — real oil paintings (Van Gogh, Mona Lisa)
could potentially trigger Sightengine's genai model. Results here are a product signal.

Usage (from ai-detector/backend/calibration/):
    python test_image_accuracy.py
    (backend must be running: uvicorn main:app --port 8001)
"""

import json
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

API_URL       = "http://localhost:8001/api/scan"
OUTPUT_FILE   = Path(__file__).parent / "image_accuracy_v2_results.json"
SLEEP_SECONDS = 10
MAX_TESTS     = 110  # cap slightly above 100 to absorb any dead Lexica URLs

# ---------------------------------------------------------------------------
# URL lists — verified sources only (no placeholder UUIDs)
# Real: Wikimedia Commons + Picsum  |  AI: verified Lexica.art UUIDs
# ---------------------------------------------------------------------------

CATEGORIES = {
    "food": {
        "real": [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Good_Food_Display_-_NCI_Visuals_Online.jpg/640px-Good_Food_Display_-_NCI_Visuals_Online.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Food_at_wedding.jpg/1200px-Food_at_wedding.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/Big_Mac_hamburger.jpg/1200px-Big_Mac_hamburger.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/1/15/Burger_King_Premium_Alaskan_Fish_Sandwich.jpg/1200px-Burger_King_Premium_Alaskan_Fish_Sandwich.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/A_small_cup_of_coffee.JPG/640px-A_small_cup_of_coffee.JPG",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/Biryani_Home_Cooked.jpg/640px-Biryani_Home_Cooked.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/9/90/Hapus_Mango.jpg/640px-Hapus_Mango.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a3/Eq_it-na_pizza-margherita_sep2005_sml.jpg/640px-Eq_it-na_pizza-margherita_sep2005_sml.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/4/44/Cheeseburger.jpg/640px-Cheeseburger.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7d/Assorted_cheeses.jpg/640px-Assorted_cheeses.jpg",
        ],
        "ai_generated": [
            "https://image.lexica.art/md2_webp/1e209904-6a7f-4a62-bbaf-5ac96a286374",
            "https://image.lexica.art/md2_webp/251d827f-4eb2-48f6-baa3-4384fe796610",
            "https://image.lexica.art/md2_webp/261f44f2-cd78-4068-af99-584c6f6ac288",
            "https://image.lexica.art/md2_webp/26a9441c-8a7e-471f-a938-43cd89d3abed",
            "https://image.lexica.art/md2_webp/219a6f8f-c843-490b-b14b-e2bb9bb08137",
            "https://image.lexica.art/md2_webp/16978848-b4df-474a-870d-1590572472df",
            "https://image.lexica.art/md2_webp/1cc6088c-cdff-431d-9fcf-39b5aec3ed3b",
            "https://image.lexica.art/md2_webp/1a24f91d-68e8-40ff-877c-0b3c97fb748c",
            "https://image.lexica.art/md2_webp/10e57c91-0f6b-4c5b-aa4c-d0412205b998",
            "https://image.lexica.art/md2_webp/1576db8c-f71b-4f1b-90d5-ee17c194fd63",
        ],
    },
    "landscape": {
        "real": [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/9/97/The_Earth_seen_from_Apollo_17.jpg/640px-The_Earth_seen_from_Apollo_17.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/1/13/Sahara_2006.jpg/640px-Sahara_2006.jpg",
            "https://picsum.photos/id/200/800/600",
            "https://picsum.photos/id/250/800/600",
            "https://picsum.photos/id/300/800/600",
            "https://picsum.photos/id/350/800/600",
            "https://picsum.photos/id/400/800/600",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Jackrabbit.jpg/640px-Jackrabbit.jpg",
            "https://picsum.photos/id/230/800/600",
            "https://picsum.photos/id/280/800/600",
        ],
        "ai_generated": [
            "https://image.lexica.art/md2_webp/20c2353f-6332-418b-9a6b-ef1a71623bb2",
            "https://image.lexica.art/md2_webp/431ea5df-34b8-4837-8b2f-4083f72e3627",
            "https://image.lexica.art/md2_webp/43494151-8556-4e45-9495-3e328aaf44d6",
            "https://image.lexica.art/md2_webp/48775d36-c1f5-47a7-a26f-8ffc8e61bcfa",
            "https://image.lexica.art/md2_webp/488b425a-c5a3-43bf-ae9f-5ee1d32c26a3",
            "https://image.lexica.art/md2_webp/3ed14f41-7872-4dea-b7de-870f480877f4",
            "https://image.lexica.art/md2_webp/30672488-9133-4a31-a100-14099a8f6b80",
            "https://image.lexica.art/md2_webp/3b224c08-354c-4f2b-b87f-4be5a249f7a9",
            "https://image.lexica.art/md2_webp/2bedda0b-4937-4b31-aadb-1005c1df9f85",
            "https://image.lexica.art/md2_webp/2d1286e5-2bba-49f2-b950-ab12b2a1bc8b",
        ],
    },
    "classic_art": {  # EDGE CASE: real oil paintings that could look AI
        "real": [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ec/Mona_Lisa%2C_by_Leonardo_da_Vinci%2C_from_C2RMF_retouched.jpg/480px-Mona_Lisa%2C_by_Leonardo_da_Vinci%2C_from_C2RMF_retouched.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ea/Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg/640px-Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/The_Fighting_Temeraire%2C_JMW_Turner%2C_National_Gallery.jpg/640px-The_Fighting_Temeraire%2C_JMW_Turner%2C_National_Gallery.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Tsunami_by_hokusai_19th_century.jpg/640px-Tsunami_by_hokusai_19th_century.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/d/da/The_Hay_Wain%2C_Constable%2C_1821.jpg/640px-The_Hay_Wain%2C_Constable%2C_1821.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/3/30/Michelangelo_-_Creation_of_Adam_%28cropped%29.jpg/640px-Michelangelo_-_Creation_of_Adam_%28cropped%29.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/7/73/Rembrandt_van_Rijn_-_Self-Portrait_-_Google_Art_Project.jpg/640px-Rembrandt_van_Rijn_-_Self-Portrait_-_Google_Art_Project.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/1/17/Edvard_Munch%2C_1893%2C_The_Scream%2C_oil%2C_tempera_and_pastel_on_cardboard%2C_91_x_73_cm%2C_National_Gallery_of_Norway.jpg/480px-Edvard_Munch%2C_1893%2C_The_Scream%2C_oil%2C_tempera_and_pastel_on_cardboard%2C_91_x_73_cm%2C_National_Gallery_of_Norway.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/d/df/Winslow_Homer_-_Snap_the_Whip.jpg/640px-Winslow_Homer_-_Snap_the_Whip.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f4/The_Swing_-_Fragonard.jpg/480px-The_Swing_-_Fragonard.jpg",
        ],
        "ai_generated": [
            "https://image.lexica.art/md2_webp/28a3a9e4-37ec-4f47-9d34-ea19d2ba7d40",
            "https://image.lexica.art/md2_webp/2ce597cb-6809-4e27-92c3-078b62c714a3",
            "https://image.lexica.art/md2_webp/2d69e174-ba4b-47f3-9c75-139f2259a783",
            "https://image.lexica.art/md2_webp/2d08923c-5aa9-4f31-950d-9612302a1251",
            "https://image.lexica.art/md2_webp/2ad786bb-563f-4653-9abe-ee2c34849748",
            "https://image.lexica.art/md2_webp/1d9f20fb-2141-45bd-9d9e-68b3e17fc178",
            "https://image.lexica.art/md2_webp/1f52de9a-3ce7-4706-a499-bd11115b140c",
            "https://image.lexica.art/md2_webp/22397953-32ff-4e5c-9872-e2947264d86a",
            "https://image.lexica.art/md2_webp/274b7b1d-c0aa-4b8b-ba40-51e84dbfa0d4",
            "https://image.lexica.art/md2_webp/283e96b3-44bd-4bca-88b7-a6352e4e1f7c",
        ],
    },
    "fitness": {
        "real": [
            "https://img.youtube.com/vi/HKJR64VrxRQ/maxresdefault.jpg",
            "https://img.youtube.com/vi/vc1E5CfRfos/maxresdefault.jpg",
            "https://img.youtube.com/vi/cbKkB3POqaY/maxresdefault.jpg",
            "https://img.youtube.com/vi/Y1EH5S7BKIQ/maxresdefault.jpg",
            "https://img.youtube.com/vi/4Bo2Mgs9VJQ/maxresdefault.jpg",
            "https://img.youtube.com/vi/g_tea8ZNk5A/maxresdefault.jpg",
            "https://img.youtube.com/vi/J0YMkFbm3M4/maxresdefault.jpg",
            "https://img.youtube.com/vi/oBu-pQG6sTY/maxresdefault.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Camponotus_flavomarginatus_ant.jpg/640px-Camponotus_flavomarginatus_ant.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/1/18/Dog_Breeds.jpg/640px-Dog_Breeds.jpg",
        ],
        "ai_generated": [
            "https://image.lexica.art/md2_webp/34ba000f-b770-4bcd-9055-6fc8560decda",
            "https://image.lexica.art/md2_webp/36529cbf-c453-41bd-98ce-6e75ccee640b",
            "https://image.lexica.art/md2_webp/3c1dd298-56ea-4acc-9255-21deaed12634",
            "https://image.lexica.art/md2_webp/38951d7f-431d-430c-a193-15c460f2daab",
            "https://image.lexica.art/md2_webp/34c4b9c3-3b1f-4d49-b0d0-b36d94d7975b",
            "https://image.lexica.art/md2_webp/3512072e-8fa5-479a-8b62-59ed2cfdd7a5",
            "https://image.lexica.art/md2_webp/2d9555b8-c9f7-4953-b5bb-78041d733fb3",
            "https://image.lexica.art/md2_webp/2ea94e52-18a5-4077-aa69-801cf9891042",
            "https://image.lexica.art/md2_webp/33be04b3-de71-4df0-bd79-72da05113ae9",
            "https://image.lexica.art/md2_webp/1d62ff6d-b7bc-4aa2-82d0-2bbdf77367a7",
        ],
    },
    "pets": {
        "real": [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/YellowLabradorLooking_new.jpg/640px-YellowLabradorLooking_new.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0b/Cat_poster_1.jpg/640px-Cat_poster_1.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bb/Kittyply_edit1.jpg/640px-Kittyply_edit1.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/1/14/Gatto_europeo4.jpg/640px-Gatto_europeo4.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/6/60/Standing_jaguar.jpg/640px-Standing_jaguar.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/4/43/Cute_dog.jpg/640px-Cute_dog.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/1/18/Dog_Breeds.jpg/640px-Dog_Breeds.jpg",
            "https://picsum.photos/id/219/800/600",
            "https://picsum.photos/id/237/800/600",
            "https://picsum.photos/id/242/800/600",
        ],
        "ai_generated": [
            "https://image.lexica.art/md2_webp/1eea74a3-ff0b-4959-bb1f-c5c2a1c48f3d",
            "https://image.lexica.art/md2_webp/30552140-193e-43ec-b188-55a78fb3bf52",
            "https://image.lexica.art/md2_webp/3437f669-a6d4-4f62-b2e1-8502de34bd0d",
            "https://image.lexica.art/md2_webp/355ad1db-f608-46f1-a90c-29ad75f6b6a6",
            "https://image.lexica.art/md2_webp/2ee495a5-d16b-4746-bc49-f9e5529526b1",
            "https://image.lexica.art/md2_webp/296b99ca-c140-45b3-8f8c-2b0056734ca1",
            "https://image.lexica.art/md2_webp/2c60f12a-d471-4d04-82f6-a6ed0455f839",
            "https://image.lexica.art/md2_webp/2ec53f09-af62-4ff5-b31f-550fc90518ea",
            "https://image.lexica.art/md2_webp/27c2b6af-31dc-4def-acb0-e274d3a5ccd7",
            "https://image.lexica.art/md2_webp/20d374aa-ae2b-4116-8c60-9349d7b40567",
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
            "total_tested": 0,
            "target": 100,
            "accuracy_running": 0.0,
            "version": "v2 — verified URLs only",
        },
        "by_category": {},
        "results": [],
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


def main():
    data = load_existing()
    queue = build_queue()
    tested = 0
    skipped = 0
    next_id = len(data["results"]) + 1

    print(f"Image accuracy v2 — {len(queue)} URLs, max {MAX_TESTS} tests, {SLEEP_SECONDS}s between each")
    print(f"Output: {OUTPUT_FILE}\n")

    for url, ground_truth, cat in queue:
        if tested >= MAX_TESTS:
            print(f"\nReached {MAX_TESTS} test cap.")
            break

        print(f"[{tested+1}/{MAX_TESTS}] {cat} | {ground_truth} | ...{url[-55:]}")
        resp = scan_image(url)

        if "verdict" not in resp:
            print(f"  SKIP — {resp.get('error', 'no verdict')}")
            skipped += 1
            continue

        se = resp.get("raw", {}).get("sightengine", {})
        if se.get("status") == "failure":
            err = str(se)
            if "quota" in err.lower() or "limit" in err.lower():
                print("\nSightengine quota hit — stopping.")
                break
            print(f"  SKIP — Sightengine error: {err[:80]}")
            skipped += 1
            continue

        verdict   = resp["verdict"]
        prob      = resp.get("ai_probability", 0.0)
        correct   = is_correct(ground_truth, verdict)
        suspected = resp.get("suspected_source")

        data["results"].append({
            "id": next_id,
            "category": cat,
            "ground_truth": ground_truth,
            "url": url,
            "verdict": verdict,
            "ai_probability": prob,
            "confidence": resp.get("confidence", ""),
            "suspected_source": suspected,
            "correct": correct,
        })
        next_id += 1
        update_category(data, cat, ground_truth, prob, correct)

        all_r = data["results"]
        total_correct = sum(1 for r in all_r if r.get("correct"))
        tested += 1
        data["meta"]["total_tested"] = tested
        data["meta"]["accuracy_running"] = round(total_correct / len(all_r), 4)

        label = "OK   " if correct else "WRONG"
        print(f"  {label} — verdict={verdict} prob={prob:.2f} suspected={suspected}")

        if tested % 10 == 0:
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

    # Classic art false-positive breakdown (product risk signal)
    art_real  = [r for r in real_r if r["category"] == "classic_art"]
    art_fp    = sum(1 for r in art_real if r["verdict"] == "likely_ai")

    data["summary"] = {
        "total_tested": len(all_r),
        "skipped": skipped,
        "real_count": len(real_r),
        "ai_count": len(ai_r),
        "overall_accuracy": round(sum(1 for r in all_r if r["correct"]) / max(1, len(all_r)), 4),
        "false_positive_rate": round(fp / max(1, len(real_r)), 4),
        "false_negative_rate": round(fn / max(1, len(ai_r)), 4),
        "uncertain_rate": round(unc / max(1, len(all_r)), 4),
        "avg_prob_real": round(sum(r["ai_probability"] for r in real_r) / max(1, len(real_r)), 4),
        "avg_prob_ai":   round(sum(r["ai_probability"] for r in ai_r)   / max(1, len(ai_r)), 4),
        "classic_art_fp_count": art_fp,
        "classic_art_fp_note": (
            "PRODUCT RISK: real classic paintings flagged as AI" if art_fp > 0
            else "Classic paintings correctly classified as human"
        ),
        "by_category": {
            cat: {k: v for k, v in stats.items() if not k.startswith("_")}
            for cat, stats in data["by_category"].items()
        },
        "notes": f"v2 — {tested} tests, {skipped} skipped. Verified Lexica UUIDs only.",
    }
    save(data)

    print(f"\nDone — {tested} tests, {skipped} skipped.")
    print(f"Accuracy: {data['summary']['overall_accuracy']*100:.1f}%")
    print(f"FP rate:  {data['summary']['false_positive_rate']*100:.1f}%  "
          f"FN rate: {data['summary']['false_negative_rate']*100:.1f}%")
    print(f"Classic art FP: {art_fp}/{len(art_real)} real paintings flagged as AI")


if __name__ == "__main__":
    main()
