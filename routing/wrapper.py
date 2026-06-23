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

    # If the C++ engine determines all external routes are blocked (-1.0)
    if score == -1.0:
        return [{
            "Rank": 1, "Source": "Strategic Reserves (SPR)", 
            "Corridor": "Domestic Pipeline Release", 
            "Est. Delay": "0 Days", "Cost Premium": "None", 
            "Routing Score": "EMERGENCY DRAWDOWN"
        }]

    # Otherwise, return dynamic routes based on the calculated transit score
    return [
        {"Rank": 1, "Source": "West Africa (Spot Market)", "Corridor": "Cape of Good Hope -> Mumbai", "Est. Delay": f"+{int(score)} Days", "Cost Premium": "High", "Routing Score": f"{score:.1f}"},
        {"Rank": 2, "Source": "US Gulf Coast", "Corridor": "Atlantic -> Suez -> Jamnagar", "Est. Delay": f"+{int(score * 1.5)} Days", "Cost Premium": "Medium", "Routing Score": f"{score * 1.5:.1f}"},
    ]
