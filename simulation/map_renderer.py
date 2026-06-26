import json
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import streamlit as st


# Cache the disk I/O operation so it only runs once per session
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
            route_edges.extend([(2, 5), (5, target_id)])
        elif "suez" in corridor or "red sea" in corridor:
            route_edges.extend([(1, 6), (6, target_id)])
        elif "pipeline" in corridor or "domestic" in corridor:
            route_edges.extend([(3, 4)])
        else:
            # Fallback: highlight all active source/target combinations
            source = route.get("Source")
            if source and "west africa" in source.lower():
                route_edges.extend([(2, 5), (5, target_id)])
            elif source and "us gulf coast" in source.lower():
                route_edges.extend([(1, 6), (6, target_id)])
    return route_edges


def generate_geospatial_twin(impact_data, active_routes):
    """Generates an interactive Plotly map of the global supply chain."""
    graph_data = load_graph_data()

    node_dict = {node["id"]: node for node in graph_data["nodes"]}
    disrupted_ids = set(impact_data.get("disrupted_nodes", []))
    active_ids = set(impact_data.get("base_nodes", []))
    route_edges = _resolve_route_edges(active_routes, node_dict)
    for _, target_id in route_edges:
        active_ids.add(target_id)

    fig = go.Figure()

    # Draw all default supply lines (faded)
    for edge in graph_data["edges"]:
        src = node_dict[edge["source"]]
        tgt = node_dict[edge["target"]]
        line_color = "rgba(150, 150, 150, 0.35)"
        line_width = 1
        dash = "solid"
        if edge["source"] in disrupted_ids or edge["target"] in disrupted_ids:
            line_color = "rgba(220, 20, 60, 0.7)"
            line_width = 2
            dash = "dash"

        fig.add_trace(
            go.Scattergeo(
                lon=[src["lon"], tgt["lon"]],
                lat=[src["lat"], tgt["lat"]],
                mode="lines",
                line=dict(width=line_width, color=line_color, dash=dash),
                hoverinfo="skip",
            )
        )

    # Highlight active route corridors in green
    for src_id, tgt_id in route_edges:
        if src_id in node_dict and tgt_id in node_dict:
            src = node_dict[src_id]
            tgt = node_dict[tgt_id]
            fig.add_trace(
                go.Scattergeo(
                    lon=[src["lon"], tgt["lon"]],
                    lat=[src["lat"], tgt["lat"]],
                    mode="lines",
                    line=dict(width=4, color="#00FFAA"),
                    hoverinfo="skip",
                )
            )

    # NEW: Add simulated AIS Vessel Tracking points along active corridors
    ais_lats, ais_lons, ais_text = [], [], []
    for src_id, tgt_id in route_edges:
        if src_id in node_dict and tgt_id in node_dict:
            src = node_dict[src_id]
            tgt = node_dict[tgt_id]
            for fraction in np.linspace(0.1, 0.9, 5):
                ais_lats.append(
                    src["lat"] + (tgt["lat"] - src["lat"]) * fraction + np.random.normal(0, 0.5)
                )
                ais_lons.append(
                    src["lon"] + (tgt["lon"] - src["lon"]) * fraction + np.random.normal(0, 0.5)
                )
                ais_text.append("Live AIS Telemetry (Simulated)")

    if ais_lats:
        fig.add_trace(
            go.Scattergeo(
                lon=ais_lons,
                lat=ais_lats,
                mode="markers",
                marker=dict(size=4, color="#FFD166", opacity=0.85, symbol="triangle-up"),
                hoverinfo="text",
                hovertext=ais_text,
            )
        )

    # Plot nodes (red if disrupted, green if active, blue otherwise)
    lats, lons, texts, colors, sizes = [], [], [], [], []
    for node_id, node in node_dict.items():
        lats.append(node["lat"])
        lons.append(node["lon"])
        texts.append(f"{node['name']} ({node['type']})")
        if node_id in disrupted_ids:
            colors.append("red")
            sizes.append(16)
        elif node_id in active_ids:
            colors.append("#00FFAA")
            sizes.append(14)
        else:
            colors.append("#38BDF8")
            sizes.append(10)

    fig.add_trace(
        go.Scattergeo(
            lon=lons,
            lat=lats,
            hovertext=texts,
            mode="markers",
            marker=dict(size=sizes, color=colors, line=dict(width=1, color="#E5E7EB")),
        )
    )

    fig.update_layout(
        title_text="Live Global Procurement Routing",
        showlegend=False,
        geo=dict(
            projection_type="natural earth",
            showland=True,
            landcolor="rgb(30, 30, 30)",
            countrycolor="rgb(75, 85, 99)",
            coastlinecolor="rgb(75, 85, 99)",
            showocean=True,
            oceancolor="rgb(10, 14, 23)",
            bgcolor="rgba(0,0,0,0)",
            lataxis=dict(range=[-40, 60]),
            lonaxis=dict(range=[-120, 120]),
        ),
        paper_bgcolor="#0A0E17",
        plot_bgcolor="#0A0E17",
        font=dict(color="#E5E7EB"),
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
    )

    return fig
