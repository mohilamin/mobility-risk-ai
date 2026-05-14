CREATE VIEW underwriting_account_summary AS
SELECT fleet_id, client_name, client_type, primary_state, autonomy_level, risk_score, risk_tier, top_risk_driver, underwriting_recommendation
FROM fleet_monthly_risk_scores;

CREATE VIEW high_risk_accounts AS
SELECT *
FROM underwriting_account_summary
WHERE risk_tier IN ('High', 'Critical');

CREATE VIEW renewal_review_queue AS
SELECT u.*
FROM underwriting_account_summary u
JOIN policies p ON u.fleet_id = p.fleet_id
WHERE p.renewal_flag = TRUE AND u.risk_tier IN ('Medium', 'High', 'Critical');

CREATE VIEW pricing_review_candidates AS
SELECT fleet_id, client_name, risk_score, risk_tier, loss_ratio, underwriting_recommendation
FROM fleet_monthly_risk_scores
WHERE loss_ratio > 0.75 OR risk_tier IN ('High', 'Critical');
