#!/usr/bin/env bash
# Social media calibration test - 300 images across 8 categories
# Writes results continuously to social_media_results.json
# Sleeps 10s between every request

OUTPUT="C:/Users/ckbaw/Desktop/Thornveil_LLC/ai-detector/backend/calibration/social_media_results.json"
BACKEND="http://localhost:8001/api/scan"
STARTED_AT=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Initialize state
TOTAL=0
CORRECT=0
FALSE_POS=0
FALSE_NEG=0
QUOTA_ERROR=0

# Per-category counters (total, correct, sum_prob_real, sum_prob_ai, count_real, count_ai)
declare -A CAT_TOTAL CAT_CORRECT CAT_SUM_REAL CAT_SUM_AI CAT_COUNT_REAL CAT_COUNT_AI
for cat in portrait food landscape art fitness pets fashion video_thumbnail; do
    CAT_TOTAL[$cat]=0
    CAT_CORRECT[$cat]=0
    CAT_SUM_REAL[$cat]=0
    CAT_SUM_AI[$cat]=0
    CAT_COUNT_REAL[$cat]=0
    CAT_COUNT_AI[$cat]=0
done

RESULTS_JSON="[]"

update_file() {
    local accuracy=0
    if [ $TOTAL -gt 0 ]; then
        accuracy=$(echo "scale=4; $CORRECT / $TOTAL" | bc)
    fi
    local quota_est=$((300 - TOTAL))
    local now=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    # Build by_category JSON
    local by_cat="{"
    local first=1
    for cat in portrait food landscape art fitness pets fashion video_thumbnail; do
        local t=${CAT_TOTAL[$cat]}
        local c=${CAT_CORRECT[$cat]}
        local acc=0
        local avg_real=0
        local avg_ai=0
        if [ $t -gt 0 ]; then
            acc=$(echo "scale=4; $c / $t" | bc)
        fi
        if [ ${CAT_COUNT_REAL[$cat]} -gt 0 ]; then
            avg_real=$(echo "scale=4; ${CAT_SUM_REAL[$cat]} / ${CAT_COUNT_REAL[$cat]}" | bc)
        fi
        if [ ${CAT_COUNT_AI[$cat]} -gt 0 ]; then
            avg_ai=$(echo "scale=4; ${CAT_SUM_AI[$cat]} / ${CAT_COUNT_AI[$cat]}" | bc)
        fi
        if [ $first -eq 0 ]; then by_cat+=","; fi
        first=0
        by_cat+="\"$cat\":{\"total\":$t,\"correct\":$c,\"accuracy\":$acc,\"avg_prob_real\":$avg_real,\"avg_prob_ai\":$avg_ai}"
    done
    by_cat+="}"

    cat > "$OUTPUT" << JSONEOF
{
  "meta": {
    "started_at": "$STARTED_AT",
    "last_updated": "$now",
    "total_tested": $TOTAL,
    "target": 300,
    "quota_remaining_estimate": $quota_est,
    "accuracy_running": $accuracy
  },
  "by_category": $by_cat,
  "results": $RESULTS_JSON
}
JSONEOF
    echo "  [FILE UPDATED] total=$TOTAL correct=$CORRECT accuracy=$accuracy"
}

scan_image() {
    local id=$1
    local category=$2
    local ground_truth=$3
    local url=$4

    echo "[$id/$TOTAL_TARGET] cat=$category truth=$ground_truth url=${url:0:60}..."

    local response
    response=$(curl -s -X POST "$BACKEND" -F "image_url=$url" 2>&1)

    # Check for empty response
    if [ -z "$response" ]; then
        echo "  SKIP: empty response"
        RESULTS_JSON=$(echo "$RESULTS_JSON" | python3 -c "
import sys, json
results = json.load(sys.stdin)
results.append({'id': $id, 'category': '$category', 'ground_truth': '$ground_truth', 'url': '$url', 'error': 'empty response', 'correct': False})
print(json.dumps(results))
")
        return
    fi

    # Check for quota/rate error
    if echo "$response" | grep -qi "quota\|rate.limit\|operations.*exceed\|credit"; then
        echo "  QUOTA ERROR - stopping immediately"
        QUOTA_ERROR=1
        return 1
    fi

    # Check for backend/media error (don't count toward quota)
    if echo "$response" | grep -qi '"detail"'; then
        local err_msg
        err_msg=$(echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('detail','unknown error'))" 2>/dev/null || echo "backend error")
        echo "  SKIP (error): $err_msg"
        RESULTS_JSON=$(echo "$RESULTS_JSON" | python3 -c "
import sys, json
results = json.load(sys.stdin)
results.append({'id': $id, 'category': '$category', 'ground_truth': '$ground_truth', 'url': '$url', 'error': $(echo "$err_msg" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read().strip()))"), 'correct': False})
print(json.dumps(results))
")
        return
    fi

    # Parse successful response
    local result
    result=$(echo "$response" | python3 -c "
import sys, json

data = json.load(sys.stdin)
verdict = data.get('verdict', 'unknown')
ai_prob = data.get('ai_probability', 0.5)
confidence = data.get('confidence', 'unknown')
ground_truth = '$ground_truth'
category = '$category'
url = '$url'
id_num = $id

# Determine correct
correct = False
if ground_truth == 'real':
    correct = ai_prob < 0.40  # likely_human
elif ground_truth == 'ai_generated':
    correct = ai_prob >= 0.65  # likely_ai

result = {
    'id': id_num,
    'category': category,
    'ground_truth': ground_truth,
    'url': url,
    'verdict': verdict,
    'ai_probability': ai_prob,
    'confidence': confidence,
    'correct': correct
}
print(json.dumps(result))
" 2>/dev/null)

    if [ -z "$result" ]; then
        echo "  SKIP: parse error"
        return
    fi

    # Extract values for counters
    local ai_prob verdict correct
    ai_prob=$(echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['ai_probability'])")
    verdict=$(echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['verdict'])")
    correct=$(echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['correct'])")

    TOTAL=$((TOTAL + 1))
    CAT_TOTAL[$category]=$((${CAT_TOTAL[$category]} + 1))

    if [ "$correct" = "True" ]; then
        CORRECT=$((CORRECT + 1))
        CAT_CORRECT[$category]=$((${CAT_CORRECT[$category]} + 1))
    fi

    # Track false pos/neg
    if [ "$ground_truth" = "real" ] && echo "$ai_prob >= 0.65" | bc -l | grep -q "^1"; then
        FALSE_POS=$((FALSE_POS + 1))
    fi
    if [ "$ground_truth" = "ai_generated" ] && echo "$ai_prob < 0.40" | bc -l | grep -q "^1"; then
        FALSE_NEG=$((FALSE_NEG + 1))
    fi

    # Track category averages
    if [ "$ground_truth" = "real" ]; then
        CAT_COUNT_REAL[$category]=$((${CAT_COUNT_REAL[$category]} + 1))
        CAT_SUM_REAL[$category]=$(echo "${CAT_SUM_REAL[$category]} + $ai_prob" | bc)
    else
        CAT_COUNT_AI[$category]=$((${CAT_COUNT_AI[$category]} + 1))
        CAT_SUM_AI[$category]=$(echo "${CAT_SUM_AI[$category]} + $ai_prob" | bc)
    fi

    echo "  verdict=$verdict ai_prob=$ai_prob correct=$correct"

    # Append to results
    RESULTS_JSON=$(echo "$RESULTS_JSON" | python3 -c "
import sys, json
results = json.load(sys.stdin)
new_item = json.loads('$(echo "$result" | sed "s/'/\"/g")')
results.append(new_item)
print(json.dumps(results))
")
}

TOTAL_TARGET=300

# ========================
# URL LISTS
# ========================

# --- PORTRAITS ---
# Real portrait sources: YouTube thumbnails of talking head videos, Wikimedia portrait photos
PORTRAIT_REAL_URLS=(
    "https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg"
    "https://img.youtube.com/vi/9bZkp7q19f0/maxresdefault.jpg"
    "https://img.youtube.com/vi/kJQP7kiw5Fk/maxresdefault.jpg"
    "https://img.youtube.com/vi/JGwWNGJdvx8/maxresdefault.jpg"
    "https://img.youtube.com/vi/OPf0YbXqDm0/maxresdefault.jpg"
    "https://img.youtube.com/vi/60ItHLz5WEA/maxresdefault.jpg"
    "https://img.youtube.com/vi/2Vv-BfVoq4g/maxresdefault.jpg"
    "https://img.youtube.com/vi/YqeW9_5kURI/maxresdefault.jpg"
    "https://img.youtube.com/vi/CevxZvSJLk8/maxresdefault.jpg"
    "https://img.youtube.com/vi/09R8_2nJtjg/maxresdefault.jpg"
    "https://upload.wikimedia.org/wikipedia/commons/thumb/1/14/Gatto_europeo4.jpg/640px-Gatto_europeo4.jpg"
    "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Camponotus_flavomarginatus_ant.jpg/640px-Camponotus_flavomarginatus_ant.jpg"
    "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/280px-PNG_transparency_demonstration_1.png"
    "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Good_Food_Display_-_NCI_Visuals_Online.jpg/640px-Good_Food_Display_-_NCI_Visuals_Online.jpg"
    "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Jackrabbit.jpg/640px-Jackrabbit.jpg"
)

PORTRAIT_AI_URLS=(
    "https://image.lexica.art/md2_webp/448a754f-016b-4910-b0d5-65d681a1b816"
    "https://image.lexica.art/md2_webp/3b1be28c-ad04-49b4-8a25-6c3194bdf455"
    "https://image.lexica.art/md2_webp/48ed2c5f-f019-4c92-b21a-a3c1521cf0b3"
    "https://image.lexica.art/md2_webp/5c5570d9-1944-4135-8c2d-0e04c5b64884"
    "https://image.lexica.art/md2_webp/71800f72-17c7-46d8-aa67-329aab827874"
    "https://image.lexica.art/md2_webp/5302ac8c-1edf-47de-9bde-5a5d44ec15d9"
    "https://image.lexica.art/md2_webp/45e1f94f-492f-4022-a627-606e05c330ac"
    "https://image.lexica.art/md2_webp/353e94ce-af10-489c-8f16-ba936005e677"
    "https://image.lexica.art/md2_webp/39c94612-c1b9-4da3-8bdf-1edc7fd9bebf"
    "https://image.lexica.art/md2_webp/3a7de4a5-27c9-449f-a26e-0b4d9c7f871c"
    "https://image.lexica.art/md2_webp/3120bafc-df81-457b-9dd8-abd8aaf6a325"
    "https://image.lexica.art/md2_webp/31abf5bb-4271-44f6-85bb-82408f8b16f8"
    "https://image.lexica.art/md2_webp/32583094-4317-43d0-a7e0-fa7998e63eac"
    "https://image.lexica.art/md2_webp/08f05c29-7566-4d1b-a663-0bb20940f376"
    "https://image.lexica.art/md2_webp/0a6f030c-852d-4eb4-a65e-c162ad17bad1"
    "https://image.lexica.art/md2_webp/103321ee-a90a-4592-8606-4a15e5d63a44"
    "https://image.lexica.art/md2_webp/131049bf-f755-41b0-a453-78c38a25d259"
    "https://image.lexica.art/md2_webp/238f10c4-7d56-448d-b39e-8b05ad5e8f1e"
    "https://image.lexica.art/md2_webp/17a35ea5-1a02-483c-a30d-15e76b6dfe67"
)

# --- FOOD ---
FOOD_REAL_URLS=(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Good_Food_Display_-_NCI_Visuals_Online.jpg/640px-Good_Food_Display_-_NCI_Visuals_Online.jpg"
    "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/Biryani_Home_Cooked.jpg/640px-Biryani_Home_Cooked.jpg"
    "https://upload.wikimedia.org/wikipedia/commons/thumb/9/90/Hapus_Mango.jpg/640px-Hapus_Mango.jpg"
    "https://upload.wikimedia.org/wikipedia/commons/thumb/6/60/Standing_rib_roast.jpg/640px-Standing_rib_roast.jpg"
    "https://upload.wikimedia.org/wikipedia/commons/thumb/3/30/Chocolate_fudge_with_almonds.jpg/640px-Chocolate_fudge_with_almonds.jpg"
    "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a3/Eq_it-na_pizza-margherita_sep2005_sml.jpg/640px-Eq_it-na_pizza-margherita_sep2005_sml.jpg"
    "https://upload.wikimedia.org/wikipedia/commons/thumb/4/44/Cheeseburger.jpg/640px-Cheeseburger.jpg"
    "https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/Choco_milk.jpg/640px-Choco_milk.jpg"
    "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7d/Assorted_cheeses.jpg/640px-Assorted_cheeses.jpg"
    "https://upload.wikimedia.org/wikipedia/commons/thumb/3/37/Spaghetti_bolognese_(hozinja).jpg/640px-Spaghetti_bolognese_(hozinja).jpg"
    "https://img.youtube.com/vi/WKJF8sDf5yk/maxresdefault.jpg"
    "https://img.youtube.com/vi/k39hSwsAaFg/maxresdefault.jpg"
    "https://img.youtube.com/vi/oLpQ8MXWL4U/maxresdefault.jpg"
    "https://img.youtube.com/vi/wPr4Q0FTZQE/maxresdefault.jpg"
    "https://img.youtube.com/vi/7-YxJaJGaSM/maxresdefault.jpg"
)

FOOD_AI_URLS=(
    "https://image.lexica.art/md2_webp/1e209904-6a7f-4a62-bbaf-5ac96a286374"
    "https://image.lexica.art/md2_webp/251d827f-4eb2-48f6-baa3-4384fe796610"
    "https://image.lexica.art/md2_webp/261f44f2-cd78-4068-af99-584c6f6ac288"
    "https://image.lexica.art/md2_webp/26a9441c-8a7e-471f-a938-43cd89d3abed"
    "https://image.lexica.art/md2_webp/219a6f8f-c843-490b-b14b-e2bb9bb08137"
    "https://image.lexica.art/md2_webp/16978848-b4df-474a-870d-1590572472df"
    "https://image.lexica.art/md2_webp/1cc6088c-cdff-431d-9fcf-39b5aec3ed3b"
    "https://image.lexica.art/md2_webp/1a24f91d-68e8-40ff-877c-0b3c97fb748c"
    "https://image.lexica.art/md2_webp/10e57c91-0f6b-4c5b-aa4c-d0412205b998"
    "https://image.lexica.art/md2_webp/1576db8c-f71b-4f1b-90d5-ee17c194fd63"
    "https://image.lexica.art/md2_webp/15c00b13-c780-47b0-ae04-815cbac66fa5"
    "https://image.lexica.art/md2_webp/14ccaf08-bb66-4b73-a90b-71b37ddc873a"
    "https://image.lexica.art/md2_webp/0d87471a-e9c9-4e6e-8b88-0720a079c8c9"
    "https://image.lexica.art/md2_webp/0e709533-f201-4cd6-aecf-ee837d506a94"
    "https://image.lexica.art/md2_webp/10ad7b1f-3ff1-4049-8615-6e2b38f01c47"
    "https://image.lexica.art/md2_webp/03c4088e-5a54-4395-96e1-89ce7cb61c9a"
    "https://image.lexica.art/md2_webp/070aa2c1-84b6-453c-8982-8113286a81a9"
    "https://image.lexica.art/md2_webp/080f93e2-0a80-41f9-9add-13c673d52e67"
    "https://image.lexica.art/md2_webp/0d329378-4896-42c8-b685-1fbc13dc9d7a"
)

# --- LANDSCAPE ---
LANDSCAPE_REAL_URLS=(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/24701-nature-natural-beauty.jpg/640px-24701-nature-natural-beauty.jpg"
    "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Sunrise_over_the_sea.jpg/640px-Sunrise_over_the_sea.jpg"
    "https://upload.wikimedia.org/wikipedia/commons/thumb/9/97/The_Earth_seen_from_Apollo_17.jpg/640px-The_Earth_seen_from_Apollo_17.jpg"
    "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4f/Foggy_forest.jpg/640px-Foggy_forest.jpg"
    "https://upload.wikimedia.org/wikipedia/commons/thumb/1/10/Empire_State_Building_%28aerial_view%29.jpg/640px-Empire_State_Building_%28aerial_view%29.jpg"
    "https://upload.wikimedia.org/wikipedia/commons/thumb/1/13/Sahara_2006.jpg/640px-Sahara_2006.jpg"
    "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b1/VAN_CAT.jpg/640px-VAN_CAT.jpg"
    "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/Biryani_Home_Cooked.jpg/320px-Biryani_Home_Cooked.jpg"
    "https://img.youtube.com/vi/4HqzYnRVWi8/maxresdefault.jpg"
    "https://img.youtube.com/vi/ZZ5LpwO-An4/maxresdefault.jpg"
    "https://img.youtube.com/vi/wh0Pf3mXAHE/maxresdefault.jpg"
    "https://img.youtube.com/vi/e-ORhEE9VVg/maxresdefault.jpg"
    "https://img.youtube.com/vi/1ZYbU82GVz4/maxresdefault.jpg"
    "https://img.youtube.com/vi/OtH6MkT7v0o/maxresdefault.jpg"
    "https://img.youtube.com/vi/K0ibBPhiaG0/maxresdefault.jpg"
)

LANDSCAPE_AI_URLS=(
    "https://image.lexica.art/md2_webp/20c2353f-6332-418b-9a6b-ef1a71623bb2"
    "https://image.lexica.art/md2_webp/431ea5df-34b8-4837-8b2f-4083f72e3627"
    "https://image.lexica.art/md2_webp/43494151-8556-4e45-9495-3e328aaf44d6"
    "https://image.lexica.art/md2_webp/48775d36-c1f5-47a7-a26f-8ffc8e61bcfa"
    "https://image.lexica.art/md2_webp/488b425a-c5a3-43bf-ae9f-5ee1d32c26a3"
    "https://image.lexica.art/md2_webp/3ed14f41-7872-4dea-b7de-870f480877f4"
    "https://image.lexica.art/md2_webp/30672488-9133-4a31-a100-14099a8f6b80"
    "https://image.lexica.art/md2_webp/3b224c08-354c-4f2b-b87f-4be5a249f7a9"
    "https://image.lexica.art/md2_webp/2bedda0b-4937-4b31-aadb-1005c1df9f85"
    "https://image.lexica.art/md2_webp/2d1286e5-2bba-49f2-b950-ab12b2a1bc8b"
    "https://image.lexica.art/md2_webp/1c5cde63-92ef-4da7-b36b-f2acfce5f61f"
    "https://image.lexica.art/md2_webp/1d9cfefe-bd57-4f4f-a5f9-37f1c7653e5b"
    "https://image.lexica.art/md2_webp/1ea9e6f8-5757-4011-96d9-0069aa3d5812"
    "https://image.lexica.art/md2_webp/0b78aa2c-eb17-4773-bed2-7610c67173b0"
    "https://image.lexica.art/md2_webp/0f1e87be-2240-47ee-9dcc-dac159912c79"
    "https://image.lexica.art/md2_webp/14893f57-d93a-4803-8e37-12ed1c5c3f2c"
    "https://image.lexica.art/md2_webp/1717ca58-4c1c-4cf7-b115-9f92ac712562"
    "https://image.lexica.art/md2_webp/1982ffc8-13ea-4984-8984-4b6ac8808bfe"
    "https://image.lexica.art/md2_webp/0fc52700-df17-4e78-b40a-b2745fc6247f"
    "https://image.lexica.art/md2_webp/0fcdb628-0059-4e45-a9eb-47d6f19810e8"
)

# --- ART / ILLUSTRATION ---
ART_REAL_URLS=(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ec/Mona_Lisa%2C_by_Leonardo_da_Vinci%2C_from_C2RMF_retouched.jpg/480px-Mona_Lisa%2C_by_Leonardo_da_Vinci%2C_from_C2RMF_retouched.jpg"
    "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ea/Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg/640px-Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg"
    "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/The_Fighting_Temeraire%2C_JMW_Turner%2C_National_Gallery.jpg/640px-The_Fighting_Temeraire%2C_JMW_Turner%2C_National_Gallery.jpg"
    "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Tsunami_by_hokusai_19th_century.jpg/640px-Tsunami_by_hokusai_19th_century.jpg"
    "https://upload.wikimedia.org/wikipedia/commons/thumb/d/da/The_Hay_Wain%2C_Constable%2C_1821.jpg/640px-The_Hay_Wain%2C_Constable%2C_1821.jpg"
    "https://upload.wikimedia.org/wikipedia/commons/thumb/3/30/Michelangelo_-_Creation_of_Adam_(cropped).jpg/640px-Michelangelo_-_Creation_of_Adam_(cropped).jpg"
    "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/280px-PNG_transparency_demonstration_1.png"
    "https://img.youtube.com/vi/IUN664s7N-c/maxresdefault.jpg"
    "https://img.youtube.com/vi/B0hzDHbhRzY/maxresdefault.jpg"
    "https://img.youtube.com/vi/CevxZvSJLk8/hqdefault.jpg"
    "https://img.youtube.com/vi/GJLlxj_dtq8/maxresdefault.jpg"
    "https://img.youtube.com/vi/Cxog8fMCkGA/maxresdefault.jpg"
    "https://img.youtube.com/vi/jXDbjMCP1z4/maxresdefault.jpg"
    "https://img.youtube.com/vi/JHa2O7Ek-8Y/maxresdefault.jpg"
    "https://img.youtube.com/vi/9MHlT4YURJI/maxresdefault.jpg"
)

ART_AI_URLS=(
    "https://image.lexica.art/md2_webp/28a3a9e4-37ec-4f47-9d34-ea19d2ba7d40"
    "https://image.lexica.art/md2_webp/2ce597cb-6809-4e27-92c3-078b62c714a3"
    "https://image.lexica.art/md2_webp/2d69e174-ba4b-47f3-9c75-139f2259a783"
    "https://image.lexica.art/md2_webp/2d08923c-5aa9-4f31-950d-9612302a1251"
    "https://image.lexica.art/md2_webp/2ad786bb-563f-4653-9abe-ee2c34849748"
    "https://image.lexica.art/md2_webp/1d9f20fb-2141-45bd-9d9e-68b3e17fc178"
    "https://image.lexica.art/md2_webp/1f52de9a-3ce7-4706-a499-bd11115b140c"
    "https://image.lexica.art/md2_webp/22397953-32ff-4e5c-9872-e2947264d86a"
    "https://image.lexica.art/md2_webp/274b7b1d-c0aa-4b8b-ba40-51e84dbfa0d4"
    "https://image.lexica.art/md2_webp/283e96b3-44bd-4bca-88b7-a6352e4e1f7c"
    "https://image.lexica.art/md2_webp/1fa6de15-beee-4c2d-92e3-d0319387f1a4"
    "https://image.lexica.art/md2_webp/17dbf596-826f-4257-8bac-3f20acfb8832"
    "https://image.lexica.art/md2_webp/1d91b369-0043-4269-8fb6-46662a910f00"
    "https://image.lexica.art/md2_webp/1d21758c-2236-4dc3-b55d-25de6d6844d1"
    "https://image.lexica.art/md2_webp/085a5e38-d807-40c9-bb9e-e032a4b4af02"
    "https://image.lexica.art/md2_webp/0c15af6f-52ae-487f-a11b-868c54f8c8a9"
    "https://image.lexica.art/md2_webp/11a13f0a-248d-4c1a-99ab-5dfde2662e69"
    "https://image.lexica.art/md2_webp/170477cb-c1a6-4519-b495-7113f0aadbb5"
    "https://image.lexica.art/md2_webp/173f604e-4ffc-434c-95df-d7af0994d245"
    "https://image.lexica.art/md2_webp/15cb9948-8137-4d86-a3b6-cbb92747702b"
)

# --- FITNESS ---
FITNESS_REAL_URLS=(
    "https://img.youtube.com/vi/HKJR64VrxRQ/maxresdefault.jpg"
    "https://img.youtube.com/vi/vc1E5CfRfos/maxresdefault.jpg"
    "https://img.youtube.com/vi/cbKkB3POqaY/maxresdefault.jpg"
    "https://img.youtube.com/vi/IgRpMoJSS4g/maxresdefault.jpg"
    "https://img.youtube.com/vi/BH0xHcZhO90/maxresdefault.jpg"
    "https://img.youtube.com/vi/Y1EH5S7BKIQ/maxresdefault.jpg"
    "https://img.youtube.com/vi/4Bo2Mgs9VJQ/maxresdefault.jpg"
    "https://img.youtube.com/vi/g_tea8ZNk5A/maxresdefault.jpg"
    "https://img.youtube.com/vi/J0YMkFbm3M4/maxresdefault.jpg"
    "https://img.youtube.com/vi/oBu-pQG6sTY/maxresdefault.jpg"
    "https://img.youtube.com/vi/GH0ePzBZhSs/maxresdefault.jpg"
    "https://img.youtube.com/vi/IqiTJK_uzuc/maxresdefault.jpg"
    "https://img.youtube.com/vi/r4MezPEPGKo/maxresdefault.jpg"
    "https://img.youtube.com/vi/VKJH7Bn3WYE/maxresdefault.jpg"
    "https://img.youtube.com/vi/Mez0dP-GelU/maxresdefault.jpg"
)

FITNESS_AI_URLS=(
    "https://image.lexica.art/md2_webp/34ba000f-b770-4bcd-9055-6fc8560decda"
    "https://image.lexica.art/md2_webp/36529cbf-c453-41bd-98ce-6e75ccee640b"
    "https://image.lexica.art/md2_webp/3c1dd298-56ea-4acc-9255-21deaed12634"
    "https://image.lexica.art/md2_webp/38951d7f-431d-430c-a193-15c460f2daab"
    "https://image.lexica.art/md2_webp/34c4b9c3-3b1f-4d49-b0d0-b36d94d7975b"
    "https://image.lexica.art/md2_webp/3512072e-8fa5-479a-8b62-59ed2cfdd7a5"
    "https://image.lexica.art/md2_webp/2d9555b8-c9f7-4953-b5bb-78041d733fb3"
    "https://image.lexica.art/md2_webp/2ea94e52-18a5-4077-aa69-801cf9891042"
    "https://image.lexica.art/md2_webp/33be04b3-de71-4df0-bd79-72da05113ae9"
    "https://image.lexica.art/md2_webp/1d62ff6d-b7bc-4aa2-82d0-2bbdf77367a7"
    "https://image.lexica.art/md2_webp/244318d2-154c-4158-8ef1-48f37f52e9b7"
    "https://image.lexica.art/md2_webp/25cb4ee6-603e-435f-be63-ba321560a6c2"
    "https://image.lexica.art/md2_webp/204f3025-2a46-4964-a2cd-ffb3fc2a6d3c"
    "https://image.lexica.art/md2_webp/1d0e1e49-7609-4ee0-bdc5-f05fac1549f9"
    "https://image.lexica.art/md2_webp/0bbf7d3a-557e-4bf7-8c5f-36e2156053d9"
    "https://image.lexica.art/md2_webp/0eb9e03c-9f46-45d6-84e5-6306f53ec514"
    "https://image.lexica.art/md2_webp/19fbe431-dacc-4a66-8810-0793a5f59cb8"
    "https://image.lexica.art/md2_webp/1b0f9533-cb1a-400b-8489-2790ce3cfeb9"
)

# --- PETS / ANIMALS ---
PETS_REAL_URLS=(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/1/18/Dog_Breeds.jpg/640px-Dog_Breeds.jpg"
    "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bb/Kittyply_edit1.jpg/640px-Kittyply_edit1.jpg"
    "https://upload.wikimedia.org/wikipedia/commons/thumb/4/43/Cute_dog.jpg/640px-Cute_dog.jpg"
    "https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/YellowLabradorLooking_new.jpg/640px-YellowLabradorLooking_new.jpg"
    "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0b/Cat_poster_1.jpg/640px-Cat_poster_1.jpg"
    "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Jackrabbit.jpg/640px-Jackrabbit.jpg"
    "https://upload.wikimedia.org/wikipedia/commons/thumb/1/14/Gatto_europeo4.jpg/640px-Gatto_europeo4.jpg"
    "https://img.youtube.com/vi/5dsGWM5XGdg/maxresdefault.jpg"
    "https://img.youtube.com/vi/lDK9QqIzhwk/maxresdefault.jpg"
    "https://img.youtube.com/vi/GH0ePzBZhSs/hqdefault.jpg"
    "https://img.youtube.com/vi/p2h1m7IQFPA/maxresdefault.jpg"
    "https://img.youtube.com/vi/PKffm2uI4dk/maxresdefault.jpg"
    "https://img.youtube.com/vi/OtH6MkT7v0o/hqdefault.jpg"
    "https://img.youtube.com/vi/NHozFX_ks-s/maxresdefault.jpg"
    "https://img.youtube.com/vi/tntOCGkgt98/maxresdefault.jpg"
)

PETS_AI_URLS=(
    "https://image.lexica.art/md2_webp/1eea74a3-ff0b-4959-bb1f-c5c2a1c48f3d"
    "https://image.lexica.art/md2_webp/30552140-193e-43ec-b188-55a78fb3bf52"
    "https://image.lexica.art/md2_webp/3437f669-a6d4-4f62-b2e1-8502de34bd0d"
    "https://image.lexica.art/md2_webp/355ad1db-f608-46f1-a90c-29ad75f6b6a6"
    "https://image.lexica.art/md2_webp/2ee495a5-d16b-4746-bc49-f9e5529526b1"
    "https://image.lexica.art/md2_webp/296b99ca-c140-45b3-8f8c-2b0056734ca1"
    "https://image.lexica.art/md2_webp/2c60f12a-d471-4d04-82f6-a6ed0455f839"
    "https://image.lexica.art/md2_webp/2ec53f09-af62-4ff5-b31f-550fc90518ea"
    "https://image.lexica.art/md2_webp/27c2b6af-31dc-4def-acb0-e274d3a5ccd7"
    "https://image.lexica.art/md2_webp/20d374aa-ae2b-4116-8c60-9349d7b40567"
    "https://image.lexica.art/md2_webp/149211e2-c960-44e3-955c-2778d12de914"
    "https://image.lexica.art/md2_webp/1b503ae9-5723-4d3c-842b-f99844343859"
    "https://image.lexica.art/md2_webp/1de316fd-597b-42d4-8183-767e50778164"
    "https://image.lexica.art/md2_webp/0cf36fd1-f693-4cc2-aeab-70ce9dbc1289"
    "https://image.lexica.art/md2_webp/10d66aa4-ba6c-47e1-baaf-8c2920faa67f"
    "https://image.lexica.art/md2_webp/12e82980-3352-4962-bcaa-f9ae6e091898"
    "https://image.lexica.art/md2_webp/02c0cbdf-6f55-404f-a2aa-dc560a5c2e9a"
    "https://image.lexica.art/md2_webp/0570d4b7-e6af-43ef-9ebe-dee427441410"
    "https://image.lexica.art/md2_webp/00fa2342-a5bd-4a94-b0ab-4c2c59d5e9ba"
)

# --- FASHION ---
FASHION_REAL_URLS=(
    "https://img.youtube.com/vi/whW4cqTHdWM/maxresdefault.jpg"
    "https://img.youtube.com/vi/B_0aQ-CDQ3w/maxresdefault.jpg"
    "https://img.youtube.com/vi/gJBGAaQA-Yg/maxresdefault.jpg"
    "https://img.youtube.com/vi/ykW9yjJlrC8/maxresdefault.jpg"
    "https://img.youtube.com/vi/gJBGAaQA-Yg/hqdefault.jpg"
    "https://img.youtube.com/vi/XqZsoesa55w/maxresdefault.jpg"
    "https://img.youtube.com/vi/A_hvY3xA2sI/maxresdefault.jpg"
    "https://img.youtube.com/vi/B_0aQ-CDQ3w/hqdefault.jpg"
    "https://img.youtube.com/vi/YwUFaKi85oM/maxresdefault.jpg"
    "https://img.youtube.com/vi/fJ9rUzIMcZQ/maxresdefault.jpg"
    "https://img.youtube.com/vi/w4tPpFKF70w/maxresdefault.jpg"
    "https://img.youtube.com/vi/uO5_W1Yszdk/maxresdefault.jpg"
    "https://img.youtube.com/vi/P_-FBukNEZE/maxresdefault.jpg"
    "https://img.youtube.com/vi/DEyXaX2-lKw/maxresdefault.jpg"
    "https://img.youtube.com/vi/d1HCvW-cz0I/maxresdefault.jpg"
)

FASHION_AI_URLS=(
    "https://image.lexica.art/md2_webp/315327a2-8820-4d02-8b16-4faccd8bd326"
    "https://image.lexica.art/md2_webp/297f2352-3dc4-405f-b308-6683f87c5045"
    "https://image.lexica.art/md2_webp/301e7585-d5f5-4afe-9374-59beb9de96d0"
    "https://image.lexica.art/md2_webp/3057c641-9c4c-41a3-9e4a-f2d6fc9c80a6"
    "https://image.lexica.art/md2_webp/1787da4b-e4bd-408d-b601-b09836e02add"
    "https://image.lexica.art/md2_webp/22637b8e-2490-4e19-97c0-2ae4cc3a0323"
    "https://image.lexica.art/md2_webp/26d1cbc8-edeb-4214-81cc-ac8455dff8b7"
    "https://image.lexica.art/md2_webp/1dc13954-0d71-4c6b-b20b-57d6ac92931c"
    "https://image.lexica.art/md2_webp/0afc68c2-b9e3-4864-ae8b-e3c6f42aefc0"
    "https://image.lexica.art/md2_webp/0b0792e6-9bd5-425b-af97-1a00001d0a55"
    "https://image.lexica.art/md2_webp/10e93c92-c15c-4473-a702-2d9a48c45840"
    "https://image.lexica.art/md2_webp/1457be48-a127-473a-affa-abb4a4446d1b"
    "https://image.lexica.art/md2_webp/115233e2-9fd2-4a9a-9b57-04258b66a9d6"
    "https://image.lexica.art/md2_webp/142a759e-cfbc-42d6-a6d5-603c6956d726"
)

# --- VIDEO THUMBNAILS (real YouTube vs AI-generated thumbnail style) ---
VIDEO_THUMB_REAL_URLS=(
    "https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg"
    "https://img.youtube.com/vi/9bZkp7q19f0/hqdefault.jpg"
    "https://img.youtube.com/vi/kJQP7kiw5Fk/hqdefault.jpg"
    "https://img.youtube.com/vi/JGwWNGJdvx8/hqdefault.jpg"
    "https://img.youtube.com/vi/OPf0YbXqDm0/hqdefault.jpg"
    "https://img.youtube.com/vi/60ItHLz5WEA/hqdefault.jpg"
    "https://img.youtube.com/vi/2Vv-BfVoq4g/hqdefault.jpg"
    "https://img.youtube.com/vi/YqeW9_5kURI/hqdefault.jpg"
    "https://img.youtube.com/vi/IUN664s7N-c/hqdefault.jpg"
    "https://img.youtube.com/vi/B0hzDHbhRzY/hqdefault.jpg"
    "https://img.youtube.com/vi/GJLlxj_dtq8/hqdefault.jpg"
    "https://img.youtube.com/vi/Cxog8fMCkGA/hqdefault.jpg"
    "https://img.youtube.com/vi/4HqzYnRVWi8/hqdefault.jpg"
    "https://img.youtube.com/vi/ZZ5LpwO-An4/hqdefault.jpg"
    "https://img.youtube.com/vi/HKJR64VrxRQ/hqdefault.jpg"
)

VIDEO_THUMB_AI_URLS=(
    "https://image.lexica.art/md2_webp/4c5f6e65-c8b7-4c07-9c1e-3f7b67b48320"
    "https://image.lexica.art/md2_webp/545f701d-3c77-4193-b8ce-e9170f47177b"
    "https://image.lexica.art/md2_webp/54a83724-0454-4a92-a884-ce4c800ac043"
    "https://image.lexica.art/md2_webp/5128e577-3ff4-44af-aecc-d2a68c467d83"
    "https://image.lexica.art/md2_webp/3ded5227-e483-476d-a31b-f40893297915"
    "https://image.lexica.art/md2_webp/41206351-1bf0-47e6-a461-880c5fc18cd2"
    "https://image.lexica.art/md2_webp/1b503ae9-5723-4d3c-842b-f99844343859"
    "https://image.lexica.art/md2_webp/0fcdb628-0059-4e45-a9eb-47d6f19810e8"
    "https://image.lexica.art/md2_webp/00de1b0f-5c67-4f18-b958-790d95642776"
    "https://image.lexica.art/md2_webp/054b7bd2-4c9f-43d4-ab05-7e1c2a2cdded"
    "https://image.lexica.art/md2_webp/06ba916e-1fd3-4326-8c20-2d3964358c3c"
    "https://image.lexica.art/md2_webp/0aa8ecd9-561e-41b3-8600-b09b32fd1b59"
    "https://image.lexica.art/md2_webp/079ec4d7-e93a-420f-b942-7fa0ea09e8e9"
    "https://image.lexica.art/md2_webp/07367a21-4d22-43d3-a320-2da8b6853f3b"
    "https://image.lexica.art/md2_webp/1982ffc8-13ea-4984-8984-4b6ac8808bfe"
)

# ========================
# MAIN TEST LOOP
# ========================

ID=0

run_category() {
    local category=$1
    local ground_truth=$2
    shift 2
    local urls=("$@")

    for url in "${urls[@]}"; do
        if [ $QUOTA_ERROR -ne 0 ]; then
            echo "QUOTA ERROR - aborting"
            return 1
        fi
        ID=$((ID + 1))
        scan_image $ID "$category" "$ground_truth" "$url"

        # Write file every 10 results
        if [ $((TOTAL % 10)) -eq 0 ] && [ $TOTAL -gt 0 ]; then
            update_file
        fi

        if [ $ID -lt $TOTAL_TARGET ]; then
            sleep 10
        fi
    done
}

echo "Starting calibration test..."
echo "Output: $OUTPUT"
update_file

# Run all categories (real then AI interleaved by category)
run_category "portrait" "real" "${PORTRAIT_REAL_URLS[@]}" || exit 1
run_category "portrait" "ai_generated" "${PORTRAIT_AI_URLS[@]}" || exit 1
run_category "food" "real" "${FOOD_REAL_URLS[@]}" || exit 1
run_category "food" "ai_generated" "${FOOD_AI_URLS[@]}" || exit 1
run_category "landscape" "real" "${LANDSCAPE_REAL_URLS[@]}" || exit 1
run_category "landscape" "ai_generated" "${LANDSCAPE_AI_URLS[@]}" || exit 1
run_category "art" "real" "${ART_REAL_URLS[@]}" || exit 1
run_category "art" "ai_generated" "${ART_AI_URLS[@]}" || exit 1
run_category "fitness" "real" "${FITNESS_REAL_URLS[@]}" || exit 1
run_category "fitness" "ai_generated" "${FITNESS_AI_URLS[@]}" || exit 1
run_category "pets" "real" "${PETS_REAL_URLS[@]}" || exit 1
run_category "pets" "ai_generated" "${PETS_AI_URLS[@]}" || exit 1
run_category "fashion" "real" "${FASHION_REAL_URLS[@]}" || exit 1
run_category "fashion" "ai_generated" "${FASHION_AI_URLS[@]}" || exit 1
run_category "video_thumbnail" "real" "${VIDEO_THUMB_REAL_URLS[@]}" || exit 1
run_category "video_thumbnail" "ai_generated" "${VIDEO_THUMB_AI_URLS[@]}" || exit 1

# Final update with summary
update_file

# Write summary
OVERALL_ACCURACY=0
FP_RATE=0
FN_RATE=0
if [ $TOTAL -gt 0 ]; then
    OVERALL_ACCURACY=$(echo "scale=4; $CORRECT / $TOTAL" | bc)
fi
REAL_TOTAL=$(($(for cat in portrait food landscape art fitness pets fashion video_thumbnail; do echo ${CAT_COUNT_REAL[$cat]}; done | paste -sd+ | bc)))
AI_TOTAL=$(($(for cat in portrait food landscape art fitness pets fashion video_thumbnail; do echo ${CAT_COUNT_AI[$cat]}; done | paste -sd+ | bc)))
if [ $REAL_TOTAL -gt 0 ]; then
    FP_RATE=$(echo "scale=4; $FALSE_POS / $REAL_TOTAL" | bc)
fi
if [ $AI_TOTAL -gt 0 ]; then
    FN_RATE=$(echo "scale=4; $FALSE_NEG / $AI_TOTAL" | bc)
fi

python3 - << PYEOF
import json, sys

with open('$OUTPUT') as f:
    data = json.load(f)

by_cat = data['by_category']

# Find best and worst category
best_cat = max(by_cat.items(), key=lambda x: x[1]['accuracy'] if x[1]['total'] > 0 else 0)
worst_cat = min(by_cat.items(), key=lambda x: x[1]['accuracy'] if x[1]['total'] > 0 else 1)

overall = $OVERALL_ACCURACY
fp_rate = $FP_RATE
fn_rate = $FN_RATE

# Threshold recommendation
if fp_rate > 0.15:
    threshold_rec = "raise to 0.70 - too many false positives on real images"
elif fn_rate > 0.20:
    threshold_rec = "lower to 0.55 - too many false negatives on AI images"
else:
    threshold_rec = "keep 0.65 - current threshold performing well"

data['summary'] = {
    'total_tested': $TOTAL,
    'overall_accuracy': overall,
    'false_positive_rate': fp_rate,
    'false_negative_rate': fn_rate,
    'best_category': best_cat[0],
    'worst_category': worst_cat[0],
    'threshold_recommendation': threshold_rec,
    'notes': f"Tested {$TOTAL} images across 8 categories. {$CORRECT} correct. FP={$FALSE_POS} FN={$FALSE_NEG}. Real sources: YouTube thumbnails + Wikimedia Commons. AI sources: Lexica.art generated images."
}

with open('$OUTPUT', 'w') as f:
    json.dump(data, f, indent=2)

print(f"FINAL: total={$TOTAL} accuracy={overall:.3f} FP_rate={fp_rate:.3f} FN_rate={fn_rate:.3f}")
print(f"Best: {best_cat[0]} ({best_cat[1]['accuracy']:.3f})")
print(f"Worst: {worst_cat[0]} ({worst_cat[1]['accuracy']:.3f})")
print(f"Threshold recommendation: {threshold_rec}")
PYEOF

echo "Calibration complete!"
