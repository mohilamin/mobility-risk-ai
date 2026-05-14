-- Duplicate policies
SELECT policy_id, COUNT(*) AS records
FROM policies
GROUP BY policy_id
HAVING COUNT(*) > 1;

-- Claims without policies
SELECT c.claim_id, c.policy_id
FROM claims c
LEFT JOIN policies p ON c.policy_id = p.policy_id
WHERE p.policy_id IS NULL;

-- Missing exposure
SELECT v.vehicle_id
FROM vehicles v
LEFT JOIN exposure e ON v.vehicle_id = e.vehicle_id
WHERE e.vehicle_id IS NULL;

-- Invalid active policy statuses
SELECT policy_id, expiration_date, active_flag
FROM policies
WHERE expiration_date < CURRENT_DATE AND active_flag = TRUE;

-- Negative losses
SELECT claim_id, incurred_loss
FROM claims
WHERE incurred_loss < 0;

-- Autonomy level mismatch
SELECT v.vehicle_id, v.autonomy_level, f.autonomy_level AS fleet_autonomy_level
FROM vehicles v
JOIN fleets f ON v.fleet_id = f.fleet_id
WHERE ABS(v.autonomy_level - f.autonomy_level) > 1;

-- Earned premium greater than written premium
SELECT policy_id, earned_premium, written_premium
FROM policies
WHERE earned_premium > written_premium;
