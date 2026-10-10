import re
import uuid
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from app.models.schemas import Stop, Vehicle, VehicleType, OptimizationPriority, RouteRequest
from app.agents.graph import eco_route_app
from app.services.geocoding_service import IndianGeocodingService, INDIAN_HUBS_DB

class AgentChatMessage(BaseModel):
    message: str
    scenario: Dict[str, Any]
    current_priority: str = "GREENEST"
    traffic_level: float = 1.25
    weather: str = "clear"

class AgentChatResponse(BaseModel):
    agent_name: str
    agent_avatar: str
    reply: str
    thought_chain: List[Dict[str, str]]
    action_taken: str
    new_scenario: Optional[Dict[str, Any]] = None
    optimization_result: Optional[Dict[str, Any]] = None

class LogisticsAICopilot:
    """
    Autonomous AI Logistics Copilot that interprets natural language instructions,
    geocodes any Indian location, orchestrates sub-agents, and dynamically re-plans.
    """

    @classmethod
    async def process_user_prompt(cls, req: AgentChatMessage) -> AgentChatResponse:
        user_msg = req.message.lower().strip()
        scenario = dict(req.scenario)
        stops = [Stop(**s) for s in scenario.get("stops", [])]
        depot = Stop(**scenario.get("depot"))
        priority = req.current_priority
        traffic = req.traffic_level
        weather = req.weather

        thought_chain = []
        action_taken = "ANSWER_QUERY"
        reply = ""

        # Step 1: Orchestrator analyzes instruction
        thought_chain.append({
            "agent": "Orchestrator Agent",
            "avatar": "🧠",
            "thought": f"Parsing instruction: '{req.message}'. Checking Indian location ontology & geocoding index..."
        })

        # Check if the prompt references an Indian location (e.g. "ponneri", "chennai", "pune", "kochi")
        geo_result = await IndianGeocodingService.geocode_query(user_msg)

        if geo_result:
            if geo_result.get("is_known_hub"):
                # User wants to switch to or view an Indian City Hub
                hub_key = geo_result["hub_key"]
                hub = INDIAN_HUBS_DB[hub_key]
                new_depot = Stop(
                    id=f"{hub_key}-depot",
                    name=hub["depot"]["name"],
                    lat=hub["depot"]["lat"],
                    lng=hub["depot"]["lng"],
                    demand=0.0,
                    service_duration=0
                )
                new_stops = [
                    Stop(
                        id=f"{hub_key}-stop-{idx+1}",
                        name=s["name"],
                        lat=s["lat"],
                        lng=s["lng"],
                        demand=s["demand"],
                        service_duration=12
                    )
                    for idx, s in enumerate(hub["stops"])
                ]

                scenario["depot"] = new_depot.model_dump()
                scenario["stops"] = [s.model_dump() for s in new_stops]
                depot = new_depot
                stops = new_stops

                thought_chain.append({
                    "agent": "Data Agent",
                    "avatar": "📍",
                    "thought": f"Switched to Indian logistics hub: {hub['city_name']}, {hub['state']}. Coordinates: [{new_depot.lat}, {new_depot.lng}]."
                })
                action_taken = "SWITCH_HUB"
                reply = f"Switched dispatch operations to **{hub['city_name']}, {hub['state']}** with central depot at **{new_depot.name}** and {len(new_stops)} stops."

            else:
                # Add the specific Indian location (e.g. Ponneri, Ambattur, etc.)
                loc_name = geo_result["name"]
                lat = geo_result["lat"]
                lng = geo_result["lng"]
                state_name = geo_result.get("state", "India")

                # Extract demand if mentioned, else 80kg
                demand_match = re.search(r"(\d+)\s*(kg|kilos|kgs)?", user_msg)
                demand_val = float(demand_match.group(1)) if demand_match else 85.0

                new_stop = Stop(
                    id=f"stop-{uuid.uuid4().hex[:6]}",
                    name=f"{loc_name} ({state_name})",
                    lat=lat,
                    lng=lng,
                    demand=demand_val,
                    service_duration=12
                )
                stops.append(new_stop)
                scenario["stops"] = [s.model_dump() for s in stops]

                thought_chain.append({
                    "agent": "Data Agent",
                    "avatar": "📍",
                    "thought": f"Geocoded Indian location: '{loc_name}, {state_name}' at [{lat}, {lng}]. Added stop with {demand_val} kg demand."
                })
                action_taken = "ADD_STOP"
                reply = f"📍 Identified location: **{loc_name}** in **{state_name}** (`{lat:.4f}° N, {lng:.4f}° E`). Added to delivery stops with **{demand_val} kg** cargo."

        # Pattern 2: Priority changes
        elif any(w in user_msg for w in ["fast", "fastest", "speed", "quick", "rush"]):
            priority = OptimizationPriority.FASTEST.value
            thought_chain.append({
                "agent": "Decision Agent",
                "avatar": "⚡",
                "thought": "Priority shifted to FASTEST. Minimizing transit duration."
            })
            action_taken = "CHANGE_PRIORITY"
            reply = "Optimization objective updated to **FASTEST**. Route re-calculated to prioritize highways."

        elif any(w in user_msg for w in ["green", "greenest", "eco", "emission", "co2"]):
            priority = OptimizationPriority.GREENEST.value
            thought_chain.append({
                "agent": "Emissions Agent",
                "avatar": "🌿",
                "thought": "Priority shifted to GREENEST. Maximizing EV powertrain utilization."
            })
            action_taken = "CHANGE_PRIORITY"
            reply = "Optimization objective updated to **GREENEST**. Minimizing GLEC carbon emissions with commercial EVs."

        elif any(w in user_msg for w in ["rain", "storm", "monsoon"]):
            weather = "rainy"
            thought_chain.append({
                "agent": "Data Agent",
                "avatar": "🌧️",
                "thought": "Weather alert: Heavy Monsoon rains. Applying friction coefficient."
            })
            action_taken = "DISRUPTION"
            reply = "Simulated **Monsoon Rain** conditions across the route network."

        elif any(w in user_msg for w in ["traffic", "jam", "gridlock", "congestion"]):
            traffic = 1.90
            thought_chain.append({
                "agent": "Monitor Agent",
                "avatar": "🚨",
                "thought": "Peak Indian urban traffic gridlock detected (1.9x delay). Re-routing."
            })
            action_taken = "DISRUPTION"
            reply = "Simulated **Severe Traffic Gridlock** (1.9x friction factor)."

        else:
            thought_chain.append({
                "agent": "Explainer Agent",
                "avatar": "💡",
                "thought": "Processing query. Providing available Indian logistics hubs guidance."
            })
            reply = (
                f"I am Eco RouteAI. Currently managing dispatch for **{depot.name}** with **{len(stops)} stops**.\n"
                f"You can name any Indian city or town, for example:\n"
                f"• *'Ponneri'* or *'Add delivery to Ponneri 75kg'*\n"
                f"• *'Switch to Chennai'*, *'Switch to Pune'*, *'Switch to Kolkata'*\n"
                f"• *'Prioritize fastest transit'* or *'Optimize for greenest emissions'*"
            )

        # Step 2: If an action modified the network or priorities, solve with OR-Tools
        opt_result = None
        if action_taken in ["ADD_STOP", "SWITCH_HUB", "CHANGE_PRIORITY", "DISRUPTION"]:
            thought_chain.append({
                "agent": "Route Planner (OR-Tools)",
                "avatar": "⚙️",
                "thought": f"Solving CVRPTW in Google OR-Tools with {len(stops)} stops. Evaluating EV and diesel fleet permutations."
            })
            
            from app.api.routes import INDIAN_VEHICLES
            vehicles = [Vehicle(**v) for v in scenario.get("vehicles", [])] if scenario.get("vehicles") else INDIAN_VEHICLES

            state = {
                "request_id": str(uuid.uuid4()),
                "priority": OptimizationPriority(priority),
                "depot": depot,
                "stops": stops,
                "vehicles": vehicles,
                "traffic_congestion_level": traffic,
                "weather_condition": weather,
                "logs": []
            }
            
            final_state = await eco_route_app.ainvoke(state)

            thought_chain.append({
                "agent": "Emissions Agent (GLEC)",
                "avatar": "🌿",
                "thought": f"GLEC Framework verified: {final_state['co2_saved_pct']}% CO2 reduction ({final_state['co2_saved_kg']} kg saved vs baseline)."
            })

            opt_result = {
                "status": "SUCCESS",
                "priority": final_state["priority"].value,
                "best_route": final_state["best_route"].model_dump(),
                "candidate_routes": [r.model_dump() for r in final_state["candidate_routes"]],
                "baseline_route": final_state["baseline_route"].model_dump(),
                "co2_saved_kg": final_state["co2_saved_kg"],
                "co2_saved_pct": final_state["co2_saved_pct"],
                "cost_saved": final_state["cost_saved"],
                "explanation": final_state["explanation"],
                "agent_logs": final_state.get("logs", []),
                "agent_traces": final_state.get("agent_traces", {})
            }

            reply += f"\n\n**Updated Dispatch**: Selected **{final_state['best_route'].title}** with **{final_state['co2_saved_pct']}% CO2 reduction** ({final_state['co2_saved_kg']} kg CO2 saved)."

        return AgentChatResponse(
            agent_name="Eco RouteAI Autonomous Dispatcher",
            agent_avatar="🤖",
            reply=reply,
            thought_chain=thought_chain,
            action_taken=action_taken,
            new_scenario=scenario if action_taken in ["ADD_STOP", "SWITCH_HUB"] else None,
            optimization_result=opt_result
        )
