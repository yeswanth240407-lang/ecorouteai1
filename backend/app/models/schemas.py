from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field

class OptimizationPriority(str, Enum):
    GREENEST = "GREENEST"
    BALANCED = "BALANCED"
    FASTEST = "FASTEST"
    CHEAPEST = "CHEAPEST"

class VehicleType(str, Enum):
    EV_VAN = "EV_VAN"
    DIESEL_VAN = "DIESEL_VAN"
    HYBRID_VAN = "HYBRID_VAN"
    CARGO_BIKE = "CARGO_BIKE"

class Stop(BaseModel):
    id: str
    name: str
    lat: float
    lng: float
    demand: float = 10.0  # kg payload
    time_window_start: Optional[int] = None  # minutes from start of shift (e.g. 0 to 480)
    time_window_end: Optional[int] = None
    service_duration: int = 10  # minutes

class Vehicle(BaseModel):
    id: str
    name: str
    type: VehicleType = VehicleType.DIESEL_VAN
    capacity: float = 1000.0  # kg
    fuel_type: str = "Diesel"
    base_cost_per_km: float = 1.20  # USD/EUR per km
    hourly_rate: float = 25.0       # USD/EUR per hour driver & maintenance
    co2_factor_empty: float = 180.0 # g CO2 / km
    co2_factor_loaded_delta: float = 0.05 # g CO2 / (km * kg)

class RouteStep(BaseModel):
    stop_id: str
    name: str
    lat: float
    lng: float
    arrival_time_min: float
    departure_time_min: float
    distance_from_prev_km: float
    time_from_prev_min: float
    accumulated_load_kg: float
    step_co2_kg: float

class RouteCandidate(BaseModel):
    route_id: str
    title: str
    vehicle_id: str
    vehicle_name: str
    vehicle_type: VehicleType
    stops_sequence: List[str]
    steps: List[RouteStep]
    total_distance_km: float
    total_time_min: float
    total_co2_kg: float
    total_cost: float
    geometry: List[List[float]] = Field(default_factory=list, description="Array of [lat, lng] coordinates")
    tag: Optional[str] = None  # e.g. "Greenest Choice", "Fastest Delivery", "Baseline"

class RouteRequest(BaseModel):
    priority: OptimizationPriority = OptimizationPriority.BALANCED
    depot: Stop
    stops: List[Stop]
    vehicles: Optional[List[Vehicle]] = None
    traffic_congestion_level: float = Field(default=1.0, ge=1.0, le=2.0, description="1.0 free flow, 1.3 normal, 1.6 heavy")
    weather_condition: str = Field(default="clear", description="clear, rainy, stormy")

class RouteResponse(BaseModel):
    status: str
    priority: OptimizationPriority
    best_route: RouteCandidate
    candidate_routes: List[RouteCandidate]
    baseline_route: Optional[RouteCandidate] = None
    co2_saved_kg: float
    co2_saved_pct: float
    cost_saved: float
    explanation: str
    agent_logs: List[str] = Field(default_factory=list)
    agent_traces: Dict[str, Any] = Field(default_factory=dict)
