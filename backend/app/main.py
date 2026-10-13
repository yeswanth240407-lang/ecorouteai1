import os
from pathlib import Path

# Load .env without external python-dotenv dependency
_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    with open(_env_path, "r", encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as routes_router

app = FastAPI(
    title="Eco RouteAI API",
    description="Multi-agent logistics dispatch & eco-routing engine powered by OR-Tools, GLEC emissions modeling, and LangGraph.",
    version="1.0.0"
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_router, prefix="/api/routes", tags=["Routes"])

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Eco RouteAI Core",
        "version": "1.0.0"
    }

from typing import Dict, Any
from app.api.routes import plan_orchestration_endpoint, optimize_routes, RouteRequest

@app.post("/plan")
async def root_plan_endpoint(raw_body: Dict[str, Any]):
    return await plan_orchestration_endpoint(raw_body)

@app.post("/optimize")
async def root_optimize_endpoint(request: RouteRequest):
    return await optimize_routes(request)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
