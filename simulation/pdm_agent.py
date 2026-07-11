import math
import random


def calculate_pdm_risk(run_rate_str: str, power_stress_str: str, asset_name: str = "Jamnagar CDU-3 Turbine") -> dict:
    """
    Simulates an LSTM-Autoencoder (LSTM-AE) Predictive Maintenance (PdM) model.
    Calculates time-series anomaly scores and Weibull-distributed Remaining Useful Life (RUL)
    for critical refinery infrastructure under sudden rerouted capacity loads.
    """
    try:
        run_rate = float(run_rate_str.replace('%', ''))
        power_stress = float(power_stress_str.split('/')[0])
    except Exception:
        run_rate, power_stress = 85.0, 50.0

    # 1. Physics-Informed Stress Multiplier (Fatigue Accumulation)
    base_capacity = 92.0
    overload = max(0.0, run_rate - base_capacity)
    grid_instability = max(0.0, power_stress - 60.0) / 100.0

    # 2. LSTM-AE Reconstruction Error Simulation
    base_error = 0.0150
    dynamic_error = (overload * 0.008) + (grid_instability * 0.05) + random.uniform(0.001, 0.003)
    reconstruction_error = base_error + dynamic_error

    # 3. Weibull Reliability Analysis (Probability of Failure)
    beta = 2.5
    base_eta = 10000.0
    adjusted_eta = base_eta / (1.0 + (reconstruction_error * 45.0))
    current_hours = 7500.0
    future_hours = current_hours + 336.0

    prob_now = 1.0 - math.exp(-pow(current_hours / adjusted_eta, beta))
    prob_future = 1.0 - math.exp(-pow(future_hours / adjusted_eta, beta))
    marginal_failure_prob = min(0.99, max(0.01, (prob_future - prob_now) * 100.0))

    # 4. Remaining Useful Life (RUL) Calculation
    rul_hours = adjusted_eta * math.pow(-math.log(0.20), 1.0 / beta) - current_hours
    rul_days = max(0.5, rul_hours / 24.0)

    # 5. Status Classification & Actionable Intelligence
    if marginal_failure_prob > 40.0 or rul_days < 14.0:
        status = "🔴 CRITICAL: Imminent Stator/Turbine Fatigue"
        action = f"Immediate operational scale-down required. RUL critically reduced to {rul_days:.1f} days."
    elif marginal_failure_prob > 15.0 or rul_days < 45.0:
        status = "🟠 WARNING: Accelerated Wear Detected"
        action = f"LSTM-AE reconstruction threshold exceeded ({reconstruction_error:.4f}). Increase Condition-Based Monitoring (CBM)."
    else:
        status = "🟢 STABLE: Normal Operating Parameters"
        action = f"RUL estimated at {rul_days:.1f} days. Continue standard preventive maintenance schedule."

    return {
        "asset": asset_name,
        "failure_probability": f"{marginal_failure_prob:.1f}%",
        "lstm_anomaly_score": f"{reconstruction_error:.4f}",
        "rul_days": f"{rul_days:.1f} Days",
        "status": status,
        "recommendation": action,
    }
