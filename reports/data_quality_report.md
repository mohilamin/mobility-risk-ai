# Data Quality Report

Total checks: 14
Checks with findings: 2

- **duplicate_policy_ids** (high): 0 findings. Policy IDs should be unique.
- **missing_fleet_ids** (critical): 0 findings. Fleet IDs are required across core tables.
- **claims_without_policies** (critical): 0 findings. Every claim must map to a policy.
- **vehicles_without_fleets** (critical): 0 findings. Every vehicle must map to a fleet.
- **exposure_without_vehicles** (critical): 0 findings. Every exposure record must map to a vehicle.
- **negative_premium** (critical): 0 findings. Premium cannot be negative.
- **negative_incurred_loss** (critical): 0 findings. Incurred loss cannot be negative.
- **invalid_autonomy_levels** (high): 0 findings. Autonomy level must be 0 through 5.
- **expired_policies_marked_active** (medium): 0 findings. Expired policies should not be active.
- **claims_reported_before_loss** (critical): 0 findings. Claims cannot be reported before loss date.
- **earned_premium_gt_written** (high): 0 findings. Earned premium should not exceed written premium.
- **missing_sensor_data_autonomy_4_5** (high): 60 findings. Level 4/5 vehicles should have lidar, camera, and radar enabled.
- **unusually_high_manual_override_rates** (medium): 1346 findings. Manual override rate should be reviewed when above 15 per 1,000 autonomous miles.
- **unmatched_policy_claim_exposure_records** (critical): 0 findings. Claimed vehicles should have exposure records.
