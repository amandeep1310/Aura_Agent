# 🤖 Agent AURA — AI Campaign Generator

> An AI-powered internal communication system for **Tata Steel AURA** that generates a full Monday–Friday awareness campaign — posters, polls, and content — from a single weekly topic.

---

## 📌 Overview

Agent AURA takes a weekly topic and campaign objective as input and uses **Gemini 2.5 Flash** to plan a 5-day AI awareness campaign. It generates poster content, image prompts, and polls for each day. A human approves or requests changes before anything is published.

---

## ✨ Features

- 🗓️ **5-Day Campaign Planner** — Gemini breaks down the topic into a full Mon–Fri plan
- 🖼️ **AI Poster Generator** — Image models create visuals; Pillow overlays logos and text
- 📊 **Poll Generator** — Auto-generates daily engagement polls
- ✅ **Human Approval Workflow** — Approve or reject each poster before publishing
- 🔁 **Revision Engine** — Provide feedback and regenerate only what needs to change
- 📦 **Cloudinary Storage** — All approved posters stored and served via Cloudinary
- 🧾 **Session Tracking & Logging** — Every request is traced with a unique session ID

---

## 🏗️ Architecture

```
User Input (Topic + Objective)
        │
        ▼
  Gemini 2.5 Flash  ──►  5-Day Campaign Plan
        │                  Poster Specs
        │                  Image Prompts
        │                  Poll Questions
        ▼
  Image Model (FLUX / Imagen)
        │
        ▼
  Pillow Composer  ──►  Overlays logos, mascots, text
        │
        ▼
  Cloudinary Upload
        │
        ▼
  Human Approval Interface (Streamlit)
        │
   ┌────┴────┐
   ▼         ▼
Approve   Reject + Feedback
   │         │
Publish   Revision Engine ──► Regenerate
```

---

## 🗂️ Project Structure

```
AURA Agent/
├── backend/
│   ├── app/
│   │   ├── main.py                   # FastAPI entry point
│   │   ├── config.py                 # Environment settings
│   │   ├── api/
│   │   │   ├── campaigns.py          # Campaign routes
│   │   │   ├── posters.py            # Poster routes
│   │   │   └── polls.py              # Poll routes
│   │   ├── services/
│   │   │   ├── gemini_service.py     # LLM planning & prompting
│   │   │   ├── image_service.py      # Image gen + Pillow + Cloudinary
│   │   │   └── revision_service.py   # Feedback & regeneration
│   │   ├── models/
│   │   │   ├── campaign.py           # DB table: campaigns
│   │   │   ├── poster.py             # DB table: posters
│   │   │   └── poll.py               # DB table: polls
│   │   ├── schemas/
│   │   │   ├── campaign.py           # Pydantic: campaign I/O
│   │   │   └── poster.py             # Pydantic: poster I/O
│   │   └── utils/
│   │       ├── logger.py             # Centralized logging
│   │       └── session.py            # Session ID generation
│   ├── assets/                       # Fixed brand assets
│   │   ├── tata_steel_logo.png
│   │   ├── aura_logo.png
│   │   ├── arjun_mascot.png
│   │   └── aura_mascot.png
│   ├── .env.example                  # Environment variable template
│   └── requirements.txt
│
├── frontend/                         # Streamlit dashboard
│   ├── app.py
│   ├── pages/
│   ├── components/
│   ├── services/
│   ├── utils/
│   └── requirements.txt
│
└── README.md
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Streamlit |
| **Backend** | FastAPI (Python) |
| **LLM** | Gemini 2.5 Flash |
| **Image Generation** | FLUX / Imagen / OpenAI |
| **Image Processing** | Pillow |
| **Storage** | Cloudinary |
| **Database** | PostgreSQL + SQLAlchemy |

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/your-org/aura-agent.git
cd aura-agent
```

### 2. Set up the Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Copy the environment file and fill in your keys:

```bash
copy .env.example .env
```

Run the FastAPI server:

```bash
uvicorn app.main:app --reload
```

### 3. Set up the Frontend

```bash
cd frontend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
streamlit run app.py
```

---

## 🔑 Environment Variables

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Gemini 2.5 Flash API key |
| `IMAGE_MODEL_API_KEY` | FLUX / Imagen / OpenAI API key |
| `CLOUDINARY_CLOUD_NAME` | Cloudinary cloud name |
| `CLOUDINARY_API_KEY` | Cloudinary API key |
| `CLOUDINARY_API_SECRET` | Cloudinary API secret |
| `DATABASE_URL` | PostgreSQL connection string |

---

## 🎨 Fixed Brand Assets

All brand assets are stored in `backend/assets/` and are never generated by AI:

- `tata_steel_logo.png` — Tata Steel official logo
- `aura_logo.png` — AURA product logo
- `arjun_mascot.png` — Arjun mascot character
- `aura_mascot.png` — AURA mascot character

These are composited onto every generated poster by Pillow.

---

## 🔄 Campaign Workflow

1. User enters **Weekly Topic** + **Campaign Objective**
2. Gemini generates a **5-day content plan**
3. For each day, a **poster spec + image prompt + poll** is created
4. The image model generates the **visual**
5. Pillow **composites** logos, mascots, and text onto the image
6. The poster is uploaded to **Cloudinary**
7. The human **reviews** on the Streamlit dashboard
8. On **approval** → published; on **rejection** → feedback sent to revision engine

---

## 👥 Audience & Branding

- **Audience:** All Tata Steel employees
- **Theme:** AURA AI awareness
- **Tone:** Informative, engaging, inspiring
- **Mascots:** Arjun & AURA (consistent across all posters)

---

## 📄 License

Internal use only — Tata Steel AURA Team.
