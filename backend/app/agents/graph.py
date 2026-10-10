import asyncio
import time
from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, END
from app.models.schemas import (
    RouteRequest, RouteResponse, RouteCandidate, RouteStep,
    Vehicle, VehicleType, OptimizationPriority, Stop
)
from app.services.osrm_service import OSRMService
from app.services.emissions_service import EmissionsService
from app.services.vrp_solver import VRPSolver

async def data_node(state: Dict[str, Any]) -> Dict[str, Any]:
    t0 = time.time()
    depot = state["depot"]
    stops = state["stops"]
    traffic = state.get("traffic_congestion_level", 1.25)
    weather = state.get("weather_condition", "clear")
    logs = state.setdefault("logs", [])
    agent_traces = state.setdefault("agent_traces", {})

    logs.append(f"[Data Agent] Ingested depot '{depot.name}' and {len(stops)} stops in India. Traffic: {traffic}x, Weather: {weather}.")

    all_stops = [depot] + stops
    coords = [(s.lat, s.lng) for s in all_stops]
    
    dist_matrix, time_matrix = await OSRMService.get_distance_matrix(coords)
    
    adjusted_time_matrix = [
        [round(t * traffic, 1) for t in row]
        for row in time_matrix
    ]

    state["all_stops"] = all_stops
    state["distance_matrix"] = dist_matrix
    state["time_matrix"] = adjusted_time_matrix
    
    agent_traces["data_agent"] = {
        "status": "COMPLETED",
        "duration_ms": round((time.time() - t0) * 1000, 1),
        "stops_count": len(all_stops),
        "traffic_multiplier": traffic,
        "weather_condition": weather,
        "matrix_dimension": f"{len(all_stops)}x{len(all_stops)}"
    }
    return state

async def planner_node(state: Dict[str, Any]) -> Dict[str, Any]:
    t0 = time.time()
    depot: Stop = state["depot"]
    stops: List[Stop] = state["stops"]
    all_stops: List[Stop] = state["all_stops"]
    dist_matrix = state["distance_matrix"]
    time_matrix = state["time_matrix"]
    vehicles: List[Vehicle] = state.get("vehicles") or []
    logs = state.setdefault("logs", [])
    agent_traces = state.setdefault("agent_traces", {})

    if not vehicles:
        from app.api.routes import INDIAN_VEHICLES
        vehicles = INDIAN_VEHICLES
        state["vehicles"] = vehicles

    logs.append(f"[Planner Agent] Formulating CVRPTW in Google OR-Tools. Dispatching across {len(vehicles)} vehicle candidates.")

    raw_candidates = []
    
    # Baseline Naive Route (Sequential unoptimized)
    naive_order = [0] + list(range(1, len(all_stops))) + [0]
    raw_candidates.append({
        "strategy": "BASELINE",
        "vehicle": vehicles[1] if len(vehicles) > 1 else vehicles[0],
        "order": naive_order,
        "tag": "Baseline (Unoptimized)"
    })

    # Optimized Candidates via OR-Tools
    for v in vehicles:
        weight_emiss = 1.8 if v.type == VehicleType.EV_VAN else 1.0
        weight_time = 0.8 if v.type == VehicleType.EV_VAN else 1.3

        optimized_order = VRPSolver.solve(
            depot=depot,
            stops=stops,
            vehicle=v,
            distance_matrix_km=dist_matrix,
            time_matrix_min=time_matrix,
            priority_weight_emission=weight_emiss,
            priority_weight_time=weight_time
        )

        raw_candidates.append({
            "strategy": f"OPT_{v.type.value}",
            "vehicle": v,
            "order": optimized_order,
            "tag": "Greenest Choice" if v.type == VehicleType.EV_VAN else "Fastest Delivery" if v.type == VehicleType.DIESEL_VAN else "Balanced Route"
        })

    state["raw_candidates"] = raw_candidates
    agent_traces["planner_agent"] = {
        "status": "COMPLETED",
        "duration_ms": round((time.time() - t0) * 1000, 1),
        "solver": "Google OR-Tools pywrapcp.RoutingModel",
        "constraints": ["Vehicle Capacity (CVRP)", "Service Windows", "Return-to-Depot"],
        "search_strategy": "PATH_CHEAPEST_ARC + GUIDED_LOCAL_SEARCH",
        "candidates_built": len(raw_candidates)
    }
    return state

async def emissions_node(state: Dict[str, Any]) -> Dict[str, Any]:
    t0 = time.time()
    raw_candidates = state["raw_candidates"]
    all_stops: List[Stop] = state["all_stops"]
    dist_matrix = state["distance_matrix"]
    time_matrix = state["time_matrix"]
    traffic = state.get("traffic_congestion_level", 1.25)
    weather = state.get("weather_condition", "clear")
    logs = state.setdefault("logs", [])
    agent_traces = state.setdefault("agent_traces", {})

    logs.append(f"[Emissions Agent] Executing GLEC Framework carbon accounting per segment.")

    candidate_routes: List[RouteCandidate] = []
    glec_calculations: List[Dict[str, Any]] = []

    for idx, c in enumerate(raw_candidates):
        order: List[int] = c["order"]
        vehicle: Vehicle = c["vehicle"]
        
        steps: List[RouteStep] = []
        total_dist = 0.0
        total_time = 0.0
        total_co2 = 0.0
        curr_time = 0.0
        
        current_load = sum(all_stops[i].demand for i in order if i != 0)

        for step_idx in range(len(order)):
            stop_idx = order[step_idx]
            stop = all_stops[stop_idx]

            if step_idx == 0:
                step_dist = 0.0
                step_time = 0.0
                step_co2 = 0.0
            else:
                prev_stop_idx = order[step_idx - 1]
                step_dist = dist_matrix[prev_stop_idx][stop_idx]
                step_time = time_matrix[prev_stop_idx][stop_idx]
                step_co2 = EmissionsService.calculate_segment_co2(
                    distance_km=step_dist,
                    payload_kg=current_load,
                    vehicle=vehicle,
                    traffic_congestion=traffic,
                    weather=weather
                )
                if stop_idx != 0:
                    current_load = max(0.0, current_load - stop.demand)

            total_dist += step_dist
            total_time += step_time + (stop.service_duration if step_idx > 0 and step_idx < len(order) - 1 else 0)
            total_co2 += step_co2
            curr_time += step_time

            steps.append(RouteStep(
                stop_id=stop.id,
                name=stop.name,
                lat=stop.lat,
                lng=stop.lng,
                arrival_time_min=round(curr_time, 1),
                departure_time_min=round(curr_time + (stop.service_duration if step_idx > 0 and step_idx < len(order) - 1 else 0), 1),
                distance_from_prev_km=round(step_dist, 2),
                time_from_prev_min=round(step_time, 1),
                accumulated_load_kg=round(current_load, 1),
                step_co2_kg=round(step_co2, 3)
            ))

        total_cost = EmissionsService.calculate_segment_cost(
            distance_km=total_dist,
            duration_min=total_time,
            vehicle=vehicle
        )

        ordered_coords = [(all_stops[i].lat, all_stops[i].lng) for i in order]
        geom, real_dist, real_time = await OSRMService.get_route_geometry(ordered_coords)

        candidate_routes.append(RouteCandidate(
            route_id=f"route-{idx}-{vehicle.id}",
            title=f"{c['tag']} ({vehicle.name})",
            vehicle_id=vehicle.id,
            vehicle_name=vehicle.name,
            vehicle_type=vehicle.type,
            stops_sequence=[all_stops[i].name for i in order],
            steps=steps,
            total_distance_km=round(total_dist, 2),
            total_time_min=round(total_time, 1),
            total_co2_kg=round(total_co2, 2),
            total_cost=total_cost,
            geometry=geom,
            tag=c["tag"]
        ))

    state["candidate_routes"] = candidate_routes
    agent_traces["emissions_agent"] = {
        "status": "COMPLETED",
        "duration_ms": round((time.time() - t0) * 1000, 1),
        "standard": "GLEC (Global Logistics Emissions Council) / DEFRA 2024",
        "factors_used": {
            "Tata Ace EV": "42g CO2/km (Well-to-Wheel average)",
            "Ashok Leyland Diesel": "192g CO2/km + payload slope",
            "Eicher Hybrid": "115g CO2/km"
        },
        "traffic_factor": f"{traffic}x stop-and-go idle penalty",
        "weather_factor": f"{weather} aerodynamic friction adjustment"
    }
    return state

async def decision_node(state: Dict[str, Any]) -> Dict[str, Any]:
    t0 = time.time()
    priority: OptimizationPriority = state.get("priority", OptimizationPriority.GREENEST)
    candidate_routes: List[RouteCandidate] = state["candidate_routes"]
    logs = state.setdefault("logs", [])
    agent_traces = state.setdefault("agent_traces", {})

    baseline = next((r for r in candidate_routes if "Baseline" in (r.tag or "")), candidate_routes[0])
    optimized_candidates = [r for r in candidate_routes if r.route_id != baseline.route_id]
    if not optimized_candidates:
        optimized_candidates = candidate_routes

    if priority == OptimizationPriority.GREENEST:
        best_route = min(optimized_candidates, key=lambda r: r.total_co2_kg)
    elif priority == OptimizationPriority.FASTEST:
        best_route = min(optimized_candidates, key=lambda r: r.total_time_min)
    elif priority == OptimizationPriority.CHEAPEST:
        best_route = min(optimized_candidates, key=lambda r: r.total_cost)
    else:  # BALANCED
        min_co2 = min(r.total_co2_kg for r in optimized_candidates) or 1.0
        min_time = min(r.total_time_min for r in optimized_candidates) or 1.0
        min_cost = min(r.total_cost for r in optimized_candidates) or 1.0

        def score(r: RouteCandidate) -> float:
            return 0.50 * (r.total_co2_kg / min_co2) + 0.25 * (r.total_time_min / min_time) + 0.25 * (r.total_cost / min_cost)

        best_route = min(optimized_candidates, key=score)

    co2_saved = max(0.0, baseline.total_co2_kg - best_route.total_co2_kg)
    co2_pct = round((co2_saved / baseline.total_co2_kg * 100.0), 1) if baseline.total_co2_kg > 0 else 0.0
    cost_saved = round(baseline.total_cost - best_route.total_cost, 2)

    logs.append(f"[Decision Agent] Objective: {priority.value}. Selected: '{best_route.title}'. Verified {co2_pct}% CO2 reduction vs baseline.")

    state["best_route"] = best_route
    state["baseline_route"] = baseline
    state["co2_saved_kg"] = round(co2_saved, 2)
    state["co2_saved_pct"] = co2_pct
    state["cost_saved"] = cost_saved
    
    agent_traces["decision_agent"] = {
        "status": "COMPLETED",
        "duration_ms": round((time.time() - t0) * 1000, 1),
        "selected_route": best_route.title,
        "co2_saved_pct": f"{co2_pct}%",
        "co2_saved_kg": f"{round(co2_saved, 2)} kg",
        "cost_variance": f"${cost_saved}"
    }
    return state

async def explainer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    t0 = time.time()
    best_route: RouteCandidate = state["best_route"]
    baseline: RouteCandidate = state["baseline_route"]
    priority: OptimizationPriority = state["priority"]
    co2_saved_kg = state["co2_saved_kg"]
    co2_pct = state["co2_saved_pct"]
    cost_saved = state["cost_saved"]
    logs = state.setdefault("logs", [])
    agent_traces = state.setdefault("agent_traces", {})

    time_diff_min = round(best_route.total_time_min - baseline.total_time_min, 1)
    time_str = f"{abs(time_diff_min)} min faster" if time_diff_min < 0 else f"{time_diff_min} min extra transit" if time_diff_min > 0 else "identical delivery time"

    explanation = (
        f"Selected **{best_route.title}** tailored for **{priority.value}** priority. "
        f"By re-sequencing stops via Google OR-Tools and utilizing {best_route.vehicle_name}, "
        f"this dispatch plan slashes carbon emissions by **{co2_pct}% ({co2_saved_kg} kg CO2)** "
        f"compared to the unoptimized baseline, with {time_str} and "
        f"{'$' + str(cost_saved) + ' cost reduction' if cost_saved >= 0 else '$' + str(abs(cost_saved)) + ' additional cost'}."
    )

    logs.append("[Explainer Agent] Natural language trade-off explanation formulated.")
    state["explanation"] = explanation
    
    agent_traces["explainer_agent"] = {
        "status": "COMPLETED",
        "duration_ms": round((time.time() - t0) * 1000, 1),
        "summary": "Synthesized actionable fleet dispatch trade-offs."
    }
    return state

def build_eco_route_graph():
    workflow = StateGraph(dict)

    workflow.add_node("data_agent", data_node)
    workflow.add_node("planner_agent", planner_node)
    workflow.add_node("emissions_agent", emissions_node)
    workflow.add_node("decision_agent", decision_node)
    workflow.add_node("explainer_agent", explainer_node)

    workflow.set_entry_point("data_agent")
    workflow.add_edge("data_agent", "planner_agent")
    workflow.add_edge("planner_agent", "emissions_agent")
    workflow.add_edge("emissions_agent", "decision_agent")
    workflow.add_edge("decision_agent", "explainer_agent")
    workflow.add_edge("explainer_agent", END)

    return workflow.compile()

eco_route_app = build_eco_route_graph()
