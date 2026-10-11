import uuid
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from app.models.schemas import RouteRequest, RouteResponse, Stop, Vehicle, VehicleType, OptimizationPriority
from app.agents.graph import eco_route_app
from app.agents.advisory_agent import run_advisory_agent
from app.services.geocoding_service import INDIAN_HUBS_DB, IndianGeocodingService

router = APIRouter()

INDIAN_VEHICLES: List[Vehicle] = [
    Vehicle(
        id="v-tata-ev",
        name="Tata Ace EV Cargo",
        type=VehicleType.EV_VAN,
        capacity=1000.0,
        fuel_type="Electric",
        base_cost_per_km=0.45,
        hourly_rate=18.0,
        co2_factor_empty=42.0,
        co2_factor_loaded_delta=0.02
    ),
    Vehicle(
        id="v-diesel-leyland",
        name="Ashok Leyland Dost (Diesel)",
        type=VehicleType.DIESEL_VAN,
        capacity=1500.0,
        fuel_type="Diesel",
        base_cost_per_km=1.15,
        hourly_rate=22.0,
        co2_factor_empty=192.0,
        co2_factor_loaded_delta=0.06
    ),
    Vehicle(
        id="v-eicher-hybrid",
        name="Eicher Pro Hybrid Van",
        type=VehicleType.HYBRID_VAN,
        capacity=1200.0,
        fuel_type="Hybrid",
        base_cost_per_km=0.85,
        hourly_rate=20.0,
        co2_factor_empty=115.0,
        co2_factor_loaded_delta=0.038
    )
]

@router.get("/cities")
async def get_available_cities():
    """Lists all available Indian states & logistics hubs."""
    return [
        {
            "id": key,
            "name": val["city_name"],
            "state": val["state"],
            "depot_name": val["depot"]["name"],
            "stops_count": len(val["stops"])
        }
        for key, val in INDIAN_HUBS_DB.items()
    ]

@router.get("/sample", response_model=RouteRequest)
async def get_sample_scenario(city: str = Query(default="chennai")):
    """Returns an Indian logistics scenario for any state or city."""
    city_key = city.lower()
    if city_key not in INDIAN_HUBS_DB:
        city_key = "chennai" if "ponneri" in city_key or "tamil" in city_key else "bengaluru"

    hub = INDIAN_HUBS_DB[city_key]

    depot = Stop(
        id=f"{city_key}-depot",
        name=hub["depot"]["name"],
        lat=hub["depot"]["lat"],
        lng=hub["depot"]["lng"],
        demand=0.0,
        service_duration=0
    )

    stops = [
        Stop(
            id=f"{city_key}-stop-{idx+1}",
            name=s["name"],
            lat=s["lat"],
            lng=s["lng"],
            demand=s["demand"],
            service_duration=12
        )
        for idx, s in enumerate(hub["stops"])
    ]

    return RouteRequest(
        priority=OptimizationPriority.GREENEST,
        depot=depot,
        stops=stops,
        vehicles=INDIAN_VEHICLES,
        traffic_congestion_level=1.25,
        weather_condition="clear"
    )

@router.get("/geocode")
async def geocode_indian_location(q: str = Query(...)):
    """Geocodes any town, village, or industrial hub across India."""
    result = await IndianGeocodingService.geocode_query(q)
    if not result:
        raise HTTPException(status_code=404, detail=f"Location '{q}' not found in India.")
    return result

@router.post("/optimize", response_model=RouteResponse)
async def optimize_routes(request: RouteRequest):
    """
    Executes the LangGraph Multi-Agent Engine:
    Data -> Planner (OR-Tools) -> Emissions (GLEC) -> Decision -> Explainer.
    """
    try:
        initial_state = {
            "request_id": str(uuid.uuid4()),
            "priority": request.priority,
            "depot": request.depot,
            "stops": request.stops,
            "vehicles": request.vehicles or INDIAN_VEHICLES,
            "traffic_congestion_level": request.traffic_congestion_level,
            "weather_condition": request.weather_condition,
            "logs": []
        }

        final_state = await eco_route_app.ainvoke(initial_state)

        return RouteResponse(
            status="SUCCESS",
            priority=final_state["priority"],
            best_route=final_state["best_route"],
            candidate_routes=final_state["candidate_routes"],
            baseline_route=final_state["baseline_route"],
            co2_saved_kg=final_state["co2_saved_kg"],
            co2_saved_pct=final_state["co2_saved_pct"],
            cost_saved=final_state["cost_saved"],
            explanation=final_state["explanation"],
            agent_logs=final_state.get("logs", []),
            agent_traces=final_state.get("agent_traces", {})
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Routing optimization failed: {str(e)}")

@router.post("/simulate-disruption", response_model=RouteResponse)
async def simulate_disruption(request: RouteRequest):
    updated_request = request.model_copy(update={
        "traffic_congestion_level": min(2.0, request.traffic_congestion_level + 0.45),
        "weather_condition": "rainy"
    })
    return await optimize_routes(updated_request)

from app.agents.copilot import LogisticsAICopilot, AgentChatMessage, AgentChatResponse

@router.post("/agent-chat", response_model=AgentChatResponse)
async def chat_with_agent(message_req: AgentChatMessage):
    return await LogisticsAICopilot.process_user_prompt(message_req)

@router.post("/plan")
async def plan_orchestration_endpoint(raw_body: Dict[str, Any]):
    """
    Unified Eco Route Agent Plan endpoint supporting LangGraph Multi-Agent,
    Google OR-Tools CVRPTW Solver, and GLEC Framework Carbon Accounting.
    """
    try:
        # Check if raw_body is a RouteRequest or legacy format
        depot_data = raw_body.get("depot")
        if isinstance(depot_data, dict):
            loc = depot_data.get("location") if isinstance(depot_data.get("location"), dict) else depot_data
            depot = Stop(
                id=str(depot_data.get("id", "depot-0")),
                name=str(depot_data.get("name", loc.get("name", "Central Logistics Depot"))),
                lat=float(loc.get("lat", 13.0827)),
                lng=float(loc.get("lng", 80.2707)),
                demand=0.0,
                service_duration=0
            )
        else:
            depot = Stop(id="depot-0", name="Central Depot", lat=13.0827, lng=80.2707, demand=0.0)

        stops_data = raw_body.get("stops", [])
        parsed_stops = []
        for idx, s in enumerate(stops_data):
            if isinstance(s, dict):
                loc = s.get("location") if isinstance(s.get("location"), dict) else s
                parsed_stops.append(Stop(
                    id=str(s.get("id", f"stop-{idx+1}")),
                    name=str(s.get("name", loc.get("name", f"Stop {idx+1}"))),
                    lat=float(loc.get("lat", 13.0827 + (idx + 1) * 0.05)),
                    lng=float(loc.get("lng", 80.2707 + (idx + 1) * 0.03)),
                    demand=float(s.get("demand", 25.0)),
                    service_duration=int(s.get("service_duration", 10))
                ))

        vehicles_data = raw_body.get("vehicles")
        if not vehicles_data:
            vehicles = INDIAN_VEHICLES
        else:
            vehicles = INDIAN_VEHICLES

        priority_str = raw_body.get("priority", "GREENEST")
        try:
            priority = OptimizationPriority(priority_str)
        except Exception:
            priority = OptimizationPriority.GREENEST

        traffic = float(raw_body.get("traffic_congestion_level", raw_body.get("speed_kmh", 1.25)))
        if traffic > 10.0:  # If passed speed_kmh like 40.0
            traffic = 1.25

        weather = str(raw_body.get("weather_condition", "clear"))

        initial_state = {
            "request_id": str(uuid.uuid4()),
            "priority": priority,
            "depot": depot,
            "stops": parsed_stops if parsed_stops else [
                Stop(id="s1", name="Stop 1", lat=depot.lat + 0.03, lng=depot.lng + 0.02, demand=20.0),
                Stop(id="s2", name="Stop 2", lat=depot.lat - 0.02, lng=depot.lng + 0.04, demand=35.0),
            ],
            "vehicles": vehicles,
            "traffic_congestion_level": traffic,
            "weather_condition": weather,
            "logs": []
        }

        final_state = await eco_route_app.ainvoke(initial_state)

        best_route_dict = final_state["best_route"].model_dump() if hasattr(final_state["best_route"], "model_dump") else final_state["best_route"]
        candidate_routes_dict = [r.model_dump() if hasattr(r, "model_dump") else r for r in final_state.get("candidate_routes", [])]
        baseline_route_dict = final_state["baseline_route"].model_dump() if hasattr(final_state["baseline_route"], "model_dump") else final_state["baseline_route"]

        return {
            "status": "SUCCESS",
            "priority": final_state["priority"].value if hasattr(final_state["priority"], "value") else str(final_state["priority"]),
            "best_route": best_route_dict,
            "routes": candidate_routes_dict,
            "candidate_routes": candidate_routes_dict,
            "baseline_route": baseline_route_dict,
            "co2_saved_kg": final_state["co2_saved_kg"],
            "co2_saved_pct": final_state["co2_saved_pct"],
            "cost_saved": final_state["cost_saved"],
            "explanation": final_state["explanation"],
            "logs": final_state.get("logs", []),
            "agent_logs": final_state.get("logs", []),
            "agent_traces": final_state.get("agent_traces", {}),
            "eco_scores": {
                "saved_co2_kg": final_state["co2_saved_kg"],
                "saved_percentage": final_state["co2_saved_pct"],
                "cost_variance": final_state["cost_saved"],
                "standard": "GLEC Framework v3 / DEFRA 2024"
            },
            "report": {
                "status": "COMPLETED",
                "best_vehicle": getattr(final_state["best_route"], "vehicle_name", "Tata Ace EV Cargo"),
                "co2_reduction": f"{final_state['co2_saved_pct']}%",
                "explanation": final_state["explanation"],
                "metrics": {
                    "total_distance_km": best_route_dict.get("total_distance_km", 0.0),
                    "total_time_min": best_route_dict.get("total_time_min", 0.0),
                    "total_co2_kg": best_route_dict.get("total_co2_kg", 0.0)
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent Plan execution failed: {str(e)}")


# ─────────────────────────────────────────────────────────────────────────────
# Predictive Risk & Advisory Agent Endpoint
# ─────────────────────────────────────────────────────────────────────────────

class AdvisoryRequest(RouteRequest.__class__.__bases__[0]):
    scenario: Dict[str, Any]
    optimization_result: Optional[Dict[str, Any]] = None

from pydantic import BaseModel

class AdvisoryRequestBody(BaseModel):
    scenario: Dict[str, Any]
    optimization_result: Optional[Dict[str, Any]] = None

@router.post("/advisory")
async def advisory_agent_endpoint(body: AdvisoryRequestBody):
    """
    Predictive Risk & Advisory Agent — analyses current delivery scenario and
    returns smart alerts, recommendations, and carbon credit forecasts.
    """
    try:
        result = run_advisory_agent(
            scenario=body.scenario,
            optimization_result=body.optimization_result,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Advisory Agent failed: {str(e)}")
