CREATE TABLE fleets (
  fleet_id TEXT PRIMARY KEY,
  client_name TEXT,
  client_type TEXT,
  fleet_size INTEGER,
  operating_region TEXT,
  primary_state TEXT,
  urban_density_score REAL,
  account_tenure_months INTEGER,
  autonomy_level INTEGER,
  vehicle_type TEXT,
  annual_mileage_estimate INTEGER,
  average_trip_volume_monthly INTEGER,
  safety_program_score REAL,
  maintenance_score REAL,
  client_growth_rate REAL,
  account_manager TEXT
);

CREATE TABLE vehicles (
  vehicle_id TEXT PRIMARY KEY,
  fleet_id TEXT,
  make TEXT,
  model TEXT,
  model_year INTEGER,
  autonomy_level INTEGER,
  sensor_vendor TEXT,
  software_version TEXT,
  lidar_enabled BOOLEAN,
  camera_enabled BOOLEAN,
  radar_enabled BOOLEAN,
  vehicle_utilization_rate REAL,
  last_maintenance_date DATE,
  maintenance_score REAL
);

CREATE TABLE exposure (
  exposure_id TEXT PRIMARY KEY,
  vehicle_id TEXT,
  fleet_id TEXT,
  month DATE,
  miles_driven REAL,
  autonomous_miles REAL,
  manual_miles REAL,
  autonomous_hours REAL,
  manual_override_count INTEGER,
  disengagement_count INTEGER,
  near_miss_events INTEGER,
  emergency_braking_events INTEGER,
  night_driving_pct REAL,
  weather_risk_score REAL,
  congestion_score REAL,
  route_complexity_score REAL,
  pedestrian_density_score REAL,
  construction_zone_exposure REAL,
  sensor_failure_events INTEGER,
  software_update_count INTEGER,
  ai_confidence_avg REAL
);

CREATE TABLE policies (
  policy_id TEXT PRIMARY KEY,
  fleet_id TEXT,
  effective_date DATE,
  expiration_date DATE,
  policy_state TEXT,
  coverage_type TEXT,
  policy_limit REAL,
  deductible REAL,
  written_premium REAL,
  earned_premium REAL,
  underwriting_tier TEXT,
  pricing_score REAL,
  renewal_flag BOOLEAN,
  active_flag BOOLEAN
);

CREATE TABLE claims (
  claim_id TEXT PRIMARY KEY,
  policy_id TEXT,
  vehicle_id TEXT,
  fleet_id TEXT,
  loss_date DATE,
  report_date DATE,
  claim_type TEXT,
  claim_status TEXT,
  paid_loss REAL,
  reserve_amount REAL,
  incurred_loss REAL,
  litigation_flag BOOLEAN,
  bodily_injury_flag BOOLEAN,
  property_damage_flag BOOLEAN,
  software_failure_flag BOOLEAN,
  sensor_issue_flag BOOLEAN,
  weather_condition TEXT,
  accident_severity TEXT,
  subrogation_recovery REAL,
  claim_close_days INTEGER
);

CREATE TABLE client_interactions (
  interaction_id TEXT PRIMARY KEY,
  fleet_id TEXT,
  interaction_date DATE,
  interaction_type TEXT,
  topic TEXT,
  recommendation_made TEXT,
  follow_up_required BOOLEAN,
  business_owner TEXT
);
