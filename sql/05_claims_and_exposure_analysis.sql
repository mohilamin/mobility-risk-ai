-- Claim severity by cause
SELECT claim_type, accident_severity, AVG(incurred_loss) AS avg_incurred_loss, COUNT(*) AS claims
FROM claims
GROUP BY claim_type, accident_severity;

-- Litigation rate by fleet
SELECT fleet_id, AVG(CASE WHEN litigation_flag THEN 1.0 ELSE 0.0 END) AS litigation_rate
FROM claims
GROUP BY fleet_id;

-- Near-miss to claims relationship
SELECT e.fleet_id, SUM(e.near_miss_events) AS near_misses, COUNT(c.claim_id) AS claims
FROM exposure e
LEFT JOIN claims c ON e.fleet_id = c.fleet_id
GROUP BY e.fleet_id;

-- Sensor failure vs claim frequency
SELECT e.fleet_id, SUM(sensor_failure_events) AS sensor_failures, COUNT(c.claim_id) * 1.0 / NULLIF(SUM(miles_driven) / 1000, 0) AS claim_frequency
FROM exposure e
LEFT JOIN claims c ON e.fleet_id = c.fleet_id
GROUP BY e.fleet_id;

-- Software version risk analysis
SELECT v.software_version, COUNT(c.claim_id) AS claims, AVG(c.incurred_loss) AS avg_loss
FROM vehicles v
LEFT JOIN claims c ON v.vehicle_id = c.vehicle_id
GROUP BY v.software_version
ORDER BY claims DESC;

-- Weather exposure vs loss ratio
SELECT f.fleet_id, AVG(e.weather_risk_score) AS weather_risk, SUM(c.incurred_loss) / NULLIF(MAX(p.earned_premium), 0) AS loss_ratio
FROM fleets f
JOIN exposure e ON f.fleet_id = e.fleet_id
JOIN policies p ON f.fleet_id = p.fleet_id
LEFT JOIN claims c ON f.fleet_id = c.fleet_id
GROUP BY f.fleet_id;
