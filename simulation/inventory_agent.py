import json
from collections import deque
from pathlib import Path


def load_graph_structure():
    data_path = Path(__file__).resolve().parent.parent / "data" / "supply_nodes.json"
    with open(data_path, "r") as f:
        return json.load(f)


def calculate_stranded_inventory(disrupted_nodes, severity, current_brent_price=80.0):
    """
    Advanced BFS Impact-Tree Traversal modeling downstream asset starvation,
    Days of Inventory on Hand (DOH) depletion curves, and Economic Exposure.
    """
    if not disrupted_nodes:
        return None

    graph_data = load_graph_structure()
    node_dict = {n["id"]: n for n in graph_data["nodes"]}

    # Build directed adjacency list for downstream dependency tracking
    adj = {node_id: [] for node_id in node_dict.keys()}
    for edge in graph_data["edges"]:
        adj[edge["source"]].append(edge["target"])

    impacted_refineries = {}
    stranded_volume_mmbpd = 0.0

    # Traverse the impact tree via BFS from each active point of disruption
    for start_node in disrupted_nodes:
        if start_node not in node_dict:
            continue

        node_info = node_dict[start_node]
        node_cap = node_info.get("capacity_mmbpd", 0.0)

        # Quantify volume trapped at this specific chokepoint corridor
        trapped_volume = node_cap if node_cap > 0 else (severity * 0.4)
        stranded_volume_mmbpd += trapped_volume

        queue = deque([start_node])
        seen = {start_node}

        while queue:
            current = queue.popleft()
            current_node = node_dict[current]

            # If the disruption wave cascades into a refining node
            if current_node["type"] == "refinery":
                refinery_name = current_node["name"]
                ref_capacity = current_node.get("capacity_mmbpd", 1.5)

                if refinery_name not in impacted_refineries:
                    impacted_refineries[refinery_name] = {
                        "capacity": ref_capacity,
                        "deficit_contribution": 0.0,
                    }
                impacted_refineries[refinery_name]["deficit_contribution"] += trapped_volume

            for neighbor in adj[current]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append(neighbor)

    # --- ADVANCED INDUSTRIAL LOGISTICS METRICS ---

    # 1. Localized Days of Inventory on Hand (DOH) Depletion Modeling
    # Calibrated against India's national 9.5-day emergency reserve cushion
    SPR_BASE_BUFFER_DAYS = 9.5
    refinery_reports = []

    for name, metrics in impacted_refineries.items():
        allocated_deficit = min(metrics["capacity"], metrics["deficit_contribution"])

        # Structural depletion curve: calculate how fast safety stocks deplete based on deficit severity
        depletion_rate = allocated_deficit / metrics["capacity"] if metrics["capacity"] > 0 else 0.5
        remaining_doh = max(0.0, SPR_BASE_BUFFER_DAYS * (1.0 - (depletion_rate * (severity / 10.0))))

        refinery_reports.append({
            "name": name,
            "allocated_deficit": f"{allocated_deficit:.2f} MMbpd",
            "days_of_cover": f"{remaining_doh:.1f} Days",
            "risk_tier": "CRITICAL" if remaining_doh < 4.0 else "HIGH" if remaining_doh < 7.0 else "MODERATE",
        })

    # 2. Capital Exposure & Holding Costs vs Stoppage Penalties
    # Annualized inventory holding costs (MRO/Storage/Insurance) average ~15% in the energy sector
    total_barrels_stranded = stranded_volume_mmbpd * 1_000_000
    capital_tied_up = total_barrels_stranded * current_brent_price
    daily_holding_cost = (capital_tied_up * 0.15) / 365.0

    # Unplanned downstream production downtime in heavy refining averages $250,000/hour ($6M/day)
    daily_stoppage_risk = len(impacted_refineries) * 250_000 * 24 if impacted_refineries else 0.0

    return {
        "stranded_volume": f"{stranded_volume_mmbpd:.2f} MMbpd",
        "daily_financial_deficit": f"${capital_tied_up:,.0f} USD Assets Stranded",
        "daily_holding_cost": f"${daily_holding_cost:,.0f} USD / Day",
        "operational_stoppage_exposure": f"${daily_stoppage_risk:,.0f} USD / Day",
        "inventory_status": "CRITICAL: Supply Starvation" if severity >= 7 else "WARNING: Congested Flow",
        "refinery_impacts": refinery_reports,
    }
