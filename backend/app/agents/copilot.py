import re
import uuid
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from app.models.schemas import Stop, Vehicle, VehicleType, OptimizationPriority, RouteRequest
from app.agents.graph import eco_route_app
from app.services.geocoding_service import IndianGeocodingService, INDIAN_HUBS_DB
from app.services.gemini_service import GeminiService

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
            associated_hub = geo_result.get("associated_hub")
            is_hub = geo_result.get("is_known_hub", False)

            # Check if this requires switching hub (explicit switch or location in another city)
            current_hub_name = depot.name.lower()
            needs_hub_switch = is_hub or (
                associated_hub and associated_hub in INDIAN_HUBS_DB and
                associated_hub not in current_hub_name and
                INDIAN_HUBS_DB[associated_hub]["city_name"].lower() not in current_hub_name
            )

            if is_hub or needs_hub_switch:
                hub_key = geo_result.get("hub_key") or associated_hub
                demand_match = re.search(r"(\d+)\s*(kg|kilos|kgs)?", user_msg)
                demand_val = float(demand_match.group(1)) if demand_match else 50.0

                if hub_key and hub_key in INDIAN_HUBS_DB:
                    hub = INDIAN_HUBS_DB[hub_key]
                    new_depot = Stop(
                        id=f"{hub_key}-depot",
                        name=hub["depot"]["name"],
                        lat=hub["depot"]["lat"],
                        lng=hub["depot"]["lng"],
                        demand=0.0,
                        service_duration=0
                    )
                    new_stops = []
                    target_added = False
                    for idx, s in enumerate(hub["stops"]):
                        is_target = geo_result["name"].lower() in s["name"].lower()
                        stop_demand = demand_val if is_target else s["demand"]
                        if is_target:
                            target_added = True
                        new_stops.append(Stop(
                            id=f"{hub_key}-stop-{idx+1}",
                            name=s["name"],
                            lat=s["lat"],
                            lng=s["lng"],
                            demand=stop_demand,
                            service_duration=12
                        ))

                    if not target_added and not is_hub:
                        new_stops.append(Stop(
                            id=f"stop-{uuid.uuid4().hex[:6]}",
                            name=f"{geo_result['name']} ({geo_result.get('state', 'India')})",
                            lat=geo_result["lat"],
                            lng=geo_result["lng"],
                            demand=demand_val,
                            service_duration=12
                        ))

                    loc_display = hub['city_name']
                    state_display = hub['state']

                else:
                    # Dynamically create regional dispatch hub for this newly requested Indian town/city
                    loc_display = geo_result['name']
                    state_display = geo_result.get('state', 'India')
                    lat = geo_result['lat']
                    lng = geo_result['lng']

                    new_depot = Stop(
                        id=f"depot-{uuid.uuid4().hex[:6]}",
                        name=f"{loc_display} Logistics Hub",
                        lat=lat,
                        lng=lng,
                        demand=0.0,
                        service_duration=0
                    )
                    new_stops = [
                        Stop(
                            id=f"stop-{uuid.uuid4().hex[:6]}",
                            name=f"{loc_display} Commercial Zone",
                            lat=lat + 0.016,
                            lng=lng + 0.018,
                            demand=demand_val,
                            service_duration=12
                        ),
                        Stop(
                            id=f"stop-{uuid.uuid4().hex[:6]}",
                            name=f"{loc_display} Industrial Estate",
                            lat=lat - 0.022,
                            lng=lng + 0.014,
                            demand=demand_val * 1.25,
                            service_duration=14
                        ),
                        Stop(
                            id=f"stop-{uuid.uuid4().hex[:6]}",
                            name=f"{loc_display} Freight Station",
                            lat=lat + 0.012,
                            lng=lng - 0.024,
                            demand=demand_val * 0.8,
                            service_duration=10
                        ),
                        Stop(
                            id=f"stop-{uuid.uuid4().hex[:6]}",
                            name=f"{loc_display} Retail Corridor",
                            lat=lat - 0.014,
                            lng=lng - 0.016,
                            demand=demand_val * 0.95,
                            service_duration=12
                        )
                    ]

                scenario["depot"] = new_depot.model_dump()
                scenario["stops"] = [s.model_dump() for s in new_stops]
                depot = new_depot
                stops = new_stops

                thought_chain.append({
                    "agent": "Data Agent",
                    "avatar": "📍",
                    "thought": f"Shifted operations to {loc_display} Hub: {new_depot.name} at [{new_depot.lat:.4f}, {new_depot.lng:.4f}]. Configured {len(new_stops)} stops."
                })
                action_taken = "SWITCH_HUB"
                reply = f"Switched dispatch operations to **{loc_display}, {state_display}** with central depot at **{new_depot.name}** and {len(new_stops)} delivery stops."

            else:
                loc_name = geo_result["name"]
                lat = geo_result["lat"]
                lng = geo_result["lng"]
                state_name = geo_result.get("state", "India")

                demand_match = re.search(r"(\d+)\s*(kg|kilos|kgs)?", user_msg)
                demand_val = float(demand_match.group(1)) if demand_match else 75.0

                # Check if this location is far away from current depot (> 2.0 degrees, ~220km)
                # If so, create a dedicated regional dispatch network centered on this new location!
                dist_degrees = ((lat - depot.lat) ** 2 + (lng - depot.lng) ** 2) ** 0.5
                if dist_degrees > 2.0:
                    new_depot = Stop(
                        id=f"depot-{uuid.uuid4().hex[:6]}",
                        name=f"{loc_name} Regional Logistics Hub",
                        lat=lat,
                        lng=lng,
                        demand=0.0,
                        service_duration=0
                    )
                    # Generate realistic intra-city delivery clusters around the new location
                    new_stops = [
                        Stop(
                            id=f"stop-{uuid.uuid4().hex[:6]}",
                            name=f"{loc_name} Commercial Center",
                            lat=lat + 0.018,
                            lng=lng + 0.022,
                            demand=demand_val,
                            service_duration=12
                        ),
                        Stop(
                            id=f"stop-{uuid.uuid4().hex[:6]}",
                            name=f"{loc_name} Industrial Corridor",
                            lat=lat - 0.024,
                            lng=lng + 0.015,
                            demand=demand_val * 1.2,
                            service_duration=14
                        ),
                        Stop(
                            id=f"stop-{uuid.uuid4().hex[:6]}",
                            name=f"{loc_name} Freight Terminal",
                            lat=lat + 0.012,
                            lng=lng - 0.025,
                            demand=demand_val * 0.8,
                            service_duration=10
                        ),
                        Stop(
                            id=f"stop-{uuid.uuid4().hex[:6]}",
                            name=f"{loc_name} Retail Square",
                            lat=lat - 0.015,
                            lng=lng - 0.018,
                            demand=demand_val * 0.9,
                            service_duration=12
                        )
                    ]
                    scenario["depot"] = new_depot.model_dump()
                    scenario["stops"] = [s.model_dump() for s in new_stops]
                    depot = new_depot
                    stops = new_stops

                    thought_chain.append({
                        "agent": "Data Agent",
                        "avatar": "📍",
                        "thought": f"Detected distinct Indian destination: '{loc_name}, {state_name}' at [{lat:.4f}, {lng:.4f}]. Shifted central depot & generated local delivery cluster."
                    })
                    action_taken = "SWITCH_HUB"
                    reply = f"📍 Relocated logistics dispatch to **{loc_name}, {state_name}** (`{lat:.4f}° N, {lng:.4f}° E`). Established central depot at **{new_depot.name}** and generated 4 regional delivery stops with **{demand_val} kg** priority cargo."

                else:
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
                        "thought": f"Geocoded Indian location: '{loc_name}, {state_name}' at [{lat:.4f}, {lng:.4f}]. Added stop with {demand_val} kg demand."
                    })
                    action_taken = "ADD_STOP"
                    reply = f"📍 Identified location: **{loc_name}** in **{state_name}** (`{lat:.4f}° N, {lng:.4f}° E`). Added to delivery stops with **{demand_val} kg** cargo."

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

        elif any(w in user_msg for w in ["green", "greenest", "eco"]) and any(w in user_msg for w in ["optimize", "prioritize", "priority", "switch"]):
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

        elif any(w in user_msg for w in ["traffic", "jam", "gridlock", "congestion", "silk board"]):
            traffic = 1.95
            thought_chain.append({
                "agent": "Monitor Agent",
                "avatar": "🚨",
                "thought": "Peak Indian urban traffic gridlock detected (1.95x delay). Re-routing."
            })
            action_taken = "DISRUPTION"
            reply = "Simulated **Severe Traffic Gridlock** (1.95x friction factor). Re-optimizing road sequence."

        else:
            thought_chain.append({
                "agent": "Gemini AI Agent",
                "avatar": "✨",
                "thought": f"Consulting Google Gemini AI to analyze dispatch query: '{req.message}'"
            })
            gemini_ans = await GeminiService.answer_general_query(req.message, depot.name, len(stops))
            if gemini_ans:
                reply = gemini_ans
            else:
                reply = (
                    f"I am Eco RouteAI powered by Google Gemini. Currently managing dispatch for **{depot.name}** with **{len(stops)} stops**.\n"
                    f"You can name any Indian city or town, for example:\n"
                    f"• *'Ponneri'* or *'Add delivery to Ponneri 75kg'*\n"
                    f"• *'Add urgent delivery to Indiranagar (50 kg)'*\n"
                    f"• *'Switch to Chennai'*, *'Switch to Bengaluru'*, *'Switch to Mumbai'*\n"
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

            # Update scenario properties
            scenario["priority"] = priority
            scenario["traffic_congestion_level"] = traffic
            scenario["weather_condition"] = weather

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
            new_scenario=scenario if action_taken in ["ADD_STOP", "SWITCH_HUB", "CHANGE_PRIORITY", "DISRUPTION"] else None,
            optimization_result=opt_result
        )
