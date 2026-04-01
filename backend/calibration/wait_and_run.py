#!/usr/bin/env python
"""
Polls Sightengine every 30 minutes until daily quota resets, then runs continue_calibration.py.
"""
import subprocess
import time
import json
from datetime import datetime, timezone

BACKEND = "http://localhost:8001/api/scan"
TEST_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Good_Food_Display_-_NCI_Visuals_Online.jpg/640px-Good_Food_Display_-_NCI_Visuals_Online.jpg"
CONTINUE_SCRIPT = "C:/Users/ckbaw/Desktop/Thornveil_LLC/ai-detector/backend/calibration/continue_calibration.py"
POLL_INTERVAL_SECONDS = 30 * 60  # 30 minutes


def test_quota():
    """Returns True if quota is available (no quota error), False if still blocked."""
    try:
        result = subprocess.run(
            ["curl", "-s", "-X", "POST", BACKEND, "-F", f"image_url={TEST_URL}"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        text = result.stdout.strip()
        if not text:
            return False
        data = json.loads(text)
        detail = data.get("detail", "")
        if isinstance(detail, str) and any(kw in detail.lower() for kw in ["quota", "daily", "usage_limit"]):
            return False
        # Either success or a different kind of error (image fetch error etc.) - quota is clear
        return True
    except Exception as e:
        print(f"  Poll error: {e}")
        return False


print(f"Quota poller started at UTC {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}")
print(f"Will poll every 30 minutes until Sightengine daily quota resets")
print(f"Then will automatically run: {CONTINUE_SCRIPT}")
print()

attempt = 0
while True:
    attempt += 1
    now_utc = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    print(f"[Attempt {attempt}] {now_utc} - testing quota...")

    if test_quota():
        print(f"  QUOTA CLEARED! Starting calibration run...")
        result = subprocess.run(
            ["python", CONTINUE_SCRIPT],
            timeout=7200,  # 2 hour timeout
        )
        print(f"  Calibration finished with exit code {result.returncode}")
        break
    else:
        print(f"  Still blocked. Next check in 30 minutes...")
        time.sleep(POLL_INTERVAL_SECONDS)
