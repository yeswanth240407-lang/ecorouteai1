"""
Predictive Risk & Advisory Agent — EcoRoute AI
================================================
A standalone AI agent that analyses the current delivery scenario and generates
proactive smart recommendations covering:
  • Weather & traffic risk alerts
  • Cargo load balancing suggestions
  • Carbon credit opportunity forecasting
  • Fleet health advisories
  • Time-window breach predictions
"""

import math
import random
import time
from typing import Any, Dict, List


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance between two points (km)."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


WEATHER_RISK = {
    "clear":       {"level": "LOW",    "emoji": "☀️",  "penalty": 0.0},
    "rain":        {"level": "MEDIUM", "emoji": "🌧️",  "penalty": 0.18},
    "heavy_rain":  {"level": "HIGH",   "emoji": "⛈️",  "penalty": 0.35},
    "fog":         {"level": "MEDIUM", "emoji": "🌫️",  "penalty": 0.22},
    "storm":       {"level": "CRITICAL","emoji": "🌪️", "penalty": 0.55},
    "flood":       {"level": "CRITICAL","emoji": "🌊",  "penalty": 0.70},
    "snow":        {"level": "HIGH",   "emoji": "❄️",  "penalty": 0.40},
}

TRAFFIC_THRESHOLDS = {
    (0.0, 1.1):  ("LOW",      "🟢", "Traffic is light — ideal dispatch window."),
    (1.1, 1.5):  ("MODERATE", "🟡", "Moderate congestion detected. Allow +15 min buffer."),
    (1.5, 2.0):  ("HIGH",     "🟠", "Heavy traffic. Consider off-peak departure at 06:00."),
    (2.0, 9.9):  ("SEVERE",   "🔴", "Severe gridlock. Re-route via ring roads recommended."),
}


def _traffic_info(level: float):
    for (lo, hi), (label, color, msg) in TRAFFIC_THRESHOLDS.items():
        if lo <= level < hi:
            return label, color, msg
    return "UNKNOWN", "⚪", "Traffic data unavailable."


# ─────────────────────────────────────────────────────────────────────────────
# Main agent entry-point
# ─────────────────────────────────────────────────────────────────────────────

def run_advisory_agent(scenario: Dict[str, Any], optimization_result: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    Analyse the given scenario + optional optimization result and return
    a structured advisory payload.
    """
    t0 = time.time()

    depot = scenario.get("depot", {})
    stops: List[Dict] = scenario.get("stops", [])
    traffic: float = float(scenario.get("traffic_congestion_level", 1.25))
    weather: str = scenario.get("weather_condition", "clear").lower()
    vehicles: List[Dict] = scenario.get("vehicles", [])

    alerts: List[Dict] = []
    recommendations: List[Dict] = []
    carbon_forecast: Dict = {}
    risk_score: int = 0  # 0–100

    # ── 1. Weather Risk Analysis ─────────────────────────────────────────────
    w = WEATHER_RISK.get(weather, WEATHER_RISK["clear"])
    weather_risk_pct = int(w["penalty"] * 100)
    risk_score += int(w["penalty"] * 40)

    if w["level"] in ("HIGH", "CRITICAL"):
        alerts.append({
            "id": "WEATHER_ALERT",
            "severity": w["level"],
            "icon": w["emoji"],
            "title": f"{w['level']} Weather Alert — {weather.replace('_', ' ').title()}",
            "message": f"Current weather adds ~{weather_risk_pct}% delivery time penalty. "
                       f"Consider delaying perishable cargo or switching to covered EV vans.",
            "action": "Switch vehicle type to enclosed EV cargo van",
        })
    elif w["level"] == "MEDIUM":
        alerts.append({
            "id": "WEATHER_CAUTION",
            "severity": "MEDIUM",
            "icon": w["emoji"],
            "title": f"Weather Caution — {weather.replace('_', ' ').title()}",
            "message": f"Moderate conditions add ~{weather_risk_pct}% transit time. Drivers should maintain reduced speed.",
            "action": "Add 15 min buffer to all delivery windows",
        })

    # ── 2. Traffic Risk Analysis ─────────────────────────────────────────────
    t_label, t_color, t_msg = _traffic_info(traffic)
    risk_score += int((traffic - 1.0) * 20)

    if traffic >= 1.5:
        alerts.append({
            "id": "TRAFFIC_ALERT",
            "severity": "HIGH" if traffic < 2.0 else "CRITICAL",
            "icon": t_color,
            "title": f"{t_label} Traffic Congestion ({traffic}x)",
            "message": t_msg,
            "action": "Optimise departure to off-peak hours (06:00–08:00 or 20:00–22:00)",
        })

    # ── 3. Stop Density & Load Balancing ────────────────────────────────────
    if stops:
        total_demand = sum(s.get("demand", 0) for s in stops)
        avg_demand = total_demand / len(stops) if stops else 0
        max_stop = max(stops, key=lambda s: s.get("demand", 0))
        max_demand = max_stop.get("demand", 0)
        imbalance_pct = int(((max_demand - avg_demand) / avg_demand * 100)) if avg_demand > 0 else 0

        if imbalance_pct > 60:
            risk_score += 10
            recommendations.append({
                "id": "LOAD_BALANCE",
                "icon": "⚖️",
                "priority": "HIGH",
                "title": "Cargo Load Imbalance Detected",
                "detail": f"Stop '{max_stop.get('name', 'Unknown')}' carries {max_demand:.0f} kg — "
                          f"{imbalance_pct}% above average. Split into two sub-deliveries to avoid vehicle overload.",
                "impact": f"Reduces per-vehicle CO₂ by ~{min(imbalance_pct // 3, 25)}%",
            })

        # Cluster stops by proximity
        if len(stops) >= 3:
            far_stops = []
            depot_lat = depot.get("lat", 0)
            depot_lng = depot.get("lng", 0)
            for s in stops:
                d = _haversine_km(depot_lat, depot_lng, s.get("lat", 0), s.get("lng", 0))
                if d > 25:
                    far_stops.append((s.get("name", "Unknown"), round(d, 1)))

            if far_stops:
                risk_score += 8
                far_names = ", ".join(f[0] for f in far_stops[:3])
                recommendations.append({
                    "id": "CLUSTER_ROUTE",
                    "icon": "🗺️",
                    "priority": "MEDIUM",
                    "title": "Long-Haul Stops Detected",
                    "detail": f"{len(far_stops)} stop(s) are >25 km from depot: {far_names}. "
                              f"Use a dedicated intercity EV truck for these to cut dead-mileage emissions.",
                    "impact": "Saves ~12–20% total fleet CO₂ by trip batching",
                })

    # ── 4. Carbon Credit Opportunity ─────────────────────────────────────────
    ev_count = sum(1 for v in vehicles if "ev" in str(v.get("type", "")).lower())
    diesel_count = len(vehicles) - ev_count

    if optimization_result:
        best = optimization_result.get("best_route", {})
        baseline = optimization_result.get("baseline_route", {})
        co2_saved = max(0, baseline.get("total_co2_kg", 0) - best.get("total_co2_kg", 0))

        # India carbon credit: ~₹1,200 per tonne CO₂ (CCTS 2024 est.)
        credits_inr = round((co2_saved / 1000) * 1200, 2)
        monthly_est = round(credits_inr * 22, 2)  # ~22 working days

        carbon_forecast = {
            "co2_saved_today_kg": round(co2_saved, 2),
            "carbon_credits_inr": credits_inr,
            "monthly_projection_inr": monthly_est,
            "annual_projection_inr": round(monthly_est * 12, 2),
            "ev_vehicles_used": ev_count,
            "diesel_vehicles_replaced": diesel_count,
            "standard": "India CCTS (Carbon Credit Trading Scheme) 2024",
            "message": (
                f"Today's EV dispatch saves **{co2_saved:.2f} kg CO₂**, worth "
                f"**₹{credits_inr:.2f} in carbon credits**. "
                f"At this rate, your fleet earns **₹{monthly_est:,.0f}/month** "
                f"under India's CCTS scheme."
            ) if co2_saved > 0 else "Run route optimization to calculate carbon credit earnings.",
        }

        if co2_saved > 5:
            recommendations.append({
                "id": "CARBON_CREDIT",
                "icon": "🌱",
                "priority": "HIGH",
                "title": "Carbon Credit Opportunity",
                "detail": f"Switching to EV dispatch saves {co2_saved:.2f} kg CO₂ today (~₹{credits_inr:.2f}). "
                          f"Register under India CCTS to monetise these savings.",
                "impact": f"₹{monthly_est:,.0f}/month projected carbon revenue",
            })
    else:
        carbon_forecast = {
            "message": "Optimize a route first to see your carbon credit earnings.",
            "standard": "India CCTS 2024",
        }

    # ── 5. EV Fleet Transition Advisory ─────────────────────────────────────
    if diesel_count > 0 and ev_count == 0:
        risk_score += 15
        recommendations.append({
            "id": "EV_TRANSITION",
            "icon": "⚡",
            "priority": "MEDIUM",
            "title": "Fleet Electrification Opportunity",
            "detail": f"Your current fleet uses {diesel_count} diesel vehicle(s). "
                      f"Replacing with Tata Ace EV or Mahindra Treo Zor cuts per-km emissions by ~78%.",
            "impact": "Avg ₹3.2/km fuel savings + carbon credit eligibility",
        })

    # ── 6. Time Window Breach Prediction ─────────────────────────────────────
    if stops and traffic > 1.3 and len(stops) > 4:
        breach_count = max(1, int(len(stops) * (traffic - 1.0) * 0.4))
        risk_score += breach_count * 5
        alerts.append({
            "id": "TIME_WINDOW_RISK",
            "severity": "MEDIUM",
            "icon": "⏰",
            "title": f"Delivery Window Breach Risk",
            "message": f"With {traffic}x traffic, ~{breach_count} stop(s) may miss their delivery windows. "
                       f"AI recommends dispatching 40 min earlier or enabling dynamic re-sequencing.",
            "action": "Enable dynamic re-sequencing in dispatch settings",
        })

    # ── 7. Overall Risk Score ─────────────────────────────────────────────────
    risk_score = min(risk_score, 100)
    if risk_score < 25:
        risk_label, risk_color = "LOW RISK", "🟢"
    elif risk_score < 55:
        risk_label, risk_color = "MODERATE RISK", "🟡"
    elif risk_score < 80:
        risk_label, risk_color = "HIGH RISK", "🟠"
    else:
        risk_label, risk_color = "CRITICAL RISK", "🔴"

    # ── Agent thought chain ───────────────────────────────────────────────────
    thought_chain = [
        {
            "agent": "Advisory Agent",
            "avatar": "🧭",
            "thought": f"Scanning {len(stops)} delivery stops across {depot.get('name', 'depot')} corridor.",
        },
        {
            "agent": "Advisory Agent",
            "avatar": "🌦️",
            "thought": f"Weather: {weather} ({w['level']} risk, +{weather_risk_pct}% penalty). "
                       f"Traffic: {traffic}x ({t_label}). Combined risk score: {risk_score}/100.",
        },
        {
            "agent": "Advisory Agent",
            "avatar": "🌱",
            "thought": f"Carbon analysis complete. {len(recommendations)} optimisation opportunities identified.",
        },
    ]

    duration_ms = round((time.time() - t0) * 1000, 1)

    return {
        "agent_name": "Predictive Risk & Advisory Agent",
        "agent_avatar": "🧭",
        "risk_score": risk_score,
        "risk_label": risk_label,
        "risk_color": risk_color,
        "alerts": alerts,
        "recommendations": recommendations,
        "carbon_forecast": carbon_forecast,
        "thought_chain": thought_chain,
        "stats": {
            "stops_analysed": len(stops),
            "alerts_generated": len(alerts),
            "recommendations_generated": len(recommendations),
            "weather_risk": w["level"],
            "traffic_level": t_label,
            "duration_ms": duration_ms,
        },
    }
