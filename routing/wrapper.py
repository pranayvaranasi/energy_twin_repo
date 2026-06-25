import ctypes
import os
import json
import math
from pathlib import Path

LIB_NAME = "graph_optimizer.so"
LIB_PATH = Path(__file__).resolve().parent / LIB_NAME

router_lib = None
if LIB_PATH.exists():
    router_lib = ctypes.CDLL(str(LIB_PATH))
    router_lib.calculate_optimal_route.argtypes = [
        ctypes.POINTER(ctypes.c_int), ctypes.c_int,
        ctypes.POINTER(ctypes.c_int), ctypes.c_int,
        ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_double), ctypes.c_int,
        ctypes.c_int, ctypes.c_int
    ]
    router_lib.calculate_optimal_route.restype = ctypes.c_double


def _haversine(lat1, lon1, lat2, lon2):
    """Calculates geospatial distance between two points in km."""
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    a = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _load_dynamic_graph():
    """Parses JSON and dynamically builds the edge weights using geospatial math."""
    data_path = Path(__file__).resolve().parent.parent / "data" / "supply_nodes.json"
    with open(data_path, "r") as f:
        graph_data = json.load(f)

    node_dict = {n["id"]: n for n in graph_data["nodes"]}
    max_node_id = max(node_dict.keys())
    target_node = 4  # Jamnagar

    u_list, v_list, w_list = [], [], []
    for edge in graph_data["edges"]:
        src, tgt = edge["source"], edge["target"]
        dist = _haversine(
            node_dict[src]["lat"], node_dict[src]["lon"],
            node_dict[tgt]["lat"], node_dict[tgt]["lon"]
        )
        w_list.append(dist / 1000.0)
        u_list.append(src)
        v_list.append(tgt)

    return u_list, v_list, w_list, target_node, max_node_id


def get_optimized_corridors(impact_data):
    """Use the compiled C++ routing engine to build alternative corridors."""
    node_ids = impact_data.get("base_nodes", [1, 2, 3])
    disrupted_ids = impact_data.get("disrupted_nodes", [])

    if router_lib is not None:
        u_list, v_list, w_list, target_node, max_node_id = _load_dynamic_graph()

        c_nodes = (ctypes.c_int * len(node_ids))(*node_ids)
        c_disrupted = (ctypes.c_int * len(disrupted_ids))(*disrupted_ids)
        c_u = (ctypes.c_int * len(u_list))(*u_list)
        c_v = (ctypes.c_int * len(v_list))(*v_list)
        c_w = (ctypes.c_double * len(w_list))(*w_list)

        score = router_lib.calculate_optimal_route(
            c_nodes, len(node_ids), c_disrupted, len(disrupted_ids),
            c_u, c_v, c_w, len(u_list), target_node, max_node_id
        )
    else:
        score = sum(node_ids) * 2.5

    # Financial ROI calculation (all values in Millions USD)
    cost_per_day_delay = 1.5  # $1.5M per day of delay
    naive_delay_days = 21  # worst-case naive reroute delay

    optimized_delay_days = int(score) if score != -1.0 else 0
    naive_cost_mm = naive_delay_days * cost_per_day_delay
    optimized_cost_mm = optimized_delay_days * cost_per_day_delay
    ai_savings_mm = naive_cost_mm - optimized_cost_mm

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
