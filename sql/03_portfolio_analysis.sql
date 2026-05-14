-- Loss ratio by fleet
SELECT f.fleet_id, f.client_name, SUM(c.incurred_loss) / NULLIF(MAX(p.earned_premium), 0) AS loss_ratio
FROM fleets f
JOIN policies p ON f.fleet_id = p.fleet_id
LEFT JOIN claims c ON f.fleet_id = c.fleet_id
GROUP BY f.fleet_id, f.client_name
ORDER BY loss_ratio DESC;

-- Loss ratio by client type
SELECT f.client_type, SUM(c.incurred_loss) / NULLIF(SUM(p.earned_premium), 0) AS loss_ratio
FROM fleets f
JOIN policies p ON f.fleet_id = p.fleet_id
LEFT JOIN claims c ON f.fleet_id = c.fleet_id
GROUP BY f.client_type;

-- Top 10 high-risk fleets
SELECT fleet_id, client_name, risk_score, risk_tier, top_risk_driver
FROM fleet_monthly_risk_scores
ORDER BY risk_score DESC
LIMIT 10;

-- Incurred loss by state
SELECT f.primary_state, SUM(c.incurred_loss) AS incurred_loss
FROM fleets f
JOIN claims c ON f.fleet_id = c.fleet_id
GROUP BY f.primary_state;

-- Frequency/severity by autonomy level
SELECT f.autonomy_level, COUNT(c.claim_id) * 1.0 / NULLIF(SUM(e.miles_driven) / 1000, 0) AS claim_frequency, AVG(c.incurred_loss) AS avg_severity
FROM fleets f
JOIN exposure e ON f.fleet_id = e.fleet_id
LEFT JOIN claims c ON f.fleet_id = c.fleet_id
GROUP BY f.autonomy_level;

-- Premium adequacy view
SELECT f.fleet_id, f.client_name, SUM(c.incurred_loss) / NULLIF(MAX(p.earned_premium), 0) AS loss_ratio, MAX(p.written_premium) AS written_premium
FROM fleets f
JOIN policies p ON f.fleet_id = p.fleet_id
LEFT JOIN claims c ON f.fleet_id = c.fleet_id
GROUP BY f.fleet_id, f.client_name
HAVING SUM(c.incurred_loss) / NULLIF(MAX(p.earned_premium), 0) > 0.75;

-- Portfolio concentration
SELECT client_type, SUM(written_premium) AS premium, SUM(written_premium) / SUM(SUM(written_premium)) OVER () AS premium_share
FROM policies p
JOIN fleets f ON p.fleet_id = f.fleet_id
GROUP BY client_type;
