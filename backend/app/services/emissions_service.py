from typing import Dict, Any
from app.models.schemas import Vehicle, VehicleType

class EmissionsService:
    """
    Implements GLEC Framework (Global Logistics Emissions Council)
    and DEFRA carbon accounting standards for road freight transport.
    """

    # Baseline emission factors (g CO2e / km)
    DEFAULT_FACTORS: Dict[VehicleType, Dict[str, float]] = {
        VehicleType.CARGO_BIKE: {
            "empty": 4.0,           # Lifecycle + auxiliary power
            "delta_per_kg": 0.005,
            "cost_per_km": 0.35,
            "hourly_rate": 18.0
        },
        VehicleType.EV_VAN: {
            "empty": 48.0,          # Well-to-Wheel based on average grid mix
            "delta_per_kg": 0.025,
            "cost_per_km": 0.65,
            "hourly_rate": 22.0
        },
        VehicleType.HYBRID_VAN: {
            "empty": 128.0,
            "delta_per_kg": 0.042,
            "cost_per_km": 0.95,
            "hourly_rate": 24.0
        },
        VehicleType.DIESEL_VAN: {
            "empty": 195.0,
            "delta_per_kg": 0.065,
            "cost_per_km": 1.25,
            "hourly_rate": 25.0
        }
    }

    WEATHER_MULTIPLIERS = {
        "clear": 1.0,
        "rainy": 1.08,  # Increased rolling resistance & windscreen/wiper draw
        "stormy": 1.18, # Heavy headwinds, extreme stop-and-go
        "cold": 1.15    # Battery preconditioning or diesel warmup inefficiencies
    }

    @classmethod
    def calculate_segment_co2(
        cls,
        distance_km: float,
        payload_kg: float,
        vehicle: Vehicle,
        traffic_congestion: float = 1.0,
        weather: str = "clear"
    ) -> float:
        """
        Calculates CO2 emissions in kilograms for a route segment.
        Formula:
          CO2 (kg) = ( (F_empty + payload * delta_factor) * traffic_penalty * weather_penalty * distance_km ) / 1000
        """
        factors = cls.DEFAULT_FACTORS.get(vehicle.type, cls.DEFAULT_FACTORS[VehicleType.DIESEL_VAN])
        base_factor = vehicle.co2_factor_empty or factors["empty"]
        load_factor = vehicle.co2_factor_loaded_delta or factors["delta_per_kg"]

        weather_mult = cls.WEATHER_MULTIPLIERS.get(weather.lower(), 1.0)
        
        # Traffic multiplier: idle stop-and-go incurs quadratic penalty for combustion engines, milder for EVs with regenerative braking
        if vehicle.type in [VehicleType.EV_VAN, VehicleType.CARGO_BIKE]:
            traffic_mult = 1.0 + (traffic_congestion - 1.0) * 0.3
        else:
            traffic_mult = 1.0 + (traffic_congestion - 1.0) * 0.75

        emission_per_km_grams = (base_factor + (payload_kg * load_factor)) * traffic_mult * weather_mult
        segment_co2_kg = (emission_per_km_grams * distance_km) / 1000.0
        return max(0.001, segment_co2_kg)

    @classmethod
    def calculate_segment_cost(
        cls,
        distance_km: float,
        duration_min: float,
        vehicle: Vehicle
    ) -> float:
        """
        Total cost = (distance * cost_per_km) + (hours * hourly_rate)
        """
        factors = cls.DEFAULT_FACTORS.get(vehicle.type, cls.DEFAULT_FACTORS[VehicleType.DIESEL_VAN])
        km_rate = vehicle.base_cost_per_km or factors["cost_per_km"]
        hr_rate = vehicle.hourly_rate or factors["hourly_rate"]

        fuel_wear_cost = distance_km * km_rate
        driver_time_cost = (duration_min / 60.0) * hr_rate
        return round(fuel_wear_cost + driver_time_cost, 2)
