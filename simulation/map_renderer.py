import json
import math
from pathlib import Path
import plotly.graph_objects as go
import streamlit as st
import datetime
from simulation.data_loader import get_cached_graph_data


def load_graph_data():
    """Retrieves supply chain graph structure from RAM cache."""
    return get_cached_graph_data()

def _haversine(lat1, lon1, lat2, lon2):
    """Calculates geospatial distance between two points in km."""
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    a = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))

def _resolve_route_edges(active_routes, node_dict):
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
            source = route.get("Source", "")
            if source and "russian" in source.lower():
                route_edges.extend([(8, 5), (5, target_id)])
            elif source and "west africa" in source.lower():
                route_edges.extend([(2, 5), (5, target_id)])
            elif source and "us gulf coast" in source.lower():
                route_edges.extend([(1, 6), (6, target_id)])
                
    return route_edges

def generate_geospatial_twin(impact_data, active_routes, inventory_result=None):
    """Generates an interactive Plotly map with concentric impact radii and Space-Time AIS tracking."""
    graph_data = load_graph_data()
    node_dict = {node["id"]: node for node in graph_data["nodes"]}
    disrupted_ids = set(impact_data.get("disrupted_nodes", []))
    active_ids = set(impact_data.get("base_nodes", []))
    severity = impact_data.get("calculated_severity", 5)
    
    route_edges = _resolve_route_edges(active_routes, node_dict)
    for _, target_id in route_edges:
        active_ids.add(target_id)
        
    fig = go.Figure()

    # --- 1. GIE: CONCENTRIC CONTAGION RADII (Spatial Econometrics) ---
    # We draw these first so they sit beneath the network lines
    for node_id in disrupted_ids:
        if node_id in node_dict:
            node = node_dict[node_id]
            # Outer Ring: Secondary Economic Spillover Zone
            fig.add_trace(go.Scattergeo(
                lon=[node["lon"]], lat=[node["lat"]],
                mode="markers",
                marker=dict(size=severity * 15, color="rgba(239, 68, 68, 0.08)", line=dict(width=1, color="rgba(239, 68, 68, 0.3)")),
                hoverinfo="text", 
                hovertext=f"<b>Secondary Contagion Zone</b><br>Radius: ~{severity * 150} km<br>High risk of supply chain spillover effects."
            ))
            # Inner Ring: Primary Disruption Epicenter
            fig.add_trace(go.Scattergeo(
                lon=[node["lon"]], lat=[node["lat"]],
                mode="markers",
                marker=dict(size=severity * 6, color="rgba(239, 68, 68, 0.25)", line=dict(width=2, color="rgba(239, 68, 68, 0.8)")),
                hoverinfo="text", 
                hovertext=f"<b>Primary Epicenter: {node['name']}</b><br>Immediate operational blackout."
            ))

    # --- 2. BASE NETWORK ROUTING ---
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

    # --- 3. NEON ACTIVE CORRIDORS & SPACE-TIME AIS TRACKING ---
    ais_lats, ais_lons, ais_text = [], [], []
    current_time = datetime.datetime.now(datetime.timezone.utc)
    
    for src_id, tgt_id in route_edges:
        if src_id in node_dict and tgt_id in node_dict:
            src = node_dict[src_id]
            tgt = node_dict[tgt_id]
            
            # Neon Bloom Effect
            fig.add_trace(go.Scattergeo(lon=[src["lon"], tgt["lon"]], lat=[src["lat"], tgt["lat"]], mode="lines", line=dict(width=8, color="rgba(0, 255, 170, 0.15)"), hoverinfo="skip"))
            fig.add_trace(go.Scattergeo(lon=[src["lon"], tgt["lon"]], lat=[src["lat"], tgt["lat"]], mode="lines", line=dict(width=4, color="rgba(0, 255, 170, 0.4)"), hoverinfo="skip"))
            fig.add_trace(go.Scattergeo(lon=[src["lon"], tgt["lon"]], lat=[src["lat"], tgt["lat"]], mode="lines", line=dict(width=1.5, color="#00FFAA"), hoverinfo="skip"))

            # Calculate total distance for temporal velocity mapping
            total_dist_km = _haversine(src["lat"], src["lon"], tgt["lat"], tgt["lon"])
            avg_vessel_speed_kmh = 25.0 # Average tanker speed ~13.5 knots
            
            # Space-Time Connection: Interpolate vessels along the route with precise ETAs
            for fraction in [0.25, 0.5, 0.75]:
                ship_lat = src["lat"] + (tgt["lat"] - src["lat"]) * fraction
                ship_lon = src["lon"] + (tgt["lon"] - src["lon"]) * fraction
                
                remaining_dist_km = total_dist_km * (1.0 - fraction)
                hours_to_arrival = remaining_dist_km / avg_vessel_speed_kmh
                eta = current_time + datetime.timedelta(hours=hours_to_arrival)
                
                ais_lats.append(ship_lat)
                ais_lons.append(ship_lon)
                ais_text.append(
                    f"🚢 <b>Live AIS Tanker Convoy</b><br>"
                    f"Destination: {tgt['name']}<br>"
                    f"Remaining Distance: {int(remaining_dist_km):,} km<br>"
                    f"<b>ETA (UTC):</b> {eta.strftime('%Y-%m-%d %H:%M')}"
                )

    if ais_lats:
        fig.add_trace(go.Scattergeo(
            lon=ais_lons, lat=ais_lats, mode="markers",
            marker=dict(size=7, color="#00FFAA", symbol="triangle-up", line=dict(width=1, color="black")),
            hoverinfo="text", hovertext=ais_text
        ))

    # --- 4. ASSET HEALTH & STARVATION TRACKING ---
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
            colors[-1] = "#00FFAA"; sizes[-1] = max(sizes[-1], 16)
            
        if node_id in disrupted_ids:
            colors[-1] = "#EF4444"; sizes[-1] = 22; symbols[-1] = "x"
            base_text = f"🚨 <b>OFFLINE: {node['name']}</b><br>Severe Geopolitical Disruption"

        if node["name"] in starving_refineries:
            colors[-1] = "#FFD166"; sizes[-1] = 22; symbols[-1] = "diamond"
            base_text = f"⚠️ <b>STARVATION RISK: {node['name']}</b><br>Downstream Supply Deficit Detected!"

        texts.append(base_text)

    fig.add_trace(go.Scattergeo(
        lon=lons, lat=lats, hovertext=texts, mode="markers",
        marker=dict(size=sizes, color=colors, symbol=symbols, line=dict(width=1.5, color="#E5E7EB"))
    ))

    # --- 5. ENTERPRISE UI LAYOUT ---
    fig.update_layout(
        title_text="Live Space-Time Geospatial Procurement Routing", showlegend=False,
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
