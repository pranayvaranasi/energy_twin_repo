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
    """Simulate cascading impacts using the PyTorch TFT Model."""
    if disruption_event not in SCENARIO_BASELINE:
        disruption_event = "Baseline (No Disruption)"

    scenario_nodes = SCENARIO_BASELINE[disruption_event].copy()
    economic_forecast = predict_economic_fallout(
        disruption_event,
        severity,
        elasticity,
        spr_release_cap,
        refinery_buffer,
    )

    final_impact_data = {**scenario_nodes, **economic_forecast}
    return final_impact_data
