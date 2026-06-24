# Agent AURA — Final Backend API Plan

## Route Summary

```
Campaign    POST /campaigns/create · GET /campaigns · GET /campaigns/{id}
Poster      POST /posters/generate/{campaign_id} · GET /posters/{id} · POST /posters/{id}/regenerate
Poll        POST /polls/generate/{poster_id} · GET /polls/{id}
Revision    POST /revisions/{poster_id} · GET /revisions/{id} · GET /campaigns/{id}/revisions
Approval    POST /approval/{poster_id}/approve · POST /approval/{poster_id}/reject · POST /approval/{poster_id}/request-change
System      GET /health
```

---

## Async Generation Design

The campaign is created first — Gemini plans all 5 days (text only, no images). Posters are then generated **one day at a time**, manually triggered by the human. Each generation runs as a **FastAPI `BackgroundTask`**.

```
POST /campaigns/create
        │
        └── Gemini → 5-day content plan (themes, prompts, text)
            Campaign status: "ready"
            All poster_ids: null  (no images yet)

Human triggers each day:
POST /posters/generate/{campaign_id}  { "day": 1 }
        │
        ├── Immediately returns 202
        │
        └── Background Task:
                Image Model → raw image for Day 1
                Pillow → composite logo + mascots + text
                Cloudinary → upload
                DB → create poster record (status: pending)
                Campaign Day 1 poster_id → populated

Frontend polls GET /campaigns/{id}
    until days[0].poster_id is not null
    Human reviews → approve / reject / request-change
    Then triggers Day 2, and so on.
```

**Campaign `status` enum:** `draft` → `ready` → `failed`  
**Poster `status` enum:** `generating` → `pending` → `approved` → `rejected` → `revision_requested`  
**Day `poster_id`:** `null` until generation is triggered for that day

---

## 1. Campaign Routes

### `POST /campaigns/create`
Kicks off the campaign. Gemini plans all 5 days. Returns immediately — generation continues in background.

**Request:**
```json
{
  "topic": "AI Safety in Manufacturing",
  "objective": "Educate employees on responsible AI use",
  "session_id": "uuid-optional"
}
```
**Response `202 Accepted`:**
```json
{
  "campaign_id": "uuid",
  "session_id": "uuid",
  "status": "generating",
  "topic": "AI Safety in Manufacturing",
  "objective": "Educate employees on responsible AI use",
  "created_at": "2026-06-18T..."
}
```

---

### `GET /campaigns`
List all campaigns. Used by the History and Campaigns pages.

**Response `200`:**
```json
[
  {
    "campaign_id": "uuid",
    "topic": "AI Safety in Manufacturing",
    "status": "ready",
    "created_at": "2026-06-18T..."
  }
]
```
```

---

### `GET /campaigns/{id}`
Full campaign detail. Frontend polls this until `status == "ready"`. Also returns revision history link.

**Response `200`:**
```json
{
  "campaign_id": "uuid",
  "session_id": "uuid",
  "topic": "AI Safety in Manufacturing",
  "objective": "Educate employees on responsible AI use",
  "status": "ready",
  "created_at": "2026-06-18T...",
  "days": [
    {
      "day": 1,
      "day_name": "Monday",
      "theme": "What is AI?",
      "poster_id": "uuid",
      "poll_id": "uuid"
    }
  ]
}
```

---

## 2. Poster Routes

### `POST /posters/generate/{campaign_id}`
Triggers async background generation of a **single poster for the specified day**. The campaign must already exist (Gemini plan is in DB). Can be re-called if a day's generation failed.

**Request:**
```json
{
  "day": 1
}
```
*`day` must be 1–5. Validated against the campaign's existing day plan.*

**Response `202 Accepted`:**
```json
{
  "campaign_id": "uuid",
  "day": 1,
  "day_name": "Monday",
  "status": "generating",
  "message": "Poster generation for Day 1 started in background"
}
```

---

### `GET /posters/{id}`
Returns a single poster with its full data.

**Response `200`:**
```json
{
  "poster_id": "uuid",
  "campaign_id": "uuid",
  "day": 1,
  "day_name": "Monday",
  "theme": "What is AI?",
  "image_url": "https://res.cloudinary.com/...",
  "image_prompt": "A glowing factory floor with AI holographic nodes...",
  "text_overlay": "AI is here to help you work smarter.",
  "status": "pending",
  "version": 1,
  "created_at": "2026-06-18T..."
}
```

---

### `POST /posters/{id}/regenerate`
Manually trigger regeneration of a single poster (no feedback — just retry). Runs async.

**Request body:** *(empty)*

**Response `202 Accepted`:**
```json
{
  "poster_id": "uuid",
  "status": "generating",
  "message": "Poster regeneration started in background"
}
```

---

## 3. Poll Routes

### `POST /polls/generate/{poster_id}`
Generates a poll for a specific day's poster using Gemini. Tied to the poster because the poll topic mirrors the poster theme.

**Request body:** *(empty — poster context fetched from DB)*

**Response `201 Created`:**
```json
{
  "poll_id": "uuid",
  "poster_id": "uuid",
  "campaign_id": "uuid",
  "day": 1,
  "day_name": "Monday",
  "question": "How familiar are you with AI tools in your daily work?",
  "options": [
    "Very familiar",
    "Somewhat familiar",
    "Not familiar at all"
  ],
  "created_at": "2026-06-18T..."
}
```

---

### `GET /polls/{id}`
Returns a single poll.

**Response `200`:**
```json
{
  "poll_id": "uuid",
  "poster_id": "uuid",
  "campaign_id": "uuid",
  "day": 1,
  "day_name": "Monday",
  "question": "How familiar are you with AI tools in your daily work?",
  "options": ["Very familiar", "Somewhat familiar", "Not familiar at all"],
  "created_at": "2026-06-18T..."
}
```

---

## 4. Revision Routes

### `POST /revisions/{poster_id}`
Submit human feedback on a poster. Gemini generates a targeted revision plan, then kicks off async regeneration of only the changed components.

**Request:**
```json
{
  "feedback": "Make Arjun more friendly, use a blue colour theme instead of green"
}
```
**Response `202 Accepted`:**
```json
{
  "revision_id": "uuid",
  "poster_id": "uuid",
  "feedback": "Make Arjun more friendly...",
  "revision_plan": {
    "changes": [
      { "component": "image_prompt", "action": "modify", "change": "Arjun smiling, warm gesture, blue palette..." },
      { "component": "text_overlay", "action": "keep" }
    ]
  },
  "status": "regenerating",
  "created_at": "2026-06-18T..."
}
```

---

### `GET /revisions/{id}`
Get the result of a specific revision — including the new poster once ready.

**Response `200`:**
```json
{
  "revision_id": "uuid",
  "poster_id": "uuid",
  "feedback": "...",
  "revision_plan": { ... },
  "new_poster_id": "uuid",
  "status": "complete",
  "created_at": "2026-06-18T..."
}
```

---

### `GET /campaigns/{id}/revisions`
Full revision history for a campaign. Used by the history/audit view.

**Response `200`:**
```json
[
  {
    "revision_id": "uuid",
    "poster_id": "uuid",
    "day": 2,
    "feedback": "...",
    "status": "complete",
    "created_at": "2026-06-18T..."
  }
]
```

---

## 5. Approval Routes

Three distinct human decisions. `request-change` is the trigger that also creates a revision record automatically.

### `POST /approval/{poster_id}/approve`
Marks poster as approved and finalises it for publishing.

**Request body:** *(empty)*

**Response `200`:**
```json
{
  "poster_id": "uuid",
  "status": "approved",
  "message": "Poster approved and published"
}
```

---

### `POST /approval/{poster_id}/reject`
Marks poster as permanently rejected. No regeneration triggered.

**Request body:** *(empty)*

**Response `200`:**
```json
{
  "poster_id": "uuid",
  "status": "rejected",
  "message": "Poster rejected"
}
```

---

### `POST /approval/{poster_id}/request-change`
Human wants a specific change. Automatically creates a revision record and triggers async regeneration.

**Request:**
```json
{
  "feedback": "The text is too small. Make the headline larger and bolder."
}
```
**Response `202 Accepted`:**
```json
{
  "poster_id": "uuid",
  "status": "revision_requested",
  "revision_id": "uuid",
  "message": "Change request received. Revision in progress."
}
```

---

## 6. System Route

### `GET /health`
**Response `200`:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "timestamp": "2026-06-18T..."
}
```

---

## Files to Create / Modify

### Core

| File | Action | Notes |
|------|--------|-------|
| [main.py](file:///c:/Users/BIT/OneDrive%20-%20Birla%20Institute%20of%20Technology/Desktop/AURA%20Agent/backend/app/main.py) | MODIFY | FastAPI app, CORS, include all routers |
| [config.py](file:///c:/Users/BIT/OneDrive%20-%20Birla%20Institute%20of%20Technology/Desktop/AURA%20Agent/backend/app/config.py) | MODIFY | `Settings` class via pydantic-settings loading `.env` |

### Models

| File | Action | Key Fields |
|------|--------|-----------|
| [campaign.py](file:///c:/Users/BIT/OneDrive%20-%20Birla%20Institute%20of%20Technology/Desktop/AURA%20Agent/backend/app/models/campaign.py) | MODIFY | `id, session_id, topic, objective, status, created_at` |
| [poster.py](file:///c:/Users/BIT/OneDrive%20-%20Birla%20Institute%20of%20Technology/Desktop/AURA%20Agent/backend/app/models/poster.py) | MODIFY | `id, campaign_id, day, day_name, theme, image_url, image_prompt, text_overlay, status, version, created_at` |
| [poll.py](file:///c:/Users/BIT/OneDrive%20-%20Birla%20Institute%20of%20Technology/Desktop/AURA%20Agent/backend/app/models/poll.py) | MODIFY | `id, campaign_id, poster_id, day, day_name, question, options(JSON), created_at` |
| `revision.py` | NEW | `id, poster_id, campaign_id, feedback, revision_plan(JSON), new_poster_id, status, created_at` |

### Schemas

| File | Action | Schemas |
|------|--------|---------|
| [campaign.py](file:///c:/Users/BIT/OneDrive%20-%20Birla%20Institute%20of%20Technology/Desktop/AURA%20Agent/backend/app/schemas/campaign.py) | MODIFY | `CampaignCreate`, `CampaignResponse`, `CampaignListItem` |
| [poster.py](file:///c:/Users/BIT/OneDrive%20-%20Birla%20Institute%20of%20Technology/Desktop/AURA%20Agent/backend/app/schemas/poster.py) | MODIFY | `PosterResponse`, `RequestChangeBody` |
| `poll.py` | NEW | `PollResponse` |
| `revision.py` | NEW | `RevisionCreate`, `RevisionResponse` |

### API Routers

| File | Action |
|------|--------|
| [campaigns.py](file:///c:/Users/BIT/OneDrive%20-%20Birla%20Institute%20of%20Technology/Desktop/AURA%20Agent/backend/app/api/campaigns.py) | MODIFY |
| [posters.py](file:///c:/Users/BIT/OneDrive%20-%20Birla%20Institute%20of%20Technology/Desktop/AURA%20Agent/backend/app/api/posters.py) | MODIFY |
| [polls.py](file:///c:/Users/BIT/OneDrive%20-%20Birla%20Institute%20of%20Technology/Desktop/AURA%20Agent/backend/app/api/polls.py) | MODIFY |
| `revisions.py` | NEW |
| `approval.py` | NEW |

### Services

| File | Action | Key Functions |
|------|--------|---------------|
| [gemini_service.py](file:///c:/Users/BIT/OneDrive%20-%20Birla%20Institute%20of%20Technology/Desktop/AURA%20Agent/backend/app/services/gemini_service.py) | MODIFY | `generate_campaign_plan()`, `generate_revision_plan()`, `generate_poll()` |
| [image_service.py](file:///c:/Users/BIT/OneDrive%20-%20Birla%20Institute%20of%20Technology/Desktop/AURA%20Agent/backend/app/services/image_service.py) | MODIFY | `generate_image()`, `composite_poster()`, `upload_to_cloudinary()` |
| [revision_service.py](file:///c:/Users/BIT/OneDrive%20-%20Birla%20Institute%20of%20Technology/Desktop/AURA%20Agent/backend/app/services/revision_service.py) | MODIFY | `process_revision()` — orchestrates full revision pipeline |

### Frontend

| File | Action |
|------|--------|
| [api.py](file:///c:/Users/BIT/OneDrive%20-%20Birla%20Institute%20of%20Technology/Desktop/AURA%20Agent/frontend/services/api.py) | MODIFY — wire all new endpoints |

---

## Verification Plan

```bash
# 1. Start the server
uvicorn app.main:app --reload

# 2. Health check
curl http://localhost:8000/health

# 3. Open Swagger UI — verify all routers appear
http://localhost:8000/docs

# 4. Full flow test via Swagger:
#    POST /campaigns/create → get campaign_id
#    POST /posters/generate/{id} → 202
#    Poll GET /campaigns/{id} until status == "ready"
#    GET /posters/{id} → verify image_url populated
#    POST /approval/{poster_id}/approve → 200
#    POST /revisions/{poster_id} + feedback → 202
#    GET /revisions/{revision_id} → verify new_poster_id
```
