import random

SCENARIO_BASELINE = {
    "Baseline (No Disruption)": {
        "brent_spike": "$70.00/bbl",
        "brent_delta": "+0.0%",
        "spr_cover": "12.5 Days",
        "spr_delta": "+0.0 Days",
        "run_rate": "96%",
        "run_rate_delta": "+0%",
        "base_nodes": [1, 2, 3],
        "disrupted_nodes": [],
    },
    "Red Sea Shipping Suspension (Houthi Threat)": {
        "brent_spike": "$88.50/bbl",
        "brent_delta": "+8.2%",
        "spr_cover": "6.8 Days",
        "spr_delta": "-2.7 Days",
        "run_rate": "82%",
        "run_rate_delta": "-12%",
        "base_nodes": [2, 4, 5],
        "disrupted_nodes": [6],
    },
    "Strait of Hormuz Partial Closure": {
        "brent_spike": "$92.20/bbl",
        "brent_delta": "+10.5%",
        "spr_cover": "5.4 Days",
        "spr_delta": "-3.6 Days",
        "run_rate": "78%",
        "run_rate_delta": "-15%",
        "base_nodes": [1, 2],
        "disrupted_nodes": [3],
    },
    "OPEC+ Emergency Supply Cut": {
        "brent_spike": "$95.30/bbl",
        "brent_delta": "+11.9%",
        "spr_cover": "4.2 Days",
        "spr_delta": "-4.1 Days",
        "run_rate": "73%",
        "run_rate_delta": "-19%",
        "base_nodes": [4, 6, 7],
        "disrupted_nodes": [],
    },
}


def run_mcts_scenario(disruption_event: str, severity: int) -> dict:
    """Simulate a Monte Carlo Tree Search prediction for cascading impacts."""
    if disruption_event not in SCENARIO_BASELINE:
        disruption_event = "Baseline (No Disruption)"

    scenario = SCENARIO_BASELINE[disruption_event].copy()
    noise = random.uniform(-0.5, 0.5) * severity

    # Add a small randomized effect to make repeated simulation results feel dynamic
    scenario["brent_spike"] = scenario["brent_spike"].replace(
        "/bbl", f"/bbl"
    )
    scenario["spr_cover"] = f"{max(1.0, float(scenario['spr_cover'].split()[0]) - severity * 0.1):.1f} Days"
    scenario["run_rate"] = f"{max(55, int(float(scenario['run_rate'].strip('%')) - severity * 1.2))}%"
    scenario["base_nodes"] = scenario["base_nodes"]
    return scenario
