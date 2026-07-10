import json
from collections import deque
from pathlib import Path


def load_graph_structure():
    data_path = Path(__file__).resolve().parent.parent / "data" / "supply_nodes.json"
    with open(data_path, "r") as f:
        return json.load(f)


def calculate_stranded_inventory(disrupted_nodes, severity, current_brent_price=80.0):
    """
    Adapt a BFS impact-tree traversal to identify downstream energy deficits
    and the financial value of stranded maritime assets.
    """
    if not disrupted_nodes:
        return None

    graph_data = load_graph_structure()
    node_dict = {n["id"]: n for n in graph_data["nodes"]}

    adj = {node_id: [] for node_id in node_dict.keys()}
    for edge in graph_data["edges"]:
        adj[edge["source"]].append(edge["target"])

    impacted_refineries = set()
    stranded_volume_mmbpd = 0.0

    for start_node in disrupted_nodes:
        if start_node not in node_dict:
            continue

        node_cap = node_dict[start_node].get("capacity_mmbpd", 0.0)
        trapped_volume = node_cap if node_cap > 0 else (severity * 0.4)
        stranded_volume_mmbpd += trapped_volume

        queue = deque([start_node])
        seen = {start_node}

        while queue:
            current = queue.popleft()

            if node_dict[current]["type"] == "refinery":
                impacted_refineries.add(node_dict[current]["name"])

            for neighbor in adj[current]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append(neighbor)

    daily_financial_loss = stranded_volume_mmbpd * 1_000_000 * current_brent_price

    return {
        "affected_dependents": sorted(impacted_refineries),
        "stranded_volume": f"{stranded_volume_mmbpd:.2f} MMbpd",
        "daily_financial_deficit": f"${daily_financial_loss:,.0f} USD / Day",
        "inventory_status": "CRITICAL: Downstream Starvation" if stranded_volume_mmbpd > 2.0 else "WARNING: Supply Constrained",
    }
