# AI Detector App — Project Master Plan
### Thornveil LLC | Unnamed (working title: "RealCheck")

---

## What This App Is

A consumer-facing, multi-modal AI content detection app with iOS share sheet integration. Users share any social media post directly into the app from Instagram, TikTok, X, etc. and get an instant AI probability score with plain-English explanations.

**The core differentiator:** Share sheet integration + multi-modal (image + caption analyzed together) + consumer-first UX. No competitor has this combination.

---

## API Stack

| Content Type     | Primary API                  | Backup            |
|------------------|------------------------------|-------------------|
| Images           | Sightengine (genai model)    | Hive Image        |
| Video            | Sightengine (AI video)       | Hive Video        |
| Text / Captions  | GPTZero                      | Hive Text         |
| Audio            | Hive Audio                   | —                 |
| Deepfake Faces   | Sightengine (deepfake model) | —                 |

**Sightengine pricing:** Free tier 2,000 ops/month → Starter $29/mo (10K ops) → Pro $99/mo (40K ops)
**GPTZero pricing:** Free 10K words/month → API from $45/mo (300K words)
**Hive:** Developer free credits → Enterprise pricing (less transparent)

---

## Architecture

```
iOS App (React Native or Swift)
  ├── Main App UI (results, history, subscription management)
  └── Share Extension (accepts URLs/images/text from any app)
          │
          ▼ HTTPS
    Backend (Python FastAPI on Railway)
          │
    ┌─────┼─────┐
    ▼     ▼     ▼
Sightengine  GPTZero  Hive
```

### Backend Responsibilities
- Route content to correct API(s) based on type
- Aggregate multi-modal results (image + caption) into unified score
- Generate plain-English "why we think this" explanations
- Handle user accounts, scan history, freemium limits
- SQLite (Railway volume) for users/scans/subscriptions

### Frontend Responsibilities
- Share extension: compact "Analyzing..." → results UI
- Main app: results view with color-coded confidence, history, scan counter
- Subscription management (StoreKit 2 for iOS)

---

## Phase Roadmap

### Phase 1 — MVP Web App (Current Phase)
**Goal:** Working end-to-end scan via a web UI (paste text or upload image → get result)
**Stack:** Python FastAPI backend + React/Vite frontend (deployed on Railway + Netlify)
**Deliverables:**
- [ ] FastAPI backend with `/api/scan` endpoint
- [x] Sightengine integration (image scanning) — calibrated 98.2% accuracy
- [ ] GPTZero integration (text scanning)
- [x] Hive audio integration — migrated to V3 API, calibrated 94.7% accuracy
- [x] React frontend: text / image / video / audio tabs; drag+drop upload; URL inputs; results view
- [x] Color-coded confidence score display (green/yellow/red) with animated probability meter
- [x] "Why we think this" explanation section with sentence-level highlights
- [ ] Deploy backend to Railway
- [ ] Deploy frontend to Netlify

### Phase 2 — URL Extraction + Scan History
**Goal:** Paste a social media URL and have the backend extract content
**Deliverables:**
- [ ] URL → content extraction (download image/video from link)
- [ ] User accounts (Supabase auth, same pattern as ForkThis)
- [ ] Scan history stored in SQLite
- [ ] SQLite schema: `users`, `scans` tables
- [ ] Freemium limits (5 free scans/day)

### Phase 3 — iOS App + Share Sheet
**Goal:** Native iOS experience with share extension
**Deliverables:**
- [ ] React Native app (or Swift)
- [ ] iOS Share Extension accepting URLs, images, text
- [ ] Compact share extension UI (quick results in-line)
- [ ] Full app results view with deep-dive breakdown
- [ ] StoreKit 2 subscription ($2.99/mo or $19.99/yr)

### Phase 4 — Multi-Modal + Explainability
**Goal:** Analyze image AND caption together; identify suspected AI model
**Deliverables:**
- [ ] Multi-modal score aggregation
- [ ] "Suspected source: Midjourney / DALL-E / ChatGPT" display
- [ ] Sentence-level text highlighting (GPTZero feature)
- [ ] Video scanning (frame-by-frame via Sightengine)
- [ ] Audio detection (Hive)

### Phase 5 — Growth Features
- [ ] Android support
- [ ] Browser extension (Safari/Chrome)
- [ ] "AI Score" badge users can share back to social
- [ ] Community reporting / crowdsourced verification
- [ ] PWA for web access

---

## Cost Model

**At launch (free API tiers):** ~$0–$50/month
**At 10K MAU (15 scans/user/month):**
- Image scans (90K): ~$174/mo (Sightengine Pro + overages)
- Text scans (45K): ~$75/mo (GPTZero API)
- Video scans (15K, 5 ops each): ~$112/mo (Sightengine overages)
- **Total: ~$360/mo**

**Revenue at 10K MAU (5% paid conversion):** 500 × $2.99 = **$1,495/mo**
**Margin: ~75%**

---

## Revenue Model

- **Free tier:** 5 scans/day (or 3 video scans/day — expensive)
- **Pro:** $2.99/month or $19.99/year — unlimited scans, history, explainability
- **Credit packs:** Optional one-time purchase for heavy users

---

## Key Technical Risks

1. **False positives** — Never show binary "IS AI" verdict. Always show probability + confidence. Frame as "likely" / "uncertain" / "probably human".
2. **Instagram/TikTok URL extraction** — Platforms block scraping. May need to ask users to save/screenshot content first, or rely on the share sheet providing the raw image bytes directly (which it does for images).
3. **Video cost** — Frame-by-frame analysis is expensive. Limit free video scans to 1–2/day.
4. **App Store review** — Use careful language: "helps identify potentially AI-generated content" not "detects all AI".
5. **Arms race** — Offloaded to Sightengine/GPTZero who maintain model accuracy.
6. **Hive credits deplete fast** — $1.00 free credits ≈ 19 audio tests. Monitor balance before running calibration or load tests.

---

## API Debugging Notes

### Hive V3 Audio API (updated 2026-03-22)
- **Correct endpoint:** `POST /api/v3/hive/ai-generated-and-deepfake-content-detection`
- **Auth:** `Authorization: Bearer <HIVE_SECRET_KEY>` — NOT the V2 `access-key-id`/`secret-key` header scheme
- **File upload:** Must POST audio as multipart bytes. Hive's URL fetcher cannot reach Wikimedia, GitHub, or HuggingFace domains.
- **Response path:** `output[].classes[].value` where class name = `ai_generated_audio`
- **MIME types:** Must be dynamic (wav→`audio/wav`, mp3→`audio/mpeg`); do not hardcode.
- **Score aggregation:** Use `max()` across all 10-second chunks for worst-case safety.

### Sightengine URL Fetcher
- Cannot reach Wikimedia or Picsum CDN domains (returns 502). Use direct CDN sources or download locally for calibration.

### General Third-Party Download Headers
- Some servers (e.g., voiptroubleshooter.com) require full browser User-Agent + `Accept` + `Accept-Encoding: identity` headers or return 406.
- HuggingFace LFS files on public repos are reliable for audio calibration without auth.

---

## Calibration Results (2026-03-22)

| Modality | API            | Accuracy | FP  | FN  | Test Count | Output File                          |
|----------|----------------|----------|-----|-----|------------|--------------------------------------|
| Image    | Sightengine    | 98.2%    | 0%  | 2%  | 56         | `backend/calibration/image_accuracy_v2_results.json` |
| Audio    | Hive V3        | 94.7%    | 0%  | 0%  | 19         | `backend/calibration/audio_accuracy_results.json`    |

**Recommended score thresholds (0% FP on calibration sets):**
- 0.00–0.30 → Likely Human (green)
- 0.31–0.69 → Uncertain (yellow)
- 0.70–1.00 → Likely AI (red)

---

## Naming Ideas (Unnamed)

Working suggestions from research doc:
- **RealCheck**
- **TrueOrAI**
- **SourceScan**
- **AIScan**
- (TBD — user has not chosen a name yet)

---

## Environment Variables Required

```
SIGHTENGINE_API_USER=       # Sightengine user ID
SIGHTENGINE_API_SECRET=     # Sightengine secret
GPTZERO_API_KEY=            # GPTZero API key
HIVE_SECRET_KEY=            # Hive bearer token (Authorization: Bearer header)
HIVE_ACCESS_KEY_ID=         # Hive key rotation ID (not used in API requests)
SUPABASE_URL=               # optional Phase 2+
SUPABASE_ANON_KEY=          # optional Phase 2+
RAILWAY_SERVER_URL=         # for frontend proxy
```

---

## Project Directory Structure (Target)

```
ai-detector/
├── CLAUDE.md              ← This file
├── backend/
│   ├── main.py            ← FastAPI app entry point
│   ├── routers/
│   │   └── scan.py        ← /api/scan endpoint
│   ├── services/
│   │   ├── sightengine.py ← Image/video detection
│   │   ├── gptzero.py     ← Text detection
│   │   └── hive.py        ← Audio detection (Phase 4)
│   ├── models.py          ← Pydantic request/response models
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── ScanInput.tsx
│   │   │   └── ScanResult.tsx
│   │   └── main.tsx
│   ├── index.html
│   ├── vite.config.ts
│   └── package.json
└── README.md
```

---

## Current Status

**Phase:** 1 — MVP Web App (in progress)
**Started:** 2026-03-18
**Last session:** 2026-03-22
**App name:** TBD (candidates: RealCheck, TrueOrAI, SourceScan, AIScan)
**APIs signed up for:** Sightengine (active), GPTZero (active), Hive (active — monitor credits)
**Calibration complete:** Image (98.2%) + Audio (94.7%)
**Next steps:** FastAPI `/api/scan` endpoint wiring + Railway deploy + Netlify deploy

---

## Decision Log

| Date       | Decision                                             | Reason                                                    |
|------------|------------------------------------------------------|-----------------------------------------------------------|
| 2026-03-18 | Start with web app MVP before iOS                    | Faster iteration, no App Store review needed for testing  |
| 2026-03-18 | FastAPI over Flask                                   | Better async support, auto-generated OpenAPI docs         |
| 2026-03-18 | Sightengine + GPTZero primary stack                  | Transparent pricing, best-in-class accuracy for each type |
| 2026-03-18 | React/Vite frontend (same pattern as ForkThis)       | Reuse deployment knowledge, familiar toolchain            |
| 2026-03-22 | Rewrote hive.py for V3 API (complete migration)      | V2 endpoint 404s; V3 uses different auth, endpoint, and response schema |
| 2026-03-22 | Audio calibration uses download-then-upload pattern  | Hive URL fetcher cannot reach GitHub/HuggingFace/Wikimedia |
| 2026-03-22 | Score threshold: 0.70+ = Likely AI (not 0.50+)      | Calibration shows real scores top out at 0.49; avoids FP |
| 2026-03-22 | Frontend redesigned — forensic tool aesthetic         | Syne + IBM Plex Mono fonts; animated verdict reveal; 4-tab input (text/image/video/audio); CSS grid background |
