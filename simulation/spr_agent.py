import pandas as pd
import math


def generate_spr_schedule(severity_score: int, delay_days: int, max_spr_capacity_mbpd: float = 1.5):
    """
    Advanced Strategic Reserve Optimisation Agent.
    Models India's actual 5.33 MMT (~39 Million Barrels) SPR constraint and calculates
    a non-linear drawdown policy to bridge the deficit without prematurely exhausting reserves.
    """
    if delay_days <= 0 or severity_score == 0:
        return None

    # FACTUAL BASELINE: India's total SPR capacity is approx 39 Million Barrels (5.33 MMT).
    # If the caverns are 64% full (current estimated real-world levels), we have ~25M barrels ready.
    remaining_spr_barrels = 25.0

    # The initial supply shock gap based on the crisis severity
    peak_gap = (severity_score / 10.0) * 2.8

    schedule = []
    current_gap = peak_gap

    # Logistics Lag: It takes roughly 5 days for alternative spot-market cargos to arrive.
    # Therefore, the deficit stays critically high for the first few days before tapering.
    spot_market_lag = 5

    for day in range(1, delay_days + 1):
        # AI Rationing Policy: If the disruption outlasts the SPR capacity, we must ration the release.
        rationing_factor = 1.0 if delay_days <= 8 else (8.0 / delay_days)

        # Target draw is capped by daily infrastructure pumping limits (max_spr_capacity_mbpd)
        target_draw = min(current_gap, max_spr_capacity_mbpd) * rationing_factor

        # Enforce the physical limits of the underground caverns
        actual_draw = min(target_draw, remaining_spr_barrels)
        remaining_spr_barrels -= actual_draw

        # Determine the operational status of the national reserves
        if remaining_spr_barrels > 12:
            status = "🟢 Stable"
        elif remaining_spr_barrels > 0:
            status = "🟠 Critical Rationing"
        else:
            status = "🔴 DEPLETED"

        schedule.append({
            "Day": f"Day {day}",
            "Supply Gap (M bpd)": round(current_gap, 2),
            "Recommended SPR Release (M bpd)": round(actual_draw, 2),
            "SPR Remaining (M Barrels)": round(remaining_spr_barrels, 2),
            "Status": status
        })

        # Non-linear supply gap reduction:
        if day >= spot_market_lag:
            # Alternative logistics kick in, and the supply gap decays exponentially
            recovery_rate = 0.30  # 30% gap reduction per day as spot buys arrive
            current_gap = current_gap * (1.0 - recovery_rate)
        else:
            # During the initial lag, market panic and hoarding keep the deficit mostly flat
            current_gap = current_gap * 0.98

    df = pd.DataFrame(schedule)
    return df if not df.empty else None
