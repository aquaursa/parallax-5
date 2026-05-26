"""Insurance premium calculation."""
from __future__ import annotations

BASELINE_RATE = 0.0085
COVERAGE_BY_LEVEL = {
    "P0": 0.00, "P1": 0.15, "P2": 0.40, "P3": 0.65, "P4": 0.85, "P5": 0.93,
}
L_OBS = 0.672
L_UNOBS = 0.272
L_AMB = 0.056


def quote_premium(tvl: float, level: str, eps: float = 0.005,
                  target_loss_ratio: float = 0.65,
                  historical_incidents: int = 0,
                  age_years: float = 1.0) -> dict:
    base_cov = COVERAGE_BY_LEVEL[level]
    coverage = base_cov * (1.0 - eps)
    base = tvl * BASELINE_RATE
    L_obs_residual = base * L_OBS * (1.0 - coverage)
    L_unobs = base * L_UNOBS
    L_amb = base * L_AMB * (1.0 - 0.5 * coverage)
    historical_factor = 1.0 + (historical_incidents / max(age_years, 1.0)) * 0.15
    historical_factor = max(0.7, min(historical_factor, 2.0))
    L_total = (L_obs_residual + L_unobs + L_amb) * historical_factor
    premium = L_total / target_loss_ratio
    return {
        "tvl_usd": tvl,
        "level": level,
        "coverage": coverage,
        "expected_loss_usd": L_total,
        "premium_usd": premium,
        "breakdown": {
            "L_observable_residual": L_obs_residual,
            "L_unobservable": L_unobs,
            "L_ambiguous": L_amb,
            "historical_factor": historical_factor,
        },
    }
