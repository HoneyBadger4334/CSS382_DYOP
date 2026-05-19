# UW Bothell Campus Pulse

Real-time interactive map of UW Bothell displaying campus events and emergency alerts.
Built with Next.js, FastAPI, OpenStreetMap (Leaflet), and GPT-4o-mini.

## Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 14 + TypeScript + react-leaflet |
| Map | OpenStreetMap via Leaflet |
| Backend | FastAPI + Python 3.11 |
| AI | GPT-4o-mini (NLP alert summarizer) |
| Database | PostgreSQL / Supabase *(Week 9)* |
| Deployment | Vercel (frontend) + Render or Railway (backend) |

## Milestone Status

| Milestone | Status | Criteria |
|---|---|---|
| Week 7 | ✅ | Map renders UW Bothell; test pin at UW1 |
| Week 8 (MVP) | ✅ | RSS feed + NLP summarizer + fallback banner |
| Week 9 (Testing) | 🔲 | Event recommender + peer testing |
| Week 10 (Final) | 🔲 | Public deploy + project website final |

## Quick Start

### Backend

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cp ../.env.example .env
# Edit .env and add your OPENAI_API_KEY

uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev         # opens http://localhost:3000
```

### NLP Test Suite (Week 8 acceptance criterion)

```bash
cd backend
source venv/bin/activate
python test_nlp_summarizer.py
# Must show ≥90% (18/20) valid JSON responses
```

## Architecture

```
Browser
  └─► Next.js (port 3000)
        ├─ CampusMap (react-leaflet / OpenStreetMap)
        └─► FastAPI (port 8000)
              ├─ RSS poller → UW Alerts RSS feed (5 min interval)
              ├─ NLP summarizer → GPT-4o-mini → {building, type, severity, action}
              └─ Building coords lookup → pin placement on map
```

## Figma Wireframe

*To be linked here by end of Week 7.*
