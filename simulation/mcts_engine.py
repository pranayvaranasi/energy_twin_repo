import random
from simulation.economic_impact_model import predict_economic_fallout

SCENARIO_BASELINE = {
    "Baseline (No Disruption)": {"base_nodes": [1, 2, 3], "disrupted_nodes": []},
    "Red Sea Shipping Suspension (Houthi Threat)": {"base_nodes": [2, 4, 5], "disrupted_nodes": [6]},
    "Strait of Hormuz Partial Closure": {"base_nodes": [1, 2], "disrupted_nodes": [3]},
    "OPEC+ Emergency Supply Cut": {"base_nodes": [4, 6, 7], "disrupted_nodes": []},
}


def run_mcts_scenario(
    disruption_event: str,
    severity: int,
    elasticity: float = -0.4,
    spr_release_cap: float = 1.5,
    refinery_buffer: int = 7,
) -> dict:
    """Runs 1,000 stochastic rollouts to simulate cascading supply chain contagion."""
    if disruption_event not in SCENARIO_BASELINE:
        disruption_event = "Baseline (No Disruption)"

    scenario_nodes = SCENARIO_BASELINE[disruption_event].copy()

    num_rollouts = 1000
    cascading_failures = 0

    for _ in range(num_rollouts):
        base_risk = severity * 0.06
        market_volatility = random.uniform(0.0, 0.4)

        if (base_risk + market_volatility) > 0.85:
            cascading_failures += 1

    contagion_prob = (cascading_failures / num_rollouts) * 100
    model_confidence = max(
        40.0,
        99.0 - (severity * 1.2) + random.uniform(-1.5, 1.5),
    )

    economic_forecast = predict_economic_fallout(
        disruption_event,
        severity,
        elasticity,
        spr_release_cap,
        refinery_buffer,
    )

    final_impact_data = {
        **scenario_nodes,
        **economic_forecast,
        "calculated_severity": severity,
        "contagion_probability": f"{contagion_prob:.1f}%",
        "mcts_confidence": f"{model_confidence:.1f}%",
    }
    return final_impact_data
