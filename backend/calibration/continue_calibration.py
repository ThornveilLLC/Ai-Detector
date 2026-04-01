#!/usr/bin/env python
"""
Continue social media calibration from where we left off.
Picks up after portrait (20 tested), continues food -> landscape -> art -> fitness -> pets -> fashion -> video_thumbnail
Writes to disk every 10 successful results. Stops on quota error.
"""

import json
import subprocess
import time
from datetime import datetime, timezone

OUTPUT = "C:/Users/ckbaw/Desktop/Thornveil_LLC/ai-detector/backend/calibration/social_media_results.json"
BACKEND = "http://localhost:8001/api/scan"

# ========================
# URL LISTS - remaining categories only (portrait already done)
# ========================

FOOD_REAL = [
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Good_Food_Display_-_NCI_Visuals_Online.jpg/640px-Good_Food_Display_-_NCI_Visuals_Online.jpg", "food", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Food_at_wedding.jpg/1200px-Food_at_wedding.jpg", "food", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/Big_Mac_hamburger.jpg/1200px-Big_Mac_hamburger.jpg", "food", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/1/15/Burger_King_Premium_Alaskan_Fish_Sandwich.jpg/1200px-Burger_King_Premium_Alaskan_Fish_Sandwich.jpg", "food", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/A_small_cup_of_coffee.JPG/640px-A_small_cup_of_coffee.JPG", "food", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/Biryani_Home_Cooked.jpg/640px-Biryani_Home_Cooked.jpg", "food", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/9/90/Hapus_Mango.jpg/640px-Hapus_Mango.jpg", "food", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a3/Eq_it-na_pizza-margherita_sep2005_sml.jpg/640px-Eq_it-na_pizza-margherita_sep2005_sml.jpg", "food", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/4/44/Cheeseburger.jpg/640px-Cheeseburger.jpg", "food", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/7/7d/Assorted_cheeses.jpg/640px-Assorted_cheeses.jpg", "food", "real"),
]

FOOD_AI = [
    ("https://image.lexica.art/md2_webp/1e209904-6a7f-4a62-bbaf-5ac96a286374", "food", "ai_generated"),
    ("https://image.lexica.art/md2_webp/251d827f-4eb2-48f6-baa3-4384fe796610", "food", "ai_generated"),
    ("https://image.lexica.art/md2_webp/261f44f2-cd78-4068-af99-584c6f6ac288", "food", "ai_generated"),
    ("https://image.lexica.art/md2_webp/26a9441c-8a7e-471f-a938-43cd89d3abed", "food", "ai_generated"),
    ("https://image.lexica.art/md2_webp/219a6f8f-c843-490b-b14b-e2bb9bb08137", "food", "ai_generated"),
    ("https://image.lexica.art/md2_webp/16978848-b4df-474a-870d-1590572472df", "food", "ai_generated"),
    ("https://image.lexica.art/md2_webp/1cc6088c-cdff-431d-9fcf-39b5aec3ed3b", "food", "ai_generated"),
    ("https://image.lexica.art/md2_webp/1a24f91d-68e8-40ff-877c-0b3c97fb748c", "food", "ai_generated"),
    ("https://image.lexica.art/md2_webp/10e57c91-0f6b-4c5b-aa4c-d0412205b998", "food", "ai_generated"),
    ("https://image.lexica.art/md2_webp/1576db8c-f71b-4f1b-90d5-ee17c194fd63", "food", "ai_generated"),
]

LANDSCAPE_REAL = [
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/9/97/The_Earth_seen_from_Apollo_17.jpg/640px-The_Earth_seen_from_Apollo_17.jpg", "landscape", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/1/13/Sahara_2006.jpg/640px-Sahara_2006.jpg", "landscape", "real"),
    ("https://picsum.photos/id/200/800/600", "landscape", "real"),
    ("https://picsum.photos/id/250/800/600", "landscape", "real"),
    ("https://picsum.photos/id/300/800/600", "landscape", "real"),
    ("https://picsum.photos/id/350/800/600", "landscape", "real"),
    ("https://picsum.photos/id/400/800/600", "landscape", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Jackrabbit.jpg/640px-Jackrabbit.jpg", "landscape", "real"),
    ("https://picsum.photos/id/230/800/600", "landscape", "real"),
    ("https://picsum.photos/id/280/800/600", "landscape", "real"),
]

LANDSCAPE_AI = [
    ("https://image.lexica.art/md2_webp/20c2353f-6332-418b-9a6b-ef1a71623bb2", "landscape", "ai_generated"),
    ("https://image.lexica.art/md2_webp/431ea5df-34b8-4837-8b2f-4083f72e3627", "landscape", "ai_generated"),
    ("https://image.lexica.art/md2_webp/43494151-8556-4e45-9495-3e328aaf44d6", "landscape", "ai_generated"),
    ("https://image.lexica.art/md2_webp/48775d36-c1f5-47a7-a26f-8ffc8e61bcfa", "landscape", "ai_generated"),
    ("https://image.lexica.art/md2_webp/488b425a-c5a3-43bf-ae9f-5ee1d32c26a3", "landscape", "ai_generated"),
    ("https://image.lexica.art/md2_webp/3ed14f41-7872-4dea-b7de-870f480877f4", "landscape", "ai_generated"),
    ("https://image.lexica.art/md2_webp/30672488-9133-4a31-a100-14099a8f6b80", "landscape", "ai_generated"),
    ("https://image.lexica.art/md2_webp/3b224c08-354c-4f2b-b87f-4be5a249f7a9", "landscape", "ai_generated"),
    ("https://image.lexica.art/md2_webp/2bedda0b-4937-4b31-aadb-1005c1df9f85", "landscape", "ai_generated"),
    ("https://image.lexica.art/md2_webp/2d1286e5-2bba-49f2-b950-ab12b2a1bc8b", "landscape", "ai_generated"),
]

ART_REAL = [
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/e/ec/Mona_Lisa%2C_by_Leonardo_da_Vinci%2C_from_C2RMF_retouched.jpg/480px-Mona_Lisa%2C_by_Leonardo_da_Vinci%2C_from_C2RMF_retouched.jpg", "art", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/e/ea/Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg/640px-Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg", "art", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/The_Fighting_Temeraire%2C_JMW_Turner%2C_National_Gallery.jpg/640px-The_Fighting_Temeraire%2C_JMW_Turner%2C_National_Gallery.jpg", "art", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Tsunami_by_hokusai_19th_century.jpg/640px-Tsunami_by_hokusai_19th_century.jpg", "art", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/d/da/The_Hay_Wain%2C_Constable%2C_1821.jpg/640px-The_Hay_Wain%2C_Constable%2C_1821.jpg", "art", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/3/30/Michelangelo_-_Creation_of_Adam_%28cropped%29.jpg/640px-Michelangelo_-_Creation_of_Adam_%28cropped%29.jpg", "art", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/7/73/Rembrandt_van_Rijn_-_Self-Portrait_-_Google_Art_Project.jpg/640px-Rembrandt_van_Rijn_-_Self-Portrait_-_Google_Art_Project.jpg", "art", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/1/17/Edvard_Munch%2C_1893%2C_The_Scream%2C_oil%2C_tempera_and_pastel_on_cardboard%2C_91_x_73_cm%2C_National_Gallery_of_Norway.jpg/480px-Edvard_Munch%2C_1893%2C_The_Scream%2C_oil%2C_tempera_and_pastel_on_cardboard%2C_91_x_73_cm%2C_National_Gallery_of_Norway.jpg", "art", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/d/df/Winslow_Homer_-_Snap_the_Whip.jpg/640px-Winslow_Homer_-_Snap_the_Whip.jpg", "art", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/f/f4/The_Swing_-_Fragonard.jpg/480px-The_Swing_-_Fragonard.jpg", "art", "real"),
]

ART_AI = [
    ("https://image.lexica.art/md2_webp/28a3a9e4-37ec-4f47-9d34-ea19d2ba7d40", "art", "ai_generated"),
    ("https://image.lexica.art/md2_webp/2ce597cb-6809-4e27-92c3-078b62c714a3", "art", "ai_generated"),
    ("https://image.lexica.art/md2_webp/2d69e174-ba4b-47f3-9c75-139f2259a783", "art", "ai_generated"),
    ("https://image.lexica.art/md2_webp/2d08923c-5aa9-4f31-950d-9612302a1251", "art", "ai_generated"),
    ("https://image.lexica.art/md2_webp/2ad786bb-563f-4653-9abe-ee2c34849748", "art", "ai_generated"),
    ("https://image.lexica.art/md2_webp/1d9f20fb-2141-45bd-9d9e-68b3e17fc178", "art", "ai_generated"),
    ("https://image.lexica.art/md2_webp/1f52de9a-3ce7-4706-a499-bd11115b140c", "art", "ai_generated"),
    ("https://image.lexica.art/md2_webp/22397953-32ff-4e5c-9872-e2947264d86a", "art", "ai_generated"),
    ("https://image.lexica.art/md2_webp/274b7b1d-c0aa-4b8b-ba40-51e84dbfa0d4", "art", "ai_generated"),
    ("https://image.lexica.art/md2_webp/283e96b3-44bd-4bca-88b7-a6352e4e1f7c", "art", "ai_generated"),
]

FITNESS_REAL = [
    ("https://img.youtube.com/vi/HKJR64VrxRQ/maxresdefault.jpg", "fitness", "real"),
    ("https://img.youtube.com/vi/vc1E5CfRfos/maxresdefault.jpg", "fitness", "real"),
    ("https://img.youtube.com/vi/cbKkB3POqaY/maxresdefault.jpg", "fitness", "real"),
    ("https://img.youtube.com/vi/Y1EH5S7BKIQ/maxresdefault.jpg", "fitness", "real"),
    ("https://img.youtube.com/vi/4Bo2Mgs9VJQ/maxresdefault.jpg", "fitness", "real"),
    ("https://img.youtube.com/vi/g_tea8ZNk5A/maxresdefault.jpg", "fitness", "real"),
    ("https://img.youtube.com/vi/J0YMkFbm3M4/maxresdefault.jpg", "fitness", "real"),
    ("https://img.youtube.com/vi/oBu-pQG6sTY/maxresdefault.jpg", "fitness", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Camponotus_flavomarginatus_ant.jpg/640px-Camponotus_flavomarginatus_ant.jpg", "fitness", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/1/18/Dog_Breeds.jpg/640px-Dog_Breeds.jpg", "fitness", "real"),
]

FITNESS_AI = [
    ("https://image.lexica.art/md2_webp/34ba000f-b770-4bcd-9055-6fc8560decda", "fitness", "ai_generated"),
    ("https://image.lexica.art/md2_webp/36529cbf-c453-41bd-98ce-6e75ccee640b", "fitness", "ai_generated"),
    ("https://image.lexica.art/md2_webp/3c1dd298-56ea-4acc-9255-21deaed12634", "fitness", "ai_generated"),
    ("https://image.lexica.art/md2_webp/38951d7f-431d-430c-a193-15c460f2daab", "fitness", "ai_generated"),
    ("https://image.lexica.art/md2_webp/34c4b9c3-3b1f-4d49-b0d0-b36d94d7975b", "fitness", "ai_generated"),
    ("https://image.lexica.art/md2_webp/3512072e-8fa5-479a-8b62-59ed2cfdd7a5", "fitness", "ai_generated"),
    ("https://image.lexica.art/md2_webp/2d9555b8-c9f7-4953-b5bb-78041d733fb3", "fitness", "ai_generated"),
    ("https://image.lexica.art/md2_webp/2ea94e52-18a5-4077-aa69-801cf9891042", "fitness", "ai_generated"),
    ("https://image.lexica.art/md2_webp/33be04b3-de71-4df0-bd79-72da05113ae9", "fitness", "ai_generated"),
    ("https://image.lexica.art/md2_webp/1d62ff6d-b7bc-4aa2-82d0-2bbdf77367a7", "fitness", "ai_generated"),
]

PETS_REAL = [
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/YellowLabradorLooking_new.jpg/640px-YellowLabradorLooking_new.jpg", "pets", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/0/0b/Cat_poster_1.jpg/640px-Cat_poster_1.jpg", "pets", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/b/bb/Kittyply_edit1.jpg/640px-Kittyply_edit1.jpg", "pets", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/1/14/Gatto_europeo4.jpg/640px-Gatto_europeo4.jpg", "pets", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/6/60/Standing_jaguar.jpg/640px-Standing_jaguar.jpg", "pets", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/4/43/Cute_dog.jpg/640px-Cute_dog.jpg", "pets", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/1/18/Dog_Breeds.jpg/640px-Dog_Breeds.jpg", "pets", "real"),
    ("https://picsum.photos/id/219/800/600", "pets", "real"),
    ("https://picsum.photos/id/237/800/600", "pets", "real"),
    ("https://picsum.photos/id/242/800/600", "pets", "real"),
]

PETS_AI = [
    ("https://image.lexica.art/md2_webp/1eea74a3-ff0b-4959-bb1f-c5c2a1c48f3d", "pets", "ai_generated"),
    ("https://image.lexica.art/md2_webp/30552140-193e-43ec-b188-55a78fb3bf52", "pets", "ai_generated"),
    ("https://image.lexica.art/md2_webp/3437f669-a6d4-4f62-b2e1-8502de34bd0d", "pets", "ai_generated"),
    ("https://image.lexica.art/md2_webp/355ad1db-f608-46f1-a90c-29ad75f6b6a6", "pets", "ai_generated"),
    ("https://image.lexica.art/md2_webp/2ee495a5-d16b-4746-bc49-f9e5529526b1", "pets", "ai_generated"),
    ("https://image.lexica.art/md2_webp/296b99ca-c140-45b3-8f8c-2b0056734ca1", "pets", "ai_generated"),
    ("https://image.lexica.art/md2_webp/2c60f12a-d471-4d04-82f6-a6ed0455f839", "pets", "ai_generated"),
    ("https://image.lexica.art/md2_webp/2ec53f09-af62-4ff5-b31f-550fc90518ea", "pets", "ai_generated"),
    ("https://image.lexica.art/md2_webp/27c2b6af-31dc-4def-acb0-e274d3a5ccd7", "pets", "ai_generated"),
    ("https://image.lexica.art/md2_webp/20d374aa-ae2b-4116-8c60-9349d7b40567", "pets", "ai_generated"),
]

FASHION_REAL = [
    ("https://img.youtube.com/vi/whW4cqTHdWM/maxresdefault.jpg", "fashion", "real"),
    ("https://img.youtube.com/vi/B_0aQ-CDQ3w/maxresdefault.jpg", "fashion", "real"),
    ("https://img.youtube.com/vi/gJBGAaQA-Yg/maxresdefault.jpg", "fashion", "real"),
    ("https://img.youtube.com/vi/ykW9yjJlrC8/maxresdefault.jpg", "fashion", "real"),
    ("https://img.youtube.com/vi/XqZsoesa55w/maxresdefault.jpg", "fashion", "real"),
    ("https://img.youtube.com/vi/A_hvY3xA2sI/maxresdefault.jpg", "fashion", "real"),
    ("https://img.youtube.com/vi/YwUFaKi85oM/maxresdefault.jpg", "fashion", "real"),
    ("https://img.youtube.com/vi/w4tPpFKF70w/maxresdefault.jpg", "fashion", "real"),
    ("https://img.youtube.com/vi/DEyXaX2-lKw/hqdefault.jpg", "fashion", "real"),
    ("https://img.youtube.com/vi/d1HCvW-cz0I/hqdefault.jpg", "fashion", "real"),
]

FASHION_AI = [
    ("https://image.lexica.art/md2_webp/315327a2-8820-4d02-8b16-4faccd8bd326", "fashion", "ai_generated"),
    ("https://image.lexica.art/md2_webp/297f2352-3dc4-405f-b308-6683f87c5045", "fashion", "ai_generated"),
    ("https://image.lexica.art/md2_webp/301e7585-d5f5-4afe-9374-59beb9de96d0", "fashion", "ai_generated"),
    ("https://image.lexica.art/md2_webp/3057c641-9c4c-41a3-9e4a-f2d6fc9c80a6", "fashion", "ai_generated"),
    ("https://image.lexica.art/md2_webp/1787da4b-e4bd-408d-b601-b09836e02add", "fashion", "ai_generated"),
    ("https://image.lexica.art/md2_webp/22637b8e-2490-4e19-97c0-2ae4cc3a0323", "fashion", "ai_generated"),
    ("https://image.lexica.art/md2_webp/26d1cbc8-edeb-4214-81cc-ac8455dff8b7", "fashion", "ai_generated"),
    ("https://image.lexica.art/md2_webp/1dc13954-0d71-4c6b-b20b-57d6ac92931c", "fashion", "ai_generated"),
    ("https://image.lexica.art/md2_webp/0afc68c2-b9e3-4864-ae8b-e3c6f42aefc0", "fashion", "ai_generated"),
    ("https://image.lexica.art/md2_webp/0b0792e6-9bd5-425b-af97-1a00001d0a55", "fashion", "ai_generated"),
]

VIDEO_THUMB_REAL = [
    ("https://img.youtube.com/vi/dQw4w9WgXcQ/hqdefault.jpg", "video_thumbnail", "real"),
    ("https://img.youtube.com/vi/9bZkp7q19f0/hqdefault.jpg", "video_thumbnail", "real"),
    ("https://img.youtube.com/vi/kJQP7kiw5Fk/hqdefault.jpg", "video_thumbnail", "real"),
    ("https://img.youtube.com/vi/jNQXAC9IVRw/hqdefault.jpg", "video_thumbnail", "real"),
    ("https://img.youtube.com/vi/JGwWNGJdvx8/hqdefault.jpg", "video_thumbnail", "real"),
    ("https://img.youtube.com/vi/OPf0YbXqDm0/hqdefault.jpg", "video_thumbnail", "real"),
    ("https://img.youtube.com/vi/60ItHLz5WEA/hqdefault.jpg", "video_thumbnail", "real"),
    ("https://img.youtube.com/vi/YqeW9_5kURI/hqdefault.jpg", "video_thumbnail", "real"),
    ("https://img.youtube.com/vi/HKJR64VrxRQ/hqdefault.jpg", "video_thumbnail", "real"),
    ("https://img.youtube.com/vi/4HqzYnRVWi8/hqdefault.jpg", "video_thumbnail", "real"),
]

VIDEO_THUMB_AI = [
    ("https://image.lexica.art/md2_webp/4c5f6e65-c8b7-4c07-9c1e-3f7b67b48320", "video_thumbnail", "ai_generated"),
    ("https://image.lexica.art/md2_webp/545f701d-3c77-4193-b8ce-e9170f47177b", "video_thumbnail", "ai_generated"),
    ("https://image.lexica.art/md2_webp/54a83724-0454-4a92-a884-ce4c800ac043", "video_thumbnail", "ai_generated"),
    ("https://image.lexica.art/md2_webp/5128e577-3ff4-44af-aecc-d2a68c467d83", "video_thumbnail", "ai_generated"),
    ("https://image.lexica.art/md2_webp/3ded5227-e483-476d-a31b-f40893297915", "video_thumbnail", "ai_generated"),
    ("https://image.lexica.art/md2_webp/41206351-1bf0-47e6-a461-880c5fc18cd2", "video_thumbnail", "ai_generated"),
    ("https://image.lexica.art/md2_webp/2be9ac35-1d82-40ab-9e29-0dd236bf90f3", "video_thumbnail", "ai_generated"),
    ("https://image.lexica.art/md2_webp/35acddd7-14a7-4b1c-b99e-94e6cbe506a2", "video_thumbnail", "ai_generated"),
    ("https://image.lexica.art/md2_webp/364ea3de-1fa4-471b-9113-21d98d7d2d62", "video_thumbnail", "ai_generated"),
    ("https://image.lexica.art/md2_webp/1c2eee42-659e-42f9-8d93-712723e47212", "video_thumbnail", "ai_generated"),
]

# Build test list: real then AI for each category
ALL_TESTS = []
for real_list, ai_list in [
    (FOOD_REAL, FOOD_AI),
    (LANDSCAPE_REAL, LANDSCAPE_AI),
    (ART_REAL, ART_AI),
    (FITNESS_REAL, FITNESS_AI),
    (PETS_REAL, PETS_AI),
    (FASHION_REAL, FASHION_AI),
    (VIDEO_THUMB_REAL, VIDEO_THUMB_AI),
]:
    ALL_TESTS.extend(real_list)
    ALL_TESTS.extend(ai_list)

print(f"Remaining tests planned: {len(ALL_TESTS)}")
print(f"Total target: 20 (portrait done) + {len(ALL_TESTS)} = {20 + len(ALL_TESTS)}")


def get_verdict(ai_prob):
    if ai_prob < 0.40:
        return "likely_human"
    elif ai_prob >= 0.65:
        return "likely_ai"
    else:
        return "uncertain"


def is_correct(ground_truth, ai_prob):
    if ground_truth == "real":
        return ai_prob < 0.40
    else:
        return ai_prob >= 0.65


def load_existing():
    """Load existing results from disk."""
    with open(OUTPUT) as f:
        data = json.load(f)

    results = data.get("results", [])
    # Next ID is max existing ID + 1
    next_id = max((r["id"] for r in results), default=0) + 1

    # Rebuild category stats from existing results
    CATEGORIES = ["portrait", "food", "landscape", "art", "fitness", "pets", "fashion", "video_thumbnail"]
    by_cat_stats = {
        cat: {"total": 0, "correct": 0, "sum_prob_real": 0.0, "sum_prob_ai": 0.0, "count_real": 0, "count_ai": 0}
        for cat in CATEGORIES
    }
    total_tested = 0
    total_correct = 0
    false_pos = 0
    false_neg = 0

    for r in results:
        if "error" in r or "ai_probability" not in r:
            continue
        cat = r["category"]
        ground_truth = r["ground_truth"]
        ai_prob = r["ai_probability"]
        correct = r["correct"]

        total_tested += 1
        cat_stats = by_cat_stats[cat]
        cat_stats["total"] += 1
        if correct:
            total_correct += 1
            cat_stats["correct"] += 1

        if ground_truth == "real":
            cat_stats["count_real"] += 1
            cat_stats["sum_prob_real"] += ai_prob
            if ai_prob >= 0.65:
                false_pos += 1
        else:
            cat_stats["count_ai"] += 1
            cat_stats["sum_prob_ai"] += ai_prob
            if ai_prob < 0.40:
                false_neg += 1

    print(f"Loaded {len(results)} existing entries, {total_tested} successful tests")
    print(f"Starting from ID {next_id}")
    return results, by_cat_stats, total_tested, total_correct, false_pos, false_neg, next_id


def write_results(results, by_cat_stats, total_tested, total_correct, false_pos, false_neg, started_at):
    now = datetime.now(timezone.utc).isoformat()
    accuracy = total_correct / total_tested if total_tested > 0 else 0.0

    CATEGORIES = ["portrait", "food", "landscape", "art", "fitness", "pets", "fashion", "video_thumbnail"]
    by_category = {}
    for cat in CATEGORIES:
        stats = by_cat_stats[cat]
        t = stats["total"]
        c = stats["correct"]
        acc = c / t if t > 0 else 0.0
        avg_real = stats["sum_prob_real"] / stats["count_real"] if stats["count_real"] > 0 else 0.0
        avg_ai = stats["sum_prob_ai"] / stats["count_ai"] if stats["count_ai"] > 0 else 0.0
        by_category[cat] = {
            "total": t,
            "correct": c,
            "accuracy": round(acc, 4),
            "avg_prob_real": round(avg_real, 4),
            "avg_prob_ai": round(avg_ai, 4),
        }

    output = {
        "meta": {
            "started_at": started_at,
            "last_updated": now,
            "total_tested": total_tested,
            "target": 300,
            "quota_remaining_estimate": 300 - total_tested,
            "accuracy_running": round(accuracy, 4),
        },
        "by_category": by_category,
        "results": results,
    }

    with open(OUTPUT, "w") as f:
        json.dump(output, f, indent=2)

    print(f"  [SAVED] total={total_tested} correct={total_correct} accuracy={accuracy:.3f}")


def scan_image(test_id, url, category, ground_truth):
    try:
        result = subprocess.run(
            ["curl", "-s", "-X", "POST", BACKEND, "-F", f"image_url={url}"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        response_text = result.stdout.strip()
    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT")
        return None, "timeout"
    except Exception as e:
        print(f"  ERROR: {e}")
        return None, str(e)

    if not response_text:
        print(f"  SKIP: empty response")
        return None, "empty response"

    try:
        data = json.loads(response_text)
    except json.JSONDecodeError:
        print(f"  SKIP: invalid JSON: {response_text[:100]}")
        return None, "invalid JSON"

    detail = data.get("detail", "")
    if isinstance(detail, str) and any(kw in detail.lower() for kw in ["quota", "rate limit", "credit", "operations exceeded", "usage_limit", "daily"]):
        print(f"  QUOTA ERROR: {detail[:200]}")
        return None, "QUOTA_ERROR"

    if "detail" in data:
        print(f"  SKIP (error): {str(detail)[:100]}")
        return {
            "id": test_id,
            "category": category,
            "ground_truth": ground_truth,
            "url": url,
            "error": str(detail)[:200],
            "correct": False,
        }, "error"

    ai_prob = data.get("ai_probability", 0.5)
    verdict = data.get("verdict", get_verdict(ai_prob))
    confidence = data.get("confidence", "unknown")
    correct = is_correct(ground_truth, ai_prob)

    print(f"  verdict={verdict} ai_prob={ai_prob:.2f} correct={correct}")

    return {
        "id": test_id,
        "category": category,
        "ground_truth": ground_truth,
        "url": url,
        "verdict": verdict,
        "ai_probability": ai_prob,
        "confidence": confidence,
        "correct": correct,
    }, "ok"


# Load existing state
results, by_cat_stats, total_tested, total_correct, false_pos, false_neg, next_id = load_existing()

# Preserve original started_at
with open(OUTPUT) as f:
    existing_data = json.load(f)
started_at = existing_data["meta"]["started_at"]

print(f"Continuing calibration: {len(ALL_TESTS)} remaining tests")
print(f"Backend: {BACKEND}")
print(f"Output: {OUTPUT}")
print("-" * 60)

quota_hit = False
for i, (url, category, ground_truth) in enumerate(ALL_TESTS):
    test_id = next_id + i
    print(f"[{test_id}] {category} ({ground_truth}) {url[:70]}...")

    result, status = scan_image(test_id, url, category, ground_truth)

    if status == "QUOTA_ERROR":
        print("QUOTA LIMIT REACHED - stopping immediately!")
        quota_hit = True
        break

    if result is not None:
        results.append(result)

        if status == "ok":
            total_tested += 1
            cat_stats = by_cat_stats[category]
            cat_stats["total"] += 1
            ai_prob = result["ai_probability"]
            correct = result["correct"]

            if correct:
                total_correct += 1
                cat_stats["correct"] += 1

            if ground_truth == "real":
                cat_stats["count_real"] += 1
                cat_stats["sum_prob_real"] += ai_prob
                if ai_prob >= 0.65:
                    false_pos += 1
            else:
                cat_stats["count_ai"] += 1
                cat_stats["sum_prob_ai"] += ai_prob
                if ai_prob < 0.40:
                    false_neg += 1

    # Write every 10 successful tests
    if total_tested > 0 and total_tested % 10 == 0:
        write_results(results, by_cat_stats, total_tested, total_correct, false_pos, false_neg, started_at)

    # Sleep 10s between requests
    if i < len(ALL_TESTS) - 1 and not quota_hit:
        print(f"  sleeping 10s...")
        time.sleep(10)

# Final write
write_results(results, by_cat_stats, total_tested, total_correct, false_pos, false_neg, started_at)

overall_acc = total_correct / total_tested if total_tested > 0 else 0.0
real_total = sum(s["count_real"] for s in by_cat_stats.values())
ai_total = sum(s["count_ai"] for s in by_cat_stats.values())
fp_rate = false_pos / real_total if real_total > 0 else 0.0
fn_rate = false_neg / ai_total if ai_total > 0 else 0.0

cats_with_data = [(cat, by_cat_stats[cat]) for cat in by_cat_stats if by_cat_stats[cat]["total"] > 0]

print("\n" + "=" * 60)
if quota_hit:
    print("STOPPED DUE TO QUOTA LIMIT")
    print("Re-run this script after quota resets (likely midnight UTC or US timezone midnight)")
else:
    print("CALIBRATION COMPLETE")
print(f"Total tested so far: {total_tested}")
print(f"Overall accuracy: {overall_acc:.3f}")
print(f"False positive rate: {fp_rate:.3f}")
print(f"False negative rate: {fn_rate:.3f}")
print(f"Results saved to: {OUTPUT}")
print()
print("Per-category breakdown:")
for cat, stats in by_cat_stats.items():
    if stats["total"] > 0:
        acc = stats["correct"] / stats["total"]
        print(f"  {cat:20s}: {stats['total']:3d} tested, {acc:.0%} accuracy")
