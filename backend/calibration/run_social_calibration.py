#!/usr/bin/env python3
"""
Social media calibration test - 300 images across 8 categories
Runs curl for each image, sleeps 10s between requests,
writes results to social_media_results.json after every 10 tests.
"""

import json
import subprocess
import time
import sys
from datetime import datetime, timezone

OUTPUT = "C:/Users/ckbaw/Desktop/Thornveil_LLC/ai-detector/backend/calibration/social_media_results.json"
BACKEND = "http://localhost:8001/api/scan"

STARTED_AT = datetime.now(timezone.utc).isoformat()

# ========================
# URL LISTS
# ========================

PORTRAIT_REAL = [
    ("https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg", "portrait", "real"),
    ("https://img.youtube.com/vi/9bZkp7q19f0/maxresdefault.jpg", "portrait", "real"),
    ("https://img.youtube.com/vi/kJQP7kiw5Fk/maxresdefault.jpg", "portrait", "real"),
    ("https://img.youtube.com/vi/JGwWNGJdvx8/maxresdefault.jpg", "portrait", "real"),
    ("https://img.youtube.com/vi/OPf0YbXqDm0/maxresdefault.jpg", "portrait", "real"),
    ("https://img.youtube.com/vi/60ItHLz5WEA/maxresdefault.jpg", "portrait", "real"),
    ("https://img.youtube.com/vi/2Vv-BfVoq4g/maxresdefault.jpg", "portrait", "real"),
    ("https://img.youtube.com/vi/YqeW9_5kURI/maxresdefault.jpg", "portrait", "real"),
    ("https://img.youtube.com/vi/CevxZvSJLk8/maxresdefault.jpg", "portrait", "real"),
    ("https://img.youtube.com/vi/09R8_2nJtjg/maxresdefault.jpg", "portrait", "real"),
    ("https://img.youtube.com/vi/fJ9rUzIMcZQ/maxresdefault.jpg", "portrait", "real"),
    ("https://img.youtube.com/vi/uO5_W1Yszdk/maxresdefault.jpg", "portrait", "real"),
    ("https://img.youtube.com/vi/P_-FBukNEZE/maxresdefault.jpg", "portrait", "real"),
    ("https://img.youtube.com/vi/DEyXaX2-lKw/maxresdefault.jpg", "portrait", "real"),
    ("https://img.youtube.com/vi/d1HCvW-cz0I/maxresdefault.jpg", "portrait", "real"),
]

PORTRAIT_AI = [
    ("https://image.lexica.art/md2_webp/448a754f-016b-4910-b0d5-65d681a1b816", "portrait", "ai_generated"),
    ("https://image.lexica.art/md2_webp/3b1be28c-ad04-49b4-8a25-6c3194bdf455", "portrait", "ai_generated"),
    ("https://image.lexica.art/md2_webp/48ed2c5f-f019-4c92-b21a-a3c1521cf0b3", "portrait", "ai_generated"),
    ("https://image.lexica.art/md2_webp/5c5570d9-1944-4135-8c2d-0e04c5b64884", "portrait", "ai_generated"),
    ("https://image.lexica.art/md2_webp/71800f72-17c7-46d8-aa67-329aab827874", "portrait", "ai_generated"),
    ("https://image.lexica.art/md2_webp/5302ac8c-1edf-47de-9bde-5a5d44ec15d9", "portrait", "ai_generated"),
    ("https://image.lexica.art/md2_webp/45e1f94f-492f-4022-a627-606e05c330ac", "portrait", "ai_generated"),
    ("https://image.lexica.art/md2_webp/353e94ce-af10-489c-8f16-ba936005e677", "portrait", "ai_generated"),
    ("https://image.lexica.art/md2_webp/39c94612-c1b9-4da3-8bdf-1edc7fd9bebf", "portrait", "ai_generated"),
    ("https://image.lexica.art/md2_webp/3a7de4a5-27c9-449f-a26e-0b4d9c7f871c", "portrait", "ai_generated"),
    ("https://image.lexica.art/md2_webp/3120bafc-df81-457b-9dd8-abd8aaf6a325", "portrait", "ai_generated"),
    ("https://image.lexica.art/md2_webp/31abf5bb-4271-44f6-85bb-82408f8b16f8", "portrait", "ai_generated"),
    ("https://image.lexica.art/md2_webp/32583094-4317-43d0-a7e0-fa7998e63eac", "portrait", "ai_generated"),
    ("https://image.lexica.art/md2_webp/08f05c29-7566-4d1b-a663-0bb20940f376", "portrait", "ai_generated"),
    ("https://image.lexica.art/md2_webp/0a6f030c-852d-4eb4-a65e-c162ad17bad1", "portrait", "ai_generated"),
    ("https://image.lexica.art/md2_webp/103321ee-a90a-4592-8606-4a15e5d63a44", "portrait", "ai_generated"),
    ("https://image.lexica.art/md2_webp/131049bf-f755-41b0-a453-78c38a25d259", "portrait", "ai_generated"),
    ("https://image.lexica.art/md2_webp/238f10c4-7d56-448d-b39e-8b05ad5e8f1e", "portrait", "ai_generated"),
    ("https://image.lexica.art/md2_webp/17a35ea5-1a02-483c-a30d-15e76b6dfe67", "portrait", "ai_generated"),
]

FOOD_REAL = [
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Good_Food_Display_-_NCI_Visuals_Online.jpg/640px-Good_Food_Display_-_NCI_Visuals_Online.jpg", "food", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/Biryani_Home_Cooked.jpg/640px-Biryani_Home_Cooked.jpg", "food", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/9/90/Hapus_Mango.jpg/640px-Hapus_Mango.jpg", "food", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/6/60/Standing_rib_roast.jpg/640px-Standing_rib_roast.jpg", "food", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a3/Eq_it-na_pizza-margherita_sep2005_sml.jpg/640px-Eq_it-na_pizza-margherita_sep2005_sml.jpg", "food", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/4/44/Cheeseburger.jpg/640px-Cheeseburger.jpg", "food", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/7/7d/Assorted_cheeses.jpg/640px-Assorted_cheeses.jpg", "food", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/3/37/Spaghetti_bolognese_%28hozinja%29.jpg/640px-Spaghetti_bolognese_%28hozinja%29.jpg", "food", "real"),
    ("https://img.youtube.com/vi/WKJF8sDf5yk/maxresdefault.jpg", "food", "real"),
    ("https://img.youtube.com/vi/k39hSwsAaFg/maxresdefault.jpg", "food", "real"),
    ("https://img.youtube.com/vi/oLpQ8MXWL4U/maxresdefault.jpg", "food", "real"),
    ("https://img.youtube.com/vi/wPr4Q0FTZQE/maxresdefault.jpg", "food", "real"),
    ("https://img.youtube.com/vi/7-YxJaJGaSM/maxresdefault.jpg", "food", "real"),
    ("https://img.youtube.com/vi/VVT3x5mT6pM/maxresdefault.jpg", "food", "real"),
    ("https://img.youtube.com/vi/bqXFUxJEVCg/maxresdefault.jpg", "food", "real"),
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
    ("https://image.lexica.art/md2_webp/15c00b13-c780-47b0-ae04-815cbac66fa5", "food", "ai_generated"),
    ("https://image.lexica.art/md2_webp/14ccaf08-bb66-4b73-a90b-71b37ddc873a", "food", "ai_generated"),
    ("https://image.lexica.art/md2_webp/0d87471a-e9c9-4e6e-8b88-0720a079c8c9", "food", "ai_generated"),
    ("https://image.lexica.art/md2_webp/0e709533-f201-4cd6-aecf-ee837d506a94", "food", "ai_generated"),
    ("https://image.lexica.art/md2_webp/10ad7b1f-3ff1-4049-8615-6e2b38f01c47", "food", "ai_generated"),
    ("https://image.lexica.art/md2_webp/03c4088e-5a54-4395-96e1-89ce7cb61c9a", "food", "ai_generated"),
    ("https://image.lexica.art/md2_webp/070aa2c1-84b6-453c-8982-8113286a81a9", "food", "ai_generated"),
    ("https://image.lexica.art/md2_webp/080f93e2-0a80-41f9-9add-13c673d52e67", "food", "ai_generated"),
    ("https://image.lexica.art/md2_webp/0d329378-4896-42c8-b685-1fbc13dc9d7a", "food", "ai_generated"),
]

LANDSCAPE_REAL = [
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/9/97/The_Earth_seen_from_Apollo_17.jpg/640px-The_Earth_seen_from_Apollo_17.jpg", "landscape", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/1/13/Sahara_2006.jpg/640px-Sahara_2006.jpg", "landscape", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Camponotus_flavomarginatus_ant.jpg/640px-Camponotus_flavomarginatus_ant.jpg", "landscape", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Jackrabbit.jpg/640px-Jackrabbit.jpg", "landscape", "real"),
    ("https://img.youtube.com/vi/4HqzYnRVWi8/maxresdefault.jpg", "landscape", "real"),
    ("https://img.youtube.com/vi/ZZ5LpwO-An4/maxresdefault.jpg", "landscape", "real"),
    ("https://img.youtube.com/vi/wh0Pf3mXAHE/maxresdefault.jpg", "landscape", "real"),
    ("https://img.youtube.com/vi/e-ORhEE9VVg/maxresdefault.jpg", "landscape", "real"),
    ("https://img.youtube.com/vi/1ZYbU82GVz4/maxresdefault.jpg", "landscape", "real"),
    ("https://img.youtube.com/vi/OtH6MkT7v0o/maxresdefault.jpg", "landscape", "real"),
    ("https://img.youtube.com/vi/K0ibBPhiaG0/maxresdefault.jpg", "landscape", "real"),
    ("https://img.youtube.com/vi/GH0ePzBZhSs/maxresdefault.jpg", "landscape", "real"),
    ("https://img.youtube.com/vi/NHozFX_ks-s/maxresdefault.jpg", "landscape", "real"),
    ("https://img.youtube.com/vi/tntOCGkgt98/maxresdefault.jpg", "landscape", "real"),
    ("https://img.youtube.com/vi/IqiTJK_uzuc/maxresdefault.jpg", "landscape", "real"),
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
    ("https://image.lexica.art/md2_webp/1c5cde63-92ef-4da7-b36b-f2acfce5f61f", "landscape", "ai_generated"),
    ("https://image.lexica.art/md2_webp/1d9cfefe-bd57-4f4f-a5f9-37f1c7653e5b", "landscape", "ai_generated"),
    ("https://image.lexica.art/md2_webp/1ea9e6f8-5757-4011-96d9-0069aa3d5812", "landscape", "ai_generated"),
    ("https://image.lexica.art/md2_webp/0b78aa2c-eb17-4773-bed2-7610c67173b0", "landscape", "ai_generated"),
    ("https://image.lexica.art/md2_webp/0f1e87be-2240-47ee-9dcc-dac159912c79", "landscape", "ai_generated"),
    ("https://image.lexica.art/md2_webp/14893f57-d93a-4803-8e37-12ed1c5c3f2c", "landscape", "ai_generated"),
    ("https://image.lexica.art/md2_webp/1717ca58-4c1c-4cf7-b115-9f92ac712562", "landscape", "ai_generated"),
    ("https://image.lexica.art/md2_webp/1982ffc8-13ea-4984-8984-4b6ac8808bfe", "landscape", "ai_generated"),
    ("https://image.lexica.art/md2_webp/0fc52700-df17-4e78-b40a-b2745fc6247f", "landscape", "ai_generated"),
    ("https://image.lexica.art/md2_webp/0fcdb628-0059-4e45-a9eb-47d6f19810e8", "landscape", "ai_generated"),
]

ART_REAL = [
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/e/ec/Mona_Lisa%2C_by_Leonardo_da_Vinci%2C_from_C2RMF_retouched.jpg/480px-Mona_Lisa%2C_by_Leonardo_da_Vinci%2C_from_C2RMF_retouched.jpg", "art", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/e/ea/Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg/640px-Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg", "art", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/The_Fighting_Temeraire%2C_JMW_Turner%2C_National_Gallery.jpg/640px-The_Fighting_Temeraire%2C_JMW_Turner%2C_National_Gallery.jpg", "art", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Tsunami_by_hokusai_19th_century.jpg/640px-Tsunami_by_hokusai_19th_century.jpg", "art", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/d/da/The_Hay_Wain%2C_Constable%2C_1821.jpg/640px-The_Hay_Wain%2C_Constable%2C_1821.jpg", "art", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/3/30/Michelangelo_-_Creation_of_Adam_%28cropped%29.jpg/640px-Michelangelo_-_Creation_of_Adam_%28cropped%29.jpg", "art", "real"),
    ("https://img.youtube.com/vi/IUN664s7N-c/maxresdefault.jpg", "art", "real"),
    ("https://img.youtube.com/vi/B0hzDHbhRzY/maxresdefault.jpg", "art", "real"),
    ("https://img.youtube.com/vi/GJLlxj_dtq8/maxresdefault.jpg", "art", "real"),
    ("https://img.youtube.com/vi/Cxog8fMCkGA/maxresdefault.jpg", "art", "real"),
    ("https://img.youtube.com/vi/jXDbjMCP1z4/maxresdefault.jpg", "art", "real"),
    ("https://img.youtube.com/vi/JHa2O7Ek-8Y/maxresdefault.jpg", "art", "real"),
    ("https://img.youtube.com/vi/9MHlT4YURJI/maxresdefault.jpg", "art", "real"),
    ("https://img.youtube.com/vi/IgRpMoJSS4g/maxresdefault.jpg", "art", "real"),
    ("https://img.youtube.com/vi/BH0xHcZhO90/maxresdefault.jpg", "art", "real"),
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
    ("https://image.lexica.art/md2_webp/1fa6de15-beee-4c2d-92e3-d0319387f1a4", "art", "ai_generated"),
    ("https://image.lexica.art/md2_webp/17dbf596-826f-4257-8bac-3f20acfb8832", "art", "ai_generated"),
    ("https://image.lexica.art/md2_webp/1d91b369-0043-4269-8fb6-46662a910f00", "art", "ai_generated"),
    ("https://image.lexica.art/md2_webp/1d21758c-2236-4dc3-b55d-25de6d6844d1", "art", "ai_generated"),
    ("https://image.lexica.art/md2_webp/085a5e38-d807-40c9-bb9e-e032a4b4af02", "art", "ai_generated"),
    ("https://image.lexica.art/md2_webp/0c15af6f-52ae-487f-a11b-868c54f8c8a9", "art", "ai_generated"),
    ("https://image.lexica.art/md2_webp/11a13f0a-248d-4c1a-99ab-5dfde2662e69", "art", "ai_generated"),
    ("https://image.lexica.art/md2_webp/170477cb-c1a6-4519-b495-7113f0aadbb5", "art", "ai_generated"),
    ("https://image.lexica.art/md2_webp/173f604e-4ffc-434c-95df-d7af0994d245", "art", "ai_generated"),
    ("https://image.lexica.art/md2_webp/15cb9948-8137-4d86-a3b6-cbb92747702b", "art", "ai_generated"),
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
    ("https://img.youtube.com/vi/r4MezPEPGKo/maxresdefault.jpg", "fitness", "real"),
    ("https://img.youtube.com/vi/VKJH7Bn3WYE/maxresdefault.jpg", "fitness", "real"),
    ("https://img.youtube.com/vi/Mez0dP-GelU/maxresdefault.jpg", "fitness", "real"),
    ("https://img.youtube.com/vi/PKffm2uI4dk/maxresdefault.jpg", "fitness", "real"),
    ("https://img.youtube.com/vi/lDK9QqIzhwk/maxresdefault.jpg", "fitness", "real"),
    ("https://img.youtube.com/vi/5dsGWM5XGdg/maxresdefault.jpg", "fitness", "real"),
    ("https://img.youtube.com/vi/p2h1m7IQFPA/maxresdefault.jpg", "fitness", "real"),
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
    ("https://image.lexica.art/md2_webp/244318d2-154c-4158-8ef1-48f37f52e9b7", "fitness", "ai_generated"),
    ("https://image.lexica.art/md2_webp/25cb4ee6-603e-435f-be63-ba321560a6c2", "fitness", "ai_generated"),
    ("https://image.lexica.art/md2_webp/204f3025-2a46-4964-a2cd-ffb3fc2a6d3c", "fitness", "ai_generated"),
    ("https://image.lexica.art/md2_webp/1d0e1e49-7609-4ee0-bdc5-f05fac1549f9", "fitness", "ai_generated"),
    ("https://image.lexica.art/md2_webp/0bbf7d3a-557e-4bf7-8c5f-36e2156053d9", "fitness", "ai_generated"),
    ("https://image.lexica.art/md2_webp/0eb9e03c-9f46-45d6-84e5-6306f53ec514", "fitness", "ai_generated"),
    ("https://image.lexica.art/md2_webp/19fbe431-dacc-4a66-8810-0793a5f59cb8", "fitness", "ai_generated"),
    ("https://image.lexica.art/md2_webp/1b0f9533-cb1a-400b-8489-2790ce3cfeb9", "fitness", "ai_generated"),
]

PETS_REAL = [
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/2/26/YellowLabradorLooking_new.jpg/640px-YellowLabradorLooking_new.jpg", "pets", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/0/0b/Cat_poster_1.jpg/640px-Cat_poster_1.jpg", "pets", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/b/bb/Kittyply_edit1.jpg/640px-Kittyply_edit1.jpg", "pets", "real"),
    ("https://upload.wikimedia.org/wikipedia/commons/thumb/1/14/Gatto_europeo4.jpg/640px-Gatto_europeo4.jpg", "pets", "real"),
    ("https://img.youtube.com/vi/5dsGWM5XGdg/hqdefault.jpg", "pets", "real"),
    ("https://img.youtube.com/vi/lDK9QqIzhwk/hqdefault.jpg", "pets", "real"),
    ("https://img.youtube.com/vi/p2h1m7IQFPA/hqdefault.jpg", "pets", "real"),
    ("https://img.youtube.com/vi/PKffm2uI4dk/hqdefault.jpg", "pets", "real"),
    ("https://img.youtube.com/vi/NHozFX_ks-s/hqdefault.jpg", "pets", "real"),
    ("https://img.youtube.com/vi/tntOCGkgt98/hqdefault.jpg", "pets", "real"),
    ("https://img.youtube.com/vi/IqiTJK_uzuc/hqdefault.jpg", "pets", "real"),
    ("https://img.youtube.com/vi/GH0ePzBZhSs/hqdefault.jpg", "pets", "real"),
    ("https://img.youtube.com/vi/OtH6MkT7v0o/hqdefault.jpg", "pets", "real"),
    ("https://img.youtube.com/vi/K0ibBPhiaG0/hqdefault.jpg", "pets", "real"),
    ("https://img.youtube.com/vi/e-ORhEE9VVg/hqdefault.jpg", "pets", "real"),
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
    ("https://image.lexica.art/md2_webp/149211e2-c960-44e3-955c-2778d12de914", "pets", "ai_generated"),
    ("https://image.lexica.art/md2_webp/1b503ae9-5723-4d3c-842b-f99844343859", "pets", "ai_generated"),
    ("https://image.lexica.art/md2_webp/1de316fd-597b-42d4-8183-767e50778164", "pets", "ai_generated"),
    ("https://image.lexica.art/md2_webp/0cf36fd1-f693-4cc2-aeab-70ce9dbc1289", "pets", "ai_generated"),
    ("https://image.lexica.art/md2_webp/10d66aa4-ba6c-47e1-baaf-8c2920faa67f", "pets", "ai_generated"),
    ("https://image.lexica.art/md2_webp/12e82980-3352-4962-bcaa-f9ae6e091898", "pets", "ai_generated"),
    ("https://image.lexica.art/md2_webp/02c0cbdf-6f55-404f-a2aa-dc560a5c2e9a", "pets", "ai_generated"),
    ("https://image.lexica.art/md2_webp/0570d4b7-e6af-43ef-9ebe-dee427441410", "pets", "ai_generated"),
    ("https://image.lexica.art/md2_webp/00fa2342-a5bd-4a94-b0ab-4c2c59d5e9ba", "pets", "ai_generated"),
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
    ("https://img.youtube.com/vi/fJ9rUzIMcZQ/hqdefault.jpg", "fashion", "real"),
    ("https://img.youtube.com/vi/uO5_W1Yszdk/hqdefault.jpg", "fashion", "real"),
    ("https://img.youtube.com/vi/P_-FBukNEZE/hqdefault.jpg", "fashion", "real"),
    ("https://img.youtube.com/vi/whW4cqTHdWM/hqdefault.jpg", "fashion", "real"),
    ("https://img.youtube.com/vi/YwUFaKi85oM/hqdefault.jpg", "fashion", "real"),
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
    ("https://image.lexica.art/md2_webp/10e93c92-c15c-4473-a702-2d9a48c45840", "fashion", "ai_generated"),
    ("https://image.lexica.art/md2_webp/1457be48-a127-473a-affa-abb4a4446d1b", "fashion", "ai_generated"),
    ("https://image.lexica.art/md2_webp/115233e2-9fd2-4a9a-9b57-04258b66a9d6", "fashion", "ai_generated"),
    ("https://image.lexica.art/md2_webp/142a759e-cfbc-42d6-a6d5-603c6956d726", "fashion", "ai_generated"),
]

VIDEO_THUMB_REAL = [
    ("https://img.youtube.com/vi/dQw4w9WgXcQ/hqdefault.jpg", "video_thumbnail", "real"),
    ("https://img.youtube.com/vi/9bZkp7q19f0/hqdefault.jpg", "video_thumbnail", "real"),
    ("https://img.youtube.com/vi/kJQP7kiw5Fk/hqdefault.jpg", "video_thumbnail", "real"),
    ("https://img.youtube.com/vi/JGwWNGJdvx8/hqdefault.jpg", "video_thumbnail", "real"),
    ("https://img.youtube.com/vi/OPf0YbXqDm0/hqdefault.jpg", "video_thumbnail", "real"),
    ("https://img.youtube.com/vi/60ItHLz5WEA/hqdefault.jpg", "video_thumbnail", "real"),
    ("https://img.youtube.com/vi/2Vv-BfVoq4g/hqdefault.jpg", "video_thumbnail", "real"),
    ("https://img.youtube.com/vi/YqeW9_5kURI/hqdefault.jpg", "video_thumbnail", "real"),
    ("https://img.youtube.com/vi/IUN664s7N-c/hqdefault.jpg", "video_thumbnail", "real"),
    ("https://img.youtube.com/vi/B0hzDHbhRzY/hqdefault.jpg", "video_thumbnail", "real"),
    ("https://img.youtube.com/vi/GJLlxj_dtq8/hqdefault.jpg", "video_thumbnail", "real"),
    ("https://img.youtube.com/vi/Cxog8fMCkGA/hqdefault.jpg", "video_thumbnail", "real"),
    ("https://img.youtube.com/vi/4HqzYnRVWi8/hqdefault.jpg", "video_thumbnail", "real"),
    ("https://img.youtube.com/vi/ZZ5LpwO-An4/hqdefault.jpg", "video_thumbnail", "real"),
    ("https://img.youtube.com/vi/HKJR64VrxRQ/hqdefault.jpg", "video_thumbnail", "real"),
]

VIDEO_THUMB_AI = [
    ("https://image.lexica.art/md2_webp/4c5f6e65-c8b7-4c07-9c1e-3f7b67b48320", "video_thumbnail", "ai_generated"),
    ("https://image.lexica.art/md2_webp/545f701d-3c77-4193-b8ce-e9170f47177b", "video_thumbnail", "ai_generated"),
    ("https://image.lexica.art/md2_webp/54a83724-0454-4a92-a884-ce4c800ac043", "video_thumbnail", "ai_generated"),
    ("https://image.lexica.art/md2_webp/5128e577-3ff4-44af-aecc-d2a68c467d83", "video_thumbnail", "ai_generated"),
    ("https://image.lexica.art/md2_webp/3ded5227-e483-476d-a31b-f40893297915", "video_thumbnail", "ai_generated"),
    ("https://image.lexica.art/md2_webp/41206351-1bf0-47e6-a461-880c5fc18cd2", "video_thumbnail", "ai_generated"),
    ("https://image.lexica.art/md2_webp/1b503ae9-5723-4d3c-842b-f99844343859", "video_thumbnail", "ai_generated"),
    ("https://image.lexica.art/md2_webp/0fcdb628-0059-4e45-a9eb-47d6f19810e8", "video_thumbnail", "ai_generated"),
    ("https://image.lexica.art/md2_webp/00de1b0f-5c67-4f18-b958-790d95642776", "video_thumbnail", "ai_generated"),
    ("https://image.lexica.art/md2_webp/054b7bd2-4c9f-43d4-ab05-7e1c2a2cdded", "video_thumbnail", "ai_generated"),
    ("https://image.lexica.art/md2_webp/06ba916e-1fd3-4326-8c20-2d3964358c3c", "video_thumbnail", "ai_generated"),
    ("https://image.lexica.art/md2_webp/0aa8ecd9-561e-41b3-8600-b09b32fd1b59", "video_thumbnail", "ai_generated"),
    ("https://image.lexica.art/md2_webp/079ec4d7-e93a-420f-b942-7fa0ea09e8e9", "video_thumbnail", "ai_generated"),
    ("https://image.lexica.art/md2_webp/07367a21-4d22-43d3-a320-2da8b6853f3b", "video_thumbnail", "ai_generated"),
    ("https://image.lexica.art/md2_webp/1ea9e6f8-5757-4011-96d9-0069aa3d5812", "video_thumbnail", "ai_generated"),
]

# Build full test list (interleave real/AI per category for balanced testing)
ALL_TESTS = []
for real_list, ai_list in [
    (PORTRAIT_REAL, PORTRAIT_AI),
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

# Cap at 300
ALL_TESTS = ALL_TESTS[:300]

print(f"Total tests planned: {len(ALL_TESTS)}")


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
    else:  # ai_generated
        return ai_prob >= 0.65


def write_results(results, by_cat_stats, total_tested, total_correct, false_pos, false_neg):
    now = datetime.now(timezone.utc).isoformat()
    accuracy = total_correct / total_tested if total_tested > 0 else 0.0

    by_category = {}
    for cat, stats in by_cat_stats.items():
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
            "started_at": STARTED_AT,
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

    # Check for quota error
    detail = data.get("detail", "")
    if isinstance(detail, str) and any(kw in detail.lower() for kw in ["quota", "rate limit", "credit", "operations exceeded"]):
        print(f"  QUOTA ERROR: {detail[:200]}")
        return None, "QUOTA_ERROR"

    # Check for other backend errors
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


# Initialize category stats
CATEGORIES = ["portrait", "food", "landscape", "art", "fitness", "pets", "fashion", "video_thumbnail"]
by_cat_stats = {
    cat: {"total": 0, "correct": 0, "sum_prob_real": 0.0, "sum_prob_ai": 0.0, "count_real": 0, "count_ai": 0}
    for cat in CATEGORIES
}

results = []
total_tested = 0
total_correct = 0
false_pos = 0
false_neg = 0

# Write initial empty file
write_results(results, by_cat_stats, 0, 0, 0, 0)

print(f"Starting calibration: {len(ALL_TESTS)} images planned")
print(f"Backend: {BACKEND}")
print(f"Output: {OUTPUT}")
print("-" * 60)

for i, (url, category, ground_truth) in enumerate(ALL_TESTS):
    test_id = i + 1
    print(f"[{test_id}/{len(ALL_TESTS)}] {category} ({ground_truth}) {url[:70]}...")

    result, status = scan_image(test_id, url, category, ground_truth)

    if status == "QUOTA_ERROR":
        print("QUOTA LIMIT REACHED - stopping immediately!")
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
        write_results(results, by_cat_stats, total_tested, total_correct, false_pos, false_neg)

    # Sleep 10s between requests (skip after last)
    if i < len(ALL_TESTS) - 1 and status != "QUOTA_ERROR":
        print(f"  sleeping 10s...")
        time.sleep(10)

# Final write
write_results(results, by_cat_stats, total_tested, total_correct, false_pos, false_neg)

# Add summary
overall_acc = total_correct / total_tested if total_tested > 0 else 0.0
real_total = sum(s["count_real"] for s in by_cat_stats.values())
ai_total = sum(s["count_ai"] for s in by_cat_stats.values())
fp_rate = false_pos / real_total if real_total > 0 else 0.0
fn_rate = false_neg / ai_total if ai_total > 0 else 0.0

by_category_final = {}
for cat, stats in by_cat_stats.items():
    t = stats["total"]
    c = stats["correct"]
    acc = c / t if t > 0 else 0.0
    avg_real = stats["sum_prob_real"] / stats["count_real"] if stats["count_real"] > 0 else 0.0
    avg_ai = stats["sum_prob_ai"] / stats["count_ai"] if stats["count_ai"] > 0 else 0.0
    by_category_final[cat] = {"total": t, "correct": c, "accuracy": round(acc, 4), "avg_prob_real": round(avg_real, 4), "avg_prob_ai": round(avg_ai, 4)}

cats_with_data = [(cat, s) for cat, s in by_category_final.items() if s["total"] > 0]
best_cat = max(cats_with_data, key=lambda x: x[1]["accuracy"])[0] if cats_with_data else "N/A"
worst_cat = min(cats_with_data, key=lambda x: x[1]["accuracy"])[0] if cats_with_data else "N/A"

if fp_rate > 0.15:
    threshold_rec = "raise to 0.70 - too many false positives on real images"
elif fn_rate > 0.20:
    threshold_rec = "lower to 0.55 - too many false negatives on AI images"
else:
    threshold_rec = "keep 0.65 - current threshold performing well"

with open(OUTPUT) as f:
    final_data = json.load(f)

final_data["summary"] = {
    "total_tested": total_tested,
    "overall_accuracy": round(overall_acc, 4),
    "false_positive_rate": round(fp_rate, 4),
    "false_negative_rate": round(fn_rate, 4),
    "best_category": best_cat,
    "worst_category": worst_cat,
    "threshold_recommendation": threshold_rec,
    "notes": (
        f"Tested {total_tested} images across 8 social media categories. "
        f"{total_correct} correct classifications. "
        f"FP={false_pos} (real misclassified as AI), FN={false_neg} (AI misclassified as real). "
        f"Real sources: YouTube thumbnails + Wikimedia Commons. "
        f"AI sources: Lexica.art generated images."
    ),
}

with open(OUTPUT, "w") as f:
    json.dump(final_data, f, indent=2)

print("\n" + "=" * 60)
print(f"CALIBRATION COMPLETE")
print(f"Total tested: {total_tested}")
print(f"Overall accuracy: {overall_acc:.3f}")
print(f"False positive rate: {fp_rate:.3f}")
print(f"False negative rate: {fn_rate:.3f}")
print(f"Best category: {best_cat}")
print(f"Worst category: {worst_cat}")
print(f"Threshold recommendation: {threshold_rec}")
print(f"Results saved to: {OUTPUT}")
