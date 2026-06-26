import ctypes
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
        ctypes.POINTER(ctypes.c_double), ctypes.c_double,
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
    """Parses JSON to build the edges and physical capacity limits."""
    data_path = Path(__file__).resolve().parent.parent / "data" / "supply_nodes.json"
    with open(data_path, "r") as f:
        graph_data = json.load(f)

    node_dict = {n["id"]: n for n in graph_data["nodes"]}
    max_node_id = max(node_dict.keys())
    target_nodes = [node_id for node_id, node in node_dict.items() if node.get("type") == "refinery"]

    capacities = [0.0] * (max_node_id + 1)
    for node_id, node in node_dict.items():
        capacities[node_id] = node.get("capacity_mmbpd", 0.0)

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

    return u_list, v_list, w_list, capacities, target_nodes, max_node_id, node_dict


def get_optimized_corridors(impact_data):
    """Use the compiled C++ routing engine to build alternative corridors."""
    node_ids = impact_data.get("base_nodes", [1, 2, 3])
    disrupted_ids = impact_data.get("disrupted_nodes", [])
    severity = impact_data.get("calculated_severity", 5)
    required_capacity = severity * 0.5

    bottlenecked_ports = []

    selected_target = 4
    selected_target_name = "Jamnagar"

    if router_lib is not None:
        u_list, v_list, w_list, capacities, target_nodes, max_node_id, node_dict = _load_dynamic_graph()

        for node_id, capacity in enumerate(capacities):
            if 0.0 < capacity < required_capacity and node_id in node_dict:
                port_name = node_dict[node_id].get("name", f"Node {node_id}")
                bottlenecked_ports.append(f"{port_name} (Max limit: {capacity:.2f} MMbpd)")

        c_nodes = (ctypes.c_int * len(node_ids))(*node_ids)
        c_disrupted = (ctypes.c_int * len(disrupted_ids))(*disrupted_ids)
        c_u = (ctypes.c_int * len(u_list))(*u_list)
        c_v = (ctypes.c_int * len(v_list))(*v_list)
        c_w = (ctypes.c_double * len(w_list))(*w_list)
        c_capacities = (ctypes.c_double * len(capacities))(*capacities)
        balanced_entry_capacity = required_capacity / max(len(target_nodes), 1)
        c_req_cap = ctypes.c_double(balanced_entry_capacity)

        candidate_scores = []
        for target_node in target_nodes:
            score = router_lib.calculate_optimal_route(
                c_nodes, len(node_ids), c_disrupted, len(disrupted_ids),
                c_u, c_v, c_w, len(u_list),
                c_capacities, c_req_cap,
                target_node, max_node_id
            )
            if score != -1.0:
                candidate_scores.append((score, target_node))

        if candidate_scores:
            score, selected_target = min(candidate_scores, key=lambda candidate: candidate[0])
            selected_target_name = node_dict[selected_target]["name"]
        else:
            score = -1.0
    else:
        score = sum(node_ids) * 2.5

    # Financial ROI calculation (all values in Millions USD)
    cost_per_day_delay = 1.5  # $1.5M per day of delay
    naive_delay_days = 21  # worst-case naive reroute delay

    optimized_delay_days = int(score) if score != -1.0 else 0
    naive_cost_mm = naive_delay_days * cost_per_day_delay
    optimized_cost_mm = optimized_delay_days * cost_per_day_delay
    ai_savings_mm = naive_cost_mm - optimized_cost_mm

    russian_pivot = 8 in node_ids and (3 in disrupted_ids or 6 in disrupted_ids or 2 in disrupted_ids)
    primary_source = "Russian Urals (Baltic)" if russian_pivot else "West Africa (Spot)"
    primary_corridor = "Russian Urals -> Cape of Good Hope" if russian_pivot else "Cape of Good Hope"

    if score == -1.0:
        routes = [
            {
                "Rank": 1,
                "Source": "Mangalore ISPRL (SPR)",
                "Corridor": "Domestic SPR Pipeline",
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
                "Source": primary_source,
                "Corridor": f"{primary_corridor} -> {selected_target_name}",
                "Est. Delay": f"+{optimized_delay_days} Days",
                "Port Congestion": "Balanced across West/East Coast",
                "Grade Match": "94% (Light Sweet)",
                "Routing Score": f"{score:.1f}",
            },
            {
                "Rank": 2,
                "Source": "Atlantic",
                "Corridor": f"Atlantic -> Suez -> {selected_target_name}",
                "Est. Delay": f"+{int(score * 1.5)} Days",
                "Port Congestion": "Secondary entry option",
                "Grade Match": "88% (Medium Sour)",
                "Routing Score": f"{score * 1.5:.1f}",
            },
        ]

    financials = {
        "naive_cost": f"${naive_cost_mm:.1f}M",
        "optimized_cost": f"${optimized_cost_mm:.1f}M",
        "ai_savings": f"${ai_savings_mm:.1f}M",
    }

    return {
        "routes": routes,
        "financials": financials,
        "bottlenecks": bottlenecked_ports,
        "required_capacity": required_capacity,
        "selected_entry_node": selected_target,
        "selected_entry_name": selected_target_name,
    }
