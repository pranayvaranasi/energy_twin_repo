import json
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import streamlit as st


@st.cache_data
def load_graph_data():
    data_path = Path(__file__).resolve().parent.parent / "data" / "supply_nodes.json"
    with open(data_path, "r") as f:
        return json.load(f)


def _resolve_route_edges(active_routes, node_dict):
    """Turn a route description into a sequence of node ids for highlighting."""
    route_edges = []
    for route in active_routes:
        corridor = route.get("Corridor", "").lower()
        target_id = 7 if "visakh" in corridor else 4

        if target_id not in node_dict:
            target_id = 4

        if "cape of good hope" in corridor:
            source_id = 8 if "russian" in corridor else 2
            route_edges.extend([(source_id, 5), (5, target_id)])
        elif "malacca" in corridor:
            route_edges.extend([(3, 10), (10, target_id)])
        elif "suez" in corridor or "red sea" in corridor:
            source_id = 8 if "russian" in corridor else 1
            route_edges.extend([(source_id, 6), (6, target_id)])
        elif "pipeline" in corridor or "domestic" in corridor:
            source_id = 9 if "spr" in corridor or "domestic" in corridor else 3
            route_edges.extend([(source_id, target_id)])
        else:
            source = route.get("Source")
            if source and "russian" in source.lower():
                route_edges.extend([(8, 5), (5, target_id)])
            elif source and "west africa" in source.lower():
                route_edges.extend([(2, 5), (5, target_id)])
            elif source and "us gulf coast" in source.lower():
                route_edges.extend([(1, 6), (6, target_id)])
    return route_edges


def generate_geospatial_twin(impact_data, active_routes, inventory_result=None):
    """Generates an interactive Plotly map with neon bloom effects and starvation tracking."""
    graph_data = load_graph_data()
    node_dict = {node["id"]: node for node in graph_data["nodes"]}
    disrupted_ids = set(impact_data.get("disrupted_nodes", []))
    active_ids = set(impact_data.get("base_nodes", []))
    route_edges = _resolve_route_edges(active_routes, node_dict)

    for _, target_id in route_edges:
        active_ids.add(target_id)

    fig = go.Figure()

    # 1. Draw Default Supply Lines (Faded Background)
    for edge in graph_data["edges"]:
        src = node_dict[edge["source"]]
        tgt = node_dict[edge["target"]]
        line_color = "rgba(150, 150, 150, 0.2)"
        line_width = 1
        dash = "solid"

        if edge["source"] in disrupted_ids or edge["target"] in disrupted_ids:
            line_color = "rgba(239, 68, 68, 0.7)"
            line_width = 2
            dash = "dash"

        fig.add_trace(go.Scattergeo(
            lon=[src["lon"], tgt["lon"]], lat=[src["lat"], tgt["lat"]],
            mode="lines", line=dict(width=line_width, color=line_color, dash=dash),
            hoverinfo="skip"
        ))

    # 2. Highlight Active Corridors with Cyberpunk "Neon Glow" Bloom Effect
    ais_lats, ais_lons, ais_text = [], [], []
    for src_id, tgt_id in route_edges:
        if src_id in node_dict and tgt_id in node_dict:
            src = node_dict[src_id]
            tgt = node_dict[tgt_id]

            fig.add_trace(go.Scattergeo(
                lon=[src["lon"], tgt["lon"]], lat=[src["lat"], tgt["lat"]],
                mode="lines", line=dict(width=8, color="rgba(0, 255, 170, 0.15)"),
                hoverinfo="skip"
            ))
            fig.add_trace(go.Scattergeo(
                lon=[src["lon"], tgt["lon"]], lat=[src["lat"], tgt["lat"]],
                mode="lines", line=dict(width=4, color="rgba(0, 255, 170, 0.4)"),
                hoverinfo="skip"
            ))
            fig.add_trace(go.Scattergeo(
                lon=[src["lon"], tgt["lon"]], lat=[src["lat"], tgt["lat"]],
                mode="lines", line=dict(width=1.5, color="#00FFAA"),
                hoverinfo="skip"
            ))

            for fraction in [0.25, 0.5, 0.75]:
                ais_lats.append(src["lat"] + (tgt["lat"] - src["lat"]) * fraction)
                ais_lons.append(src["lon"] + (tgt["lon"] - src["lon"]) * fraction)
                ais_text.append(f"Live AIS Tanker Convoy<br>Destination: {tgt['name']}")

    # 3. Add Simulated AIS Vessel Tracking
    if ais_lats:
        fig.add_trace(go.Scattergeo(
            lon=ais_lons, lat=ais_lats, mode="markers",
            marker=dict(size=6, color="#00FFAA", symbol="triangle-up", line=dict(width=1, color="black")),
            hoverinfo="text", hovertext=ais_text
        ))

    # 4. Plot Nodes with Dynamic Health/Starvation States
    lats, lons, texts, colors, sizes, symbols = [], [], [], [], [], []
    starving_refineries = inventory_result.get("affected_dependents", []) if inventory_result else []

    for node_id, node in node_dict.items():
        lats.append(node["lat"])
        lons.append(node["lon"])
        node_type = node["type"].replace("_", " ").title()
        base_text = f"<b>{node['name']}</b> ({node_type})<br>Max Cap: {node['capacity_mmbpd']} MMbpd"

        if node["type"] == "strategic_reserve":
            colors.append("#A855F7"); sizes.append(14); symbols.append("square")
        elif node["type"] == "refinery":
            colors.append("#F97316"); sizes.append(12); symbols.append("circle")
        elif node["type"] == "maritime_corridor":
            colors.append("#38BDF8"); sizes.append(8); symbols.append("circle-open")
        else:
            colors.append("dodgerblue"); sizes.append(10); symbols.append("circle")

        if node_id in active_ids:
            colors[-1] = "#00FFAA"
            sizes[-1] = max(sizes[-1], 16)

        if node_id in disrupted_ids:
            colors[-1] = "#EF4444"
            sizes[-1] = 22
            symbols[-1] = "x"
            base_text = f"🚨 <b>OFFLINE: {node['name']}</b><br>Severe Geopolitical Disruption"

        if node["name"] in starving_refineries:
            colors[-1] = "#FFD166"
            sizes[-1] = 22
            symbols[-1] = "diamond"
            base_text = f"⚠️ <b>STARVATION RISK: {node['name']}</b><br>Downstream Supply Deficit Detected!"

        texts.append(base_text)

    fig.add_trace(go.Scattergeo(
        lon=lons, lat=lats, hovertext=texts, mode="markers",
        marker=dict(size=sizes, color=colors, symbol=symbols, line=dict(width=1.5, color="#E5E7EB"))
    ))

    fig.update_layout(
        title_text="Live Global Procurement Routing", showlegend=False,
        geo=dict(
            projection_type="natural earth", showland=True,
            landcolor="rgb(30, 30, 30)", countrycolor="rgb(75, 85, 99)", coastlinecolor="rgb(75, 85, 99)",
            showocean=True, oceancolor="rgb(10, 14, 23)", bgcolor="rgba(0,0,0,0)",
            lataxis=dict(range=[-40, 65]), lonaxis=dict(range=[-110, 120])
        ),
        paper_bgcolor="#0A0E17", plot_bgcolor="#0A0E17", font=dict(color="#E5E7EB"),
        margin={"r": 0, "t": 40, "l": 0, "b": 0}
    )
    return fig
