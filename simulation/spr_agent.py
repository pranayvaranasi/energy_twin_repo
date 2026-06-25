import pandas as pd


def generate_spr_schedule(severity_score, delay_days, max_spr_capacity_mbpd):
    """
    Models optimal SPR drawdown schedules to bridge the supply gap
    until the rerouted tankers arrive.
    """
    if delay_days == 0:
        return None  # No disruption

    # Calculate daily supply gap based on severity
    peak_gap = (severity_score / 10.0) * 2.5  # Max 2.5M bpd gap

    schedule = []
    current_gap = peak_gap

    # Generate a daily schedule for the duration of the shipping delay
    for day in range(1, delay_days + 1):
        # AI Logic: Drawdown heavily at first, then taper as alternative spot market buys arrive
        recommended_draw = min(current_gap, max_spr_capacity_mbpd)

        schedule.append({
            "Day": f"Day {day}",
            "Supply Gap (M bpd)": round(current_gap, 2),
            "Recommended SPR Release (M bpd)": round(recommended_draw, 2),
        })

        # Taper the gap as the orchestrator's spot buys begin to fill it
        current_gap = max(0, current_gap - (peak_gap / delay_days))

    return pd.DataFrame(schedule)
