# Eco RouteAI 🌿🚛

**Autonomous Multi-Agent Green Logistics & Route Optimization Platform**

Eco RouteAI optimizes delivery fleets for minimum $\text{CO}_2$ emissions, operational cost, and delivery deadlines. Powered by **Google OR-Tools** (VRPTW), **GLEC Framework** carbon accounting, and a **LangGraph** multi-agent decision loop.

---

## Architecture

```
User Request / UI
       │
       ▼
[Orchestrator Agent]
       │
       ▼
[Data Agent] ───────────► OSRM Routing & Distance/Duration Matrices
       │
       ▼
[Planner Agent] ────────► Google OR-Tools (CVRPTW Optimization)
       │
       ▼
[Emissions Agent] ──────► GLEC Carbon Factors & Traffic/Weather Penalties
       │
       ▼
[Decision Agent] ───────► Multi-Objective Pareto Frontier Evaluation
       │
       ▼
[Explainer Agent] ──────► Natural Language Trade-off Justification
       │
       ▼
[FastAPI / Next.js UI]
       ▲
       │
[Monitor Agent] ────────► Live Traffic/Weather Events & Dynamic Re-routing
```

---

## Features
- **Deterministic Math + Multi-Agent Reasoning**: Real mathematical optimization via Google OR-Tools coupled with LangGraph coordination.
- **GLEC Framework Emissions Engine**: Segment-by-segment calculation factoring vehicle curb weight, real payload decay, stop-and-go idle friction, and weather resistance.
- **Real Road Polylines**: Integrates with OSRM (Open Source Routing Machine) with resilient offline Haversine 2-opt fallbacks.
- **Interactive Next.js Dashboard**: Leaflet map displaying Depot, numbered delivery stops, polyline routes, side-by-side trade-off cards, and live agent execution traces.
- **Dynamic Disruption Simulator**: One-click simulation of traffic spikes or severe weather that re-evaluates dispatch plans on the fly.

---

## Quickstart

### 1. Backend (FastAPI + LangGraph + OR-Tools)
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
The API documentation is accessible at `http://localhost:8000/docs`.

### 2. Frontend (Next.js + Leaflet + Tailwind CSS)
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your browser.
