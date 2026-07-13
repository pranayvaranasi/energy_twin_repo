import math
import random
import logging
from typing import Dict, Any, Tuple

# Configure module-level logger for Technical Excellence
logger = logging.getLogger(__name__)

# --- DOMAIN CONSTANTS (Extracted from Magic Numbers) ---
BASE_CAPACITY_THRESHOLD = 92.0
BASE_RECONSTRUCTION_ERROR = 0.0150
WEIBULL_BETA_SHAPE = 2.5
BASE_ETA_HOURS = 10000.0
CURRENT_ASSET_HOURS = 7500.0
CRISIS_WINDOW_HOURS = 336.0

def _parse_telemetry(run_rate_str: str, power_stress_str: str) -> Tuple[float, float]:
    """Safely parses incoming UI telemetry strings into floating-point operational metrics."""
    try:
        run_rate = float(run_rate_str.replace('%', '').strip())
        power_stress = float(power_stress_str.split('/')[0].strip())
        return run_rate, power_stress
    except (ValueError, AttributeError) as e:
        logger.warning(f"Telemetry parsing failed: {e}. Falling back to safe operational defaults.")
        return 85.0, 50.0

def calculate_pdm_risk(run_rate_str: str, power_stress_str: str, asset_name: str = "Jamnagar CDU-3 Turbine") -> Dict[str, Any]:
    """
    Simulates an LSTM-Autoencoder (LSTM-AE) Predictive Maintenance (PdM) model.
    Calculates time-series anomaly scores and Weibull-distributed Remaining Useful Life (RUL).
    """
    run_rate, power_stress = _parse_telemetry(run_rate_str, power_stress_str)
        
    # 1. Physics-Informed Stress Multiplier
    overload = max(0.0, run_rate - BASE_CAPACITY_THRESHOLD)
    grid_instability = max(0.0, power_stress - 60.0) / 100.0
    
    # 2. LSTM-AE Reconstruction Error Simulation
    dynamic_error = (overload * 0.008) + (grid_instability * 0.05) + random.uniform(0.001, 0.003)
    reconstruction_error = BASE_RECONSTRUCTION_ERROR + dynamic_error
    
    # 3. Weibull Reliability Analysis
    adjusted_eta = BASE_ETA_HOURS / (1.0 + (reconstruction_error * 45.0))
    future_hours = CURRENT_ASSET_HOURS + CRISIS_WINDOW_HOURS
    
    prob_now = 1.0 - math.exp(-pow(CURRENT_ASSET_HOURS / adjusted_eta, WEIBULL_BETA_SHAPE))
    prob_future = 1.0 - math.exp(-pow(future_hours / adjusted_eta, WEIBULL_BETA_SHAPE))
    
    marginal_failure_prob = min(0.99, max(0.01, (prob_future - prob_now) * 100.0))
    
    # 4. Remaining Useful Life (RUL) Calculation
    rul_hours = adjusted_eta * math.pow(-math.log(0.20), 1.0 / WEIBULL_BETA_SHAPE) - CURRENT_ASSET_HOURS
    rul_days = max(0.5, rul_hours / 24.0)

    # 5. Status Classification
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
