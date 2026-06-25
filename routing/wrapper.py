import ctypes
import os
from pathlib import Path

LIB_NAME = "graph_optimizer.so"
LIB_PATH = Path(__file__).resolve().parent / LIB_NAME

router_lib = None
if LIB_PATH.exists():
    router_lib = ctypes.CDLL(str(LIB_PATH))
    # Update argtypes to accept the new disrupted_nodes arrays
    router_lib.calculate_optimal_route.argtypes = [
        ctypes.POINTER(ctypes.c_int), ctypes.c_int,
        ctypes.POINTER(ctypes.c_int), ctypes.c_int
    ]
    router_lib.calculate_optimal_route.restype = ctypes.c_double

def get_optimized_corridors(impact_data):
    """Use the compiled C++ routing engine to build alternative corridors."""
    node_ids = impact_data.get("base_nodes", [1, 2, 3])
    disrupted_ids = impact_data.get("disrupted_nodes", [])

    node_array = (ctypes.c_int * len(node_ids))(*node_ids)
    disrupted_array = (ctypes.c_int * len(disrupted_ids))(*disrupted_ids)

    if router_lib is not None:
        score = router_lib.calculate_optimal_route(node_array, len(node_ids), disrupted_array, len(disrupted_ids))
    else:
        score = sum(node_ids) * 2.5

    # Financial ROI calculation (all values in Millions USD)
    cost_per_day_delay = 1.5  # $1.5M per day of delay
    naive_delay_days = 21  # worst-case naive reroute delay

    optimized_delay_days = int(score) if score != -1.0 else 0
    naive_cost_mm = naive_delay_days * cost_per_day_delay
    optimized_cost_mm = optimized_delay_days * cost_per_day_delay
    ai_savings_mm = naive_cost_mm - optimized_cost_mm

    # If the C++ engine determines all external routes are blocked (-1.0)
    if score == -1.0:
        routes = [
            {
                "Rank": 1,
                "Source": "Strategic Reserves",
                "Corridor": "Domestic Pipeline",
                "Est. Delay": "0 Days",
                "Port Congestion": "N/A",
                "Grade Match": "100% (Blended)",
                "Routing Score": "EMERGENCY DRAWDOWN",
            }
        ]
    else:
        routes = [
            {
                "Rank": 1,
                "Source": "West Africa (Spot)",
                "Corridor": "Cape of Good Hope",
                "Est. Delay": f"+{optimized_delay_days} Days",
                "Port Congestion": "High (92% Cap)",
                "Grade Match": "94% (Light Sweet)",
                "Routing Score": f"{score:.1f}",
            },
            {
                "Rank": 2,
                "Source": "Atlantic",
                "Corridor": "Atlantic -> Suez -> Jamnagar",
                "Est. Delay": f"+{int(score * 1.5)} Days",
                "Port Congestion": "Moderate (75% Cap)",
                "Grade Match": "88% (Medium Sour)",
                "Routing Score": f"{score * 1.5:.1f}",
            },
        ]

    financials = {
        "naive_cost": f"${naive_cost_mm:.1f}M",
        "optimized_cost": f"${optimized_cost_mm:.1f}M",
        "ai_savings": f"${ai_savings_mm:.1f}M",
    }

    return {"routes": routes, "financials": financials}
