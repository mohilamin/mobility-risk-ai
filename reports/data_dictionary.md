# Data Dictionary

## fleets.csv
Account-level commercial mobility client profile including fleet size, client type, region, state, autonomy level, mileage, safety, maintenance, growth, and account owner.

## vehicles.csv
Vehicle-level fleet assets including autonomy capability, sensor vendor, software version, sensor flags, utilization, and maintenance.

## exposure.csv
Monthly vehicle exposure including miles, autonomous/manual split, overrides, disengagements, near misses, emergency braking, weather, congestion, route complexity, sensor failures, software updates, and AI confidence.

## policies.csv
Policy terms, premium, limit, deductible, underwriting tier, pricing score, renewal status, and active status.

## claims.csv
Claim-level losses, reserves, litigation, injury/property flags, software/sensor indicators, weather, severity, recovery, and close time.

## client_interactions.csv
Portfolio and account management touchpoints with recommendations, follow-ups, topics, and owners.

## Top ML Features Observed: loss_ratio, claim_severity, claim_frequency, software_stability_score, operational_complexity_score, environmental_risk_score, disengagement_rate, emergency_braking_rate
