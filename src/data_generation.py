from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from src.config import DATA_RAW, RANDOM_SEED, ensure_directories
from src.utils import get_logger, write_csv

LOGGER = get_logger(__name__)

CLIENT_TYPES = ["rideshare", "delivery", "autonomous_taxi", "logistics", "mixed_mobility"]
STATES = ["CA", "TX", "NY", "FL", "IL", "AZ", "WA", "GA", "CO", "NV"]
REGIONS = ["West", "South", "Northeast", "Midwest"]
VEHICLE_TYPES = ["sedan", "suv", "van", "robotaxi", "delivery_van"]
MAKES = ["Aster", "Nova", "MetroMotion", "Helio", "Vector"]
MODELS = ["LX", "Urban", "FleetPro", "Sense", "Auton"]
SENSOR_VENDORS = ["Northstar Sensors", "ClearPath Systems", "Synthetic Vision", "Metro Lidar"]
CLAIM_TYPES = ["collision", "bodily_injury", "property_damage", "comprehensive", "sensor_damage"]
WEATHER = ["clear", "rain", "fog", "snow", "wind"]


def _rng() -> np.random.Generator:
    return np.random.default_rng(RANDOM_SEED)


def generate_fleets(rng: np.random.Generator, n: int = 80) -> pd.DataFrame:
    rows = []
    for i in range(n):
        fleet_size = int(rng.integers(12, 75))
        autonomy = int(rng.choice([0, 1, 2, 3, 4, 5], p=[0.12, 0.13, 0.18, 0.22, 0.22, 0.13]))
        client_type = str(rng.choice(CLIENT_TYPES))
        rows.append(
            {
                "fleet_id": f"FLT-{i + 1:04d}",
                "client_name": f"Synthetic Mobility Client {i + 1:03d}",
                "client_type": client_type,
                "fleet_size": fleet_size,
                "operating_region": str(rng.choice(REGIONS)),
                "primary_state": str(rng.choice(STATES)),
                "urban_density_score": round(float(rng.uniform(25, 95)), 2),
                "account_tenure_months": int(rng.integers(3, 84)),
                "autonomy_level": autonomy,
                "vehicle_type": str(rng.choice(VEHICLE_TYPES)),
                "annual_mileage_estimate": int(fleet_size * rng.integers(28000, 78000)),
                "average_trip_volume_monthly": int(fleet_size * rng.integers(160, 650)),
                "safety_program_score": round(float(rng.uniform(45, 98)), 2),
                "maintenance_score": round(float(rng.uniform(50, 99)), 2),
                "client_growth_rate": round(float(rng.normal(0.09, 0.12)), 3),
                "account_manager": f"Manager {rng.integers(1, 12):02d}",
            }
        )
    return pd.DataFrame(rows)


def generate_vehicles(fleets: pd.DataFrame, rng: np.random.Generator, n: int = 2000) -> pd.DataFrame:
    fleet_ids = fleets["fleet_id"].to_numpy()
    rows = []
    for i in range(n):
        fleet = fleets.loc[fleets["fleet_id"] == rng.choice(fleet_ids)].iloc[0]
        autonomy = int(max(0, min(5, fleet["autonomy_level"] + rng.choice([-1, 0, 0, 1]))))
        rows.append(
            {
                "vehicle_id": f"VEH-{i + 1:05d}",
                "fleet_id": fleet["fleet_id"],
                "make": str(rng.choice(MAKES)),
                "model": str(rng.choice(MODELS)),
                "model_year": int(rng.integers(2019, 2026)),
                "autonomy_level": autonomy,
                "sensor_vendor": str(rng.choice(SENSOR_VENDORS)),
                "software_version": f"{rng.integers(2, 7)}.{rng.integers(0, 10)}.{rng.integers(0, 20)}",
                "lidar_enabled": bool(autonomy >= 3 and rng.random() > 0.08),
                "camera_enabled": bool(autonomy >= 1 or rng.random() > 0.2),
                "radar_enabled": bool(autonomy >= 2 or rng.random() > 0.35),
                "vehicle_utilization_rate": round(float(rng.uniform(0.25, 0.96)), 3),
                "last_maintenance_date": pd.Timestamp(date(2025, 12, 31)) - pd.to_timedelta(int(rng.integers(5, 180)), unit="D"),
                "maintenance_score": round(float(np.clip(fleet["maintenance_score"] + rng.normal(0, 7), 35, 100)), 2),
            }
        )
    return pd.DataFrame(rows)


def generate_exposure(vehicles: pd.DataFrame, fleets: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    months = pd.date_range("2024-01-01", periods=24, freq="MS")
    fleet_lookup = fleets.set_index("fleet_id")
    rows = []
    idx = 1
    for _, vehicle in vehicles.iterrows():
        fleet = fleet_lookup.loc[vehicle["fleet_id"]]
        for month in months:
            utilization = float(vehicle["vehicle_utilization_rate"])
            miles = max(250, rng.normal(1800 + utilization * 2200, 450))
            autonomous_pct = np.clip((vehicle["autonomy_level"] / 5) * rng.uniform(0.55, 0.95), 0, 0.98)
            auto_miles = miles * autonomous_pct
            manual_miles = miles - auto_miles
            route_risk = np.clip((fleet["urban_density_score"] / 100) + rng.normal(0.25, 0.12), 0, 1.5)
            rows.append(
                {
                    "exposure_id": f"EXP-{idx:07d}",
                    "vehicle_id": vehicle["vehicle_id"],
                    "fleet_id": vehicle["fleet_id"],
                    "month": month.date().isoformat(),
                    "miles_driven": round(float(miles), 2),
                    "autonomous_miles": round(float(auto_miles), 2),
                    "manual_miles": round(float(manual_miles), 2),
                    "autonomous_hours": round(float(auto_miles / rng.uniform(18, 32)), 2),
                    "manual_override_count": int(rng.poisson(max(0.08, route_risk * (vehicle["autonomy_level"] + 1) / 2.8))),
                    "disengagement_count": int(rng.poisson(max(0.05, route_risk * vehicle["autonomy_level"] / 3.5))),
                    "near_miss_events": int(rng.poisson(max(0.04, route_risk * 1.8))),
                    "emergency_braking_events": int(rng.poisson(max(0.06, route_risk * 2.1))),
                    "night_driving_pct": round(float(rng.uniform(0.05, 0.45)), 3),
                    "weather_risk_score": round(float(rng.uniform(10, 85)), 2),
                    "congestion_score": round(float(np.clip(fleet["urban_density_score"] + rng.normal(0, 12), 5, 100)), 2),
                    "route_complexity_score": round(float(np.clip(route_risk * 70 + rng.normal(10, 8), 5, 100)), 2),
                    "pedestrian_density_score": round(float(np.clip(fleet["urban_density_score"] + rng.normal(0, 10), 5, 100)), 2),
                    "construction_zone_exposure": round(float(rng.uniform(0, 0.25)), 3),
                    "sensor_failure_events": int(rng.poisson(0.08 + max(0, vehicle["autonomy_level"] - 2) * 0.18)),
                    "software_update_count": int(rng.poisson(0.45 + vehicle["autonomy_level"] * 0.08)),
                    "ai_confidence_avg": round(float(np.clip(rng.normal(0.91 - route_risk * 0.04, 0.035), 0.65, 0.99)), 3),
                }
            )
            idx += 1
    return pd.DataFrame(rows)


def generate_policies(fleets: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    for i, fleet in fleets.iterrows():
        limit = float(rng.choice([1_000_000, 2_000_000, 5_000_000, 10_000_000]))
        premium = max(50_000, fleet["fleet_size"] * rng.uniform(5200, 14200) * (1 + fleet["autonomy_level"] * 0.035))
        eff = pd.Timestamp("2025-01-01") + pd.to_timedelta(int(rng.integers(0, 80)), unit="D")
        rows.append(
            {
                "policy_id": f"POL-{i + 1:04d}",
                "fleet_id": fleet["fleet_id"],
                "effective_date": eff.date().isoformat(),
                "expiration_date": (eff + pd.DateOffset(years=1)).date().isoformat(),
                "policy_state": fleet["primary_state"],
                "coverage_type": str(rng.choice(["auto_liability", "physical_damage", "combined_auto", "excess_auto"])),
                "policy_limit": limit,
                "deductible": float(rng.choice([5000, 10000, 25000, 50000, 100000])),
                "written_premium": round(float(premium), 2),
                "earned_premium": round(float(premium * rng.uniform(0.45, 0.95)), 2),
                "underwriting_tier": str(rng.choice(["Preferred", "Standard", "Watch", "Referral"], p=[0.22, 0.42, 0.24, 0.12])),
                "pricing_score": round(float(rng.uniform(35, 92)), 2),
                "renewal_flag": bool(rng.random() > 0.28),
                "active_flag": True,
            }
        )
    return pd.DataFrame(rows)


def generate_claims(policies: pd.DataFrame, vehicles: pd.DataFrame, exposure: pd.DataFrame, rng: np.random.Generator, n: int = 1500) -> pd.DataFrame:
    policy_lookup = policies.set_index("fleet_id")
    vehicle_lookup = vehicles.set_index("vehicle_id")
    exposure_by_vehicle = exposure.groupby("vehicle_id").agg({"near_miss_events": "sum", "sensor_failure_events": "sum", "weather_risk_score": "mean"})
    rows = []
    vehicle_ids = vehicles["vehicle_id"].to_numpy()
    for i in range(n):
        vehicle_id = str(rng.choice(vehicle_ids))
        vehicle = vehicle_lookup.loc[vehicle_id]
        policy = policy_lookup.loc[vehicle["fleet_id"]]
        risk_factor = 1 + exposure_by_vehicle.loc[vehicle_id, "near_miss_events"] / 80 + exposure_by_vehicle.loc[vehicle_id, "sensor_failure_events"] / 45
        severity_base = rng.gamma(2.1, 8500) * risk_factor
        paid = max(0, severity_base * rng.uniform(0.3, 0.95))
        reserve = max(0, severity_base - paid)
        loss_date = pd.Timestamp("2025-01-01") + pd.to_timedelta(int(rng.integers(0, 330)), unit="D")
        software_flag = bool(vehicle["autonomy_level"] >= 3 and rng.random() < 0.18)
        sensor_flag = bool(vehicle["autonomy_level"] >= 3 and rng.random() < 0.16)
        bodily = bool(rng.random() < 0.18)
        rows.append(
            {
                "claim_id": f"CLM-{i + 1:06d}",
                "policy_id": policy["policy_id"],
                "vehicle_id": vehicle_id,
                "fleet_id": vehicle["fleet_id"],
                "loss_date": loss_date.date().isoformat(),
                "report_date": (loss_date + pd.to_timedelta(int(rng.integers(0, 21)), unit="D")).date().isoformat(),
                "claim_type": str(rng.choice(CLAIM_TYPES)),
                "claim_status": str(rng.choice(["open", "closed", "litigation", "subrogation"], p=[0.26, 0.58, 0.08, 0.08])),
                "paid_loss": round(float(paid), 2),
                "reserve_amount": round(float(reserve), 2),
                "incurred_loss": round(float(paid + reserve), 2),
                "litigation_flag": bool(rng.random() < (0.04 + bodily * 0.16)),
                "bodily_injury_flag": bodily,
                "property_damage_flag": bool(rng.random() < 0.72),
                "software_failure_flag": software_flag,
                "sensor_issue_flag": sensor_flag,
                "weather_condition": str(rng.choice(WEATHER)),
                "accident_severity": str(rng.choice(["minor", "moderate", "major", "severe"], p=[0.52, 0.31, 0.13, 0.04])),
                "subrogation_recovery": round(float(max(0, rng.normal(1200, 2500))), 2),
                "claim_close_days": int(rng.integers(12, 240)),
            }
        )
    return pd.DataFrame(rows)


def generate_client_interactions(fleets: pd.DataFrame, rng: np.random.Generator, n: int = 400) -> pd.DataFrame:
    topics = ["renewal pricing", "safety program", "claims trend", "autonomy operations", "maintenance controls", "route risk"]
    rows = []
    for i in range(n):
        fleet = fleets.sample(1, random_state=int(rng.integers(0, 999999))).iloc[0]
        rows.append(
            {
                "interaction_id": f"INT-{i + 1:05d}",
                "fleet_id": fleet["fleet_id"],
                "interaction_date": (pd.Timestamp("2025-01-01") + pd.to_timedelta(int(rng.integers(0, 365)), unit="D")).date().isoformat(),
                "interaction_type": str(rng.choice(["QBR", "underwriting_review", "claims_review", "renewal_review", "ad_hoc_analysis"])),
                "topic": str(rng.choice(topics)),
                "recommendation_made": str(rng.choice(["monitor", "pricing review", "safety improvement", "maintenance certification", "no action"])),
                "follow_up_required": bool(rng.random() < 0.38),
                "business_owner": str(rng.choice(["Underwriting", "Claims", "Risk Engineering", "Account Management", "Pricing"])),
            }
        )
    return pd.DataFrame(rows)


def generate_all() -> dict[str, pd.DataFrame]:
    """Generate and save all synthetic source datasets."""
    ensure_directories()
    rng = _rng()
    fleets = generate_fleets(rng)
    vehicles = generate_vehicles(fleets, rng)
    exposure = generate_exposure(vehicles, fleets, rng)
    policies = generate_policies(fleets, rng)
    claims = generate_claims(policies, vehicles, exposure, rng)
    interactions = generate_client_interactions(fleets, rng)
    frames = {
        "fleets": fleets,
        "vehicles": vehicles,
        "exposure": exposure,
        "policies": policies,
        "claims": claims,
        "client_interactions": interactions,
    }
    for name, frame in frames.items():
        write_csv(frame, DATA_RAW / f"{name}.csv")
    LOGGER.info("generated synthetic mobility insurance data")
    return frames


if __name__ == "__main__":
    generate_all()
