# UW Bothell Campus Pulse

[![Live Demo](https://img.shields.io/badge/Live%20Demo-css382--dyop.vercel.app-blue)](https://css382-dyop.vercel.app)

Real-time interactive map of UW Bothell displaying campus events and emergency alerts.
Built with Next.js, FastAPI, OpenStreetMap (Leaflet), and GPT-4o-mini.

## Live Demo

**Frontend:** https://css382-dyop.vercel.app  
**Backend API:** https://css382-dyop.onrender.com

## Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 14 + TypeScript + react-leaflet |
| Map | OpenStreetMap via Leaflet |
| Backend | FastAPI + Python 3.11 |
| AI | GPT-4o-mini (NLP alert summarizer) |
| Recommender | scikit-surprise SVD (collaborative filtering) |
| Database | PostgreSQL / Supabase |
| Auth | Auth0 |
| Deployment | Vercel (frontend) + Render (backend) |

## Milestone Status

| Milestone | Status | Criteria |
|---|---|---|
| Week 7 | ✅ | Map renders UW Bothell; test pin at UW1 |
| Week 8 (MVP) | ✅ | RSS feed + NLP summarizer + fallback banner |
| Week 9 (Testing) | ✅ | Event recommender + Supabase + Auth0 + project website |
| Week 10 (Final) | ✅ | Public deploy on Vercel + Render |

## Quick Start

### Backend

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pip install "numpy<2"

cp ../.env.example .env
# Edit .env and add OPENAI_API_KEY, SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY

uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local: set NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev         # opens http://localhost:3000
```

### NLP Test Suite

```bash
cd backend
source venv/bin/activate
python test_nlp_summarizer.py
# Must show ≥90% (18/20) valid JSON responses
```

## Architecture

```
Browser
  └─► Next.js on Vercel (css382-dyop.vercel.app)
        ├─ CampusMap (react-leaflet / OpenStreetMap)
        ├─ For You panel (SVD recommender)
        └─► FastAPI on Render (css382-dyop.onrender.com)
              ├─ RSS poller → UW Alerts RSS feed (5 min interval)
              ├─ NLP summarizer → GPT-4o-mini → {building, type, severity, action}
              ├─ Building coords lookup → pin placement on map
              └─ Supabase → interaction logging + recommendations
```
