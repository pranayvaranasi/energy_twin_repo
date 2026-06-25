import random


def calculate_pdm_risk(run_rate_str: str, power_stress_str: str) -> dict:
    """
    Simulates a deep learning Predictive Maintenance (PdM) model assessing 
    the health of critical infrastructure under sudden rerouted capacity loads.
    """
    try:
        run_rate = float(run_rate_str.replace('%', ''))
        power_stress = float(power_stress_str.split('/')[0])
    except Exception:
        run_rate, power_stress = 85.0, 50.0

    base_risk = 0.08
    stress_penalty = max(0, (run_rate - 85.0) * 0.025) + max(0, (power_stress - 60.0) * 0.015)
    failure_probability = min(0.95, base_risk + stress_penalty + random.uniform(0.01, 0.04))

    if failure_probability > 0.60:
        status = "🔴 CRITICAL: Imminent Component Fatigue"
        recommendation = "Pre-position maintenance crews at primary destination. Procure spare turbine blades immediately."
    elif failure_probability > 0.35:
        status = "🟠 WARNING: Accelerated Wear Detected"
        recommendation = "Increase Condition-Based Monitoring (CBM) frequency. Monitor thermal output."
    else:
        status = "🟢 STABLE: Normal Operating Parameters"
        recommendation = "Continue standard preventive maintenance schedule."

    return {
        "asset": "Jamnagar Primary Refining Complex",
        "failure_probability": f"{failure_probability * 100:.1f}%",
        "status": status,
        "recommendation": recommendation,
    }
