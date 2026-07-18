import math
import random
import datetime
import plotly.graph_objects as go
import searoute
from typing import Dict, Any, List
from simulation.data_loader import get_cached_graph_data


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance in km."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    return 2 * R * math.asin(math.sqrt(a))

def _get_maritime_route(lat1: float, lon1: float, lat2: float, lon2: float):
    """Uses the searoute library to calculate water-only maritime paths."""
    try:
        # searoute takes [lon, lat] pairs
        route = searoute.searoute([lon1, lat1], [lon2, lat2])
        coords = route["geometry"]["coordinates"]
        lons = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        return lons, lats
    except Exception:
        # Fallback to straight line if routing fails
        return [lon1, lon2], [lat1, lat2]


# --- TERRESTRIAL PIPELINE WAYPOINTS ---
# Real-world Indian pipeline contours to avoid straight lines crossing arbitrary terrain.
# Modeled after the MPPL, PHBPL, and SMPL networks.
PIPELINE_WAYPOINTS = {
    (21, 24): [[23.83, 71.60], [26.44, 74.63], [26.91, 75.78]], # Mundra-Panipat Pipeline (MPPL)
    (22, 12): [[24.17, 72.43], [28.18, 76.61]], # Vadinar to Delhi NCR
    (4, 11): [[22.30, 70.80], [21.17, 72.83]], # Jamnagar to Mumbai
    (4, 28): [[22.30, 70.80], [21.17, 72.83], [20.90, 74.77]], # Jamnagar to Manmad
    (23, 9):  [[11.25, 75.78]], # Kochi to Mangalore (Coastal Pipeline)
    (23, 13): [[11.01, 76.95], [11.66, 78.14]], # Kochi to Bangalore
    (7, 29):  [[17.00, 81.80]], # Visakhapatnam to Kondapalli
    (26, 27): [[22.06, 88.06], [25.43, 86.13], [26.44, 80.33], [27.17, 78.00]], # Paradip to Delhi via Haldia/Barauni (PHBPL)
    (14, 19): [[31.08, 29.82]], # Sumed Pipeline to Med Coast (Sidi Kerir)
    
    # NEW: INSTC (Russia to Chabahar via Caspian Sea / Tehran)
    (8, 18): [[46.34, 48.03], [35.68, 51.38]],
    
    # NEW: IMEC Rail (Piraeus to UAE/Middle East via Haifa and Riyadh)
    (19, 3): [[32.81, 34.99], [24.71, 46.67]]
}

def _get_pipeline_route(src_id: int, tgt_id: int, src: dict, tgt: dict):
    """Generates authentic terrestrial pipeline paths using geographic waypoints."""
    # Check both forward and reverse directions
    waypoints = PIPELINE_WAYPOINTS.get((src_id, tgt_id))
    if not waypoints:
        reverse_waypoints = PIPELINE_WAYPOINTS.get((tgt_id, src_id))
        waypoints = list(reversed(reverse_waypoints)) if reverse_waypoints else []
            
    lons, lats = [src["lon"]], [src["lat"]]
    for wp_lat, wp_lon in waypoints:
        lons.append(wp_lon)
        lats.append(wp_lat)
        
    lons.append(tgt["lon"])
    lats.append(tgt["lat"])
    return lons, lats


def _calculate_cog(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates Course Over Ground (COG) bearing in degrees."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)
    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)
    return (math.degrees(math.atan2(y, x)) + 360) % 360

def _resolve_route_edges(active_routes: List[Dict[str, Any]], disrupted_ids: set) -> List[tuple]:
    """Maps logical procurement directives to explicit multi-hop geospatial graph edges."""
    route_edges = []
    is_baseline = len(disrupted_ids) == 0
    
    if is_baseline:
        # BASELINE STATE: Optimized Regional Sourcing
        # 1. Middle East supplies WEST Coast Ports ONLY (Mundra, Vadinar)
        route_edges.extend([(3, 21), (3, 22)]) 
        
        # 2. Russian Far East supplies EAST Coast Ports via Eastern Maritime Corridor (Vladivostok -> Malacca -> East Coast)
        route_edges.extend([(16, 10), (10, 17), (10, 25), (10, 30)])
        
        # 3. Ports to Domestic Refineries via Pipeline
        route_edges.extend([(21, 4), (22, 4), (21, 24), (30, 7), (25, 26)])
        
        # 4. Global imports via Suez route to the West Coast
        route_edges.extend([(8, 15), (15, 6), (6, 21), (1, 6), (6, 22)])
        
        return list(set(route_edges))
        
    # DISRUPTED STATE: Trace explicit paths based on active agentic routes
    for route in active_routes:
        corridor = route.get("Corridor", "").lower()
        
        # Primary Cape of Good Hope Bypass (to West Coast)
        if "cape of good hope" in corridor:
            route_edges.extend([(1, 5), (2, 5), (8, 5), (5, 21), (21, 4)])
        
        # Primary Suez Routing (to West Coast)
        elif "suez" in corridor and 6 not in disrupted_ids:
            route_edges.extend([(1, 6), (8, 15), (15, 6), (6, 21), (21, 4)])
            
        # Alternative: Eastern Maritime Corridor (to East Coast)
        elif "eastern maritime" in corridor or "vladivostok" in corridor:
            route_edges.extend([(16, 10), (10, 17), (10, 25), (10, 30), (30, 7), (25, 26)])
            
        # Alternative: INSTC Rail/Sea Corridor
        elif "instc" in corridor or "chabahar" in corridor:
            route_edges.extend([(8, 18), (18, 21), (21, 4)])
            
        # NEW Alternative: IMEC (India-Middle East-Europe Economic Corridor)
        elif "imec" in corridor:
            # Urals(8) -> Piraeus(19) -> Middle East Rail(3) -> Mundra(21) -> Jamnagar(4)
            route_edges.extend([(8, 19), (19, 3), (3, 21), (21, 4)])
            
        # Alternative: Sumed Pipeline
        elif "sumed" in corridor:
            route_edges.extend([(3, 6), (6, 14), (14, 19)])
        
        # Spot Market Hedge (USGC)
        if "usgc" in corridor or "us gulf" in corridor:
            if 6 not in disrupted_ids:
                route_edges.extend([(1, 6), (6, 21), (21, 4)])
            else:
                route_edges.extend([(1, 5), (5, 21), (21, 4)])
                
    # Always maintain Middle East fallback to West Coast if Hormuz (3) is not blocked
    if 3 not in disrupted_ids:
        route_edges.extend([(3, 21), (3, 22), (21, 4), (22, 4)])
        
    # NEW: Always maintain Russian Far East to East Coast if Malacca (10) is not blocked
    if 10 not in disrupted_ids:
        route_edges.extend([(16, 10), (10, 17), (10, 25), (10, 30), (30, 7), (25, 26)])
        
    return list(set(route_edges))

def generate_live_ais_map(impact_data: Dict[str, Any], active_routes: List[Dict[str, Any]], inventory_result: Dict[str, Any] = None, live_vessels: Dict[str, Any] = None) -> go.Figure:
    """Renders interactive GEOINT Map with multi-hop route resolution."""
    graph_data = get_cached_graph_data()
    node_dict = {n["id"]: n for n in graph_data["nodes"]}
    disrupted_ids = set(impact_data.get("disrupted_nodes", []))
    active_ids = set(impact_data.get("base_nodes", []))
    severity = impact_data.get("calculated_severity", 5)
    
    # 1. Resolve logical routes into explicit physical edges
    resolved_edges = _resolve_route_edges(active_routes, disrupted_ids)
    
    fig = go.Figure()

    # --- 1. GIE: CONCENTRIC CONTAGION RADII ---
    for node_id in disrupted_ids:
        if node_id in node_dict:
            node = node_dict[node_id]
            fig.add_trace(go.Scattergeo(lon=[node["lon"]], lat=[node["lat"]], mode="markers",
                marker=dict(size=severity * 15, color="rgba(239, 68, 68, 0.08)", line=dict(width=1, color="rgba(239, 68, 68, 0.3)")),
                hoverinfo="text", hovertext=f"<b>Secondary Contagion Zone</b><br>Radius: ~{severity * 150} km", showlegend=False
            ))
            fig.add_trace(go.Scattergeo(lon=[node["lon"]], lat=[node["lat"]], mode="markers",
                marker=dict(size=severity * 6, color="rgba(239, 68, 68, 0.25)", line=dict(width=2, color="rgba(239, 68, 68, 0.8)")),
                hoverinfo="text", hovertext=f"<b>Primary Epicenter: {node['name']}</b><br>Immediate operational blackout.", showlegend=False
            ))

    # --- 2. BASE GRAPH CONNECTIONS & INFRASTRUCTURE ---
    for edge in graph_data.get("edges", []):
        src = node_dict.get(edge["source"])
        tgt = node_dict.get(edge["target"])
        if not src or not tgt: continue
        
        is_pipeline = edge.get("type") in ["pipeline", "terrestrial_pipeline", "terrestrial_rail"]
        line_color = "rgba(168, 85, 247, 0.4)" if is_pipeline else "rgba(100, 116, 139, 0.25)"
        line_width = 2 if is_pipeline else 1
        line_dash = "solid" if is_pipeline else "dot"
        
        if edge["source"] in disrupted_ids or edge["target"] in disrupted_ids:
            line_color = "rgba(239, 68, 68, 0.7)"
            line_width = 3
            line_dash = "dash"
            
        # GEOINT ROUTING: Use Searoute for oceans, Waypoints for terrestrial pipelines
        if is_pipeline:
            # Use actual pipeline contours instead of straight lines
            route_lons, route_lats = _get_pipeline_route(edge["source"], edge["target"], src, tgt)
        else:
            route_lons, route_lats = _get_maritime_route(src["lat"], src["lon"], tgt["lat"], tgt["lon"])
            
        fig.add_trace(go.Scattergeo(lon=route_lons, lat=route_lats, mode="lines",
            line=dict(width=line_width, color=line_color, dash=line_dash), hoverinfo="skip", showlegend=False
        ))

    # --- 3. LIVE AIS TRACKING MARKERS & NEON CORRIDORS ---
    ais_lats, ais_lons, ais_tooltips, ais_colors, ais_sizes = [], [], [], [], []
    current_utc = datetime.datetime.now(datetime.timezone.utc)

    # 3A. Highlight the resolved multi-hop paths in Neon Green
    for (src_id, tgt_id) in resolved_edges:
        if src_id in node_dict and tgt_id in node_dict:
            src, tgt = node_dict[src_id], node_dict[tgt_id]
            active_ids.add(src_id)
            active_ids.add(tgt_id)
            
            # Make the pipeline check bidirectional to prevent searoute misfires
            is_pipeline = any(
                (e["source"] == src_id and e["target"] == tgt_id or e["source"] == tgt_id and e["target"] == src_id) 
                and ("pipeline" in e.get("type", "") or "rail" in e.get("type", "")) 
                for e in graph_data.get("edges", [])
            )
            
            if is_pipeline:
                route_lons, route_lats = _get_pipeline_route(src_id, tgt_id, src, tgt)
            else:
                route_lons, route_lats = _get_maritime_route(src["lat"], src["lon"], tgt["lat"], tgt["lon"])
            
            fig.add_trace(go.Scattergeo(
                lon=route_lons, lat=route_lats,
                mode="lines", line=dict(width=2.5, color="#00FFAA"), hoverinfo="skip", showlegend=False
            ))
            
            # Place AIS ships exactly on the maritime path
            if not is_pipeline and not live_vessels:
                total_dist = _haversine_km(src["lat"], src["lon"], tgt["lat"], tgt["lon"])
                cog_angle = _calculate_cog(src["lat"], src["lon"], tgt["lat"], tgt["lon"])

                for frac in [0.25, 0.75]:
                    # Pick a coordinate from the actual water route array
                    point_index = int(len(route_lons) * frac)
                    if point_index >= len(route_lons): point_index = -1
                    
                    vessel_lon = route_lons[point_index] + random.uniform(-0.1, 0.1)
                    vessel_lat = route_lats[point_index] + random.uniform(-0.1, 0.1)
                    
                    rem_dist = total_dist * (1.0 - frac)
                    sog_knots = round(random.uniform(12.2, 14.8), 1)
                    eta_utc = current_utc + datetime.timedelta(hours=(rem_dist / (sog_knots * 1.852)))
                    
                    is_anomaly = src_id in disrupted_ids or tgt_id in disrupted_ids
                    color = "#EF4444" if is_anomaly else "#00FFAA"
                    status = "⚠️ Transponder Gap" if is_anomaly else "Under Way Using Engine"
                    
                    ais_lats.append(vessel_lat)
                    ais_lons.append(vessel_lon)
                    ais_colors.append(color)
                    ais_sizes.append(10 if is_anomaly else 8)
                    ais_tooltips.append(
                        f"🚢 <b>LIVE AIS TARGET (SIMULATED)</b><br><b>Status:</b> {status}<br>"
                        f"<b>SOG (Speed):</b> {sog_knots} kts | <b>COG (Course):</b> {cog_angle:.0f}°<br>"
                        f"<b>Bound For:</b> {tgt['name']}<br><b>UTC ETA:</b> {eta_utc.strftime('%Y-%m-%d %H:%M')}"
                    )

    if live_vessels:
        # Plot real-time AIS feed targets
        for mmsi, ship in live_vessels.items():
            ship_type = ship.get("type", 0)
            is_tanker = 80 <= ship_type <= 89
            name_upper = ship.get("name", "").upper()
            is_tanker_name = any(k in name_upper for k in ["TANKER", "VLCC", "SUEZMAX", "CRUDE", "OIL", "CARRIER", "PETRO"])
            
            # Filter: Show crude oil tankers only
            if not is_tanker and not is_tanker_name:
                continue

            vessel_lat = ship["lat"]
            vessel_lon = ship["lon"]
            sog_knots = ship.get("sog", 0.0)
            cog_angle = ship.get("cog", 0.0)
            ship_name = ship.get("name", "Unknown Tanker")
            
            # Check for anomalies near disrupted chokepoint zones
            is_anomaly = False
            for dis_id in disrupted_ids:
                if dis_id in node_dict:
                    dis_node = node_dict[dis_id]
                    dist_to_dis = _haversine_km(vessel_lat, vessel_lon, dis_node["lat"], dis_node["lon"])
                    if dist_to_dis < 350:
                        is_anomaly = True
                        break
                        
            color = "#EF4444" if is_anomaly else "#00FFAA"
            nav_status = "⚠️ Transponder Gap / Spoofing Risk" if is_anomaly else "Under Way Using Engine"
            
            ais_lats.append(vessel_lat)
            ais_lons.append(vessel_lon)
            ais_colors.append(color)
            ais_sizes.append(10 if is_anomaly else 8)
            
            ais_tooltips.append(
                f"🚢 <b>REAL AIS TARGET (LIVE)</b><br>"
                f"<b>Name:</b> {ship_name}<br>"
                f"<b>MMSI:</b> {mmsi}<br>"
                f"<b>Status:</b> {nav_status}<br>"
                f"<b>SOG (Speed):</b> {sog_knots} kts | <b>COG (Course):</b> {cog_angle:.0f}°<br>"
                f"<b>Lat/Lon:</b> {vessel_lat:.4f}, {vessel_lon:.4f}<br>"
                f"<b>Last Ping:</b> {ship.get('last_updated', current_utc).strftime('%H:%M:%S')} UTC"
            )

    # Render Live Vessel Plot Layer
    if ais_lats:
        fig.add_trace(go.Scattergeo(lon=ais_lons, lat=ais_lats, mode="markers",
            marker=dict(size=ais_sizes, color=ais_colors, symbol="triangle-up", line=dict(width=1, color="#0A0E17")),
            hoverinfo="text", hovertext=ais_tooltips, name="Live AIS Traffic"
        ))

    # --- 4. PORTS, REFINERIES & TERMINAL NODES ---
    node_lats, node_lons, node_texts, node_colors, node_symbols, node_sizes = [], [], [], [], [], []
    starving_refineries = inventory_result.get("affected_dependents", []) if inventory_result else []
    
    for route in active_routes:
        corridor_name = route.get("Corridor", "").lower()
        src_id = 3 if "hormuz" in corridor_name else (8 if "russian" in corridor_name else 1)
        tgt_id = 7 if "visakh" in corridor_name else 4
        active_ids.add(src_id)
        active_ids.add(tgt_id)

    for node_id, node in node_dict.items():
        node_lats.append(node["lat"])
        node_lons.append(node["lon"])
        
        status_label = "🚨 DISRUPTED" if node_id in disrupted_ids else "🟢 OPERATIONAL"
        node_type = node["type"].replace("_", " ").title()
        base_text = f"<b>{node['name']}</b> ({node_type})<br>Status: {status_label}"
        
        size = 11
        if node_id in disrupted_ids:
            color = "#EF4444"
            symbol = "x"
            size = 18
            base_text = f"🚨 <b>OFFLINE: {node['name']}</b><br>Severe Geopolitical Disruption"
        elif node["name"] in starving_refineries:
            color = "#FFD166"
            symbol = "diamond"
            size = 18
            base_text = f"⚠️ <b>STARVATION RISK: {node['name']}</b><br>Downstream Supply Deficit Detected!"
        elif node["type"] == "refinery":
            color = "#F97316"
            symbol = "circle"
        elif node["type"] == "strategic_reserve":
            color = "#A855F7"
            symbol = "square"
            size = 13
        elif node["type"] == "port":
            color = "#38BDF8"
            symbol = "hexagon"
            size = 13
        else:
            color = "#3B82F6"
            symbol = "star"

        if node_id in active_ids and node_id not in disrupted_ids:
            color = "#00FFAA"
            size = max(size, 15)
            
        node_colors.append(color)
        node_symbols.append(symbol)
        node_sizes.append(size)
        node_texts.append(base_text)

    fig.add_trace(go.Scattergeo(
        lon=node_lons, lat=node_lats,
        mode="markers",
        marker=dict(size=node_sizes, color=node_colors, symbol=node_symbols, line=dict(width=1.5, color="#FFFFFF")),
        hoverinfo="text",
        hovertext=node_texts,
        showlegend=False
    ))

    # Dark Mode GEOINT Dashboard Map Layout
    fig.update_layout(
        title=dict(text="🛰️ Live AIS Maritime Vector Tracking & Digital Twin Network", font=dict(color="#E5E7EB", size=16)),
        showlegend=True,
        geo=dict(
            projection_type="natural earth",
            showland=True, landcolor="#1E293B",
            showocean=True, oceancolor="#0B0F19",
            showcountries=True, countrycolor="#334155",
            showcoastlines=True, coastlinecolor="#475569",
            bgcolor="rgba(0,0,0,0)",
            lataxis=dict(range=[-35, 65]),
            lonaxis=dict(range=[-100, 125])
        ),
        paper_bgcolor="#0A0E17",
        plot_bgcolor="#0A0E17",
        font=dict(color="#E5E7EB"),
        margin=dict(r=0, t=40, l=0, b=0),
        height=950
    )
    return fig

# Compatibility wrapper for legacy code importing the old name
generate_geospatial_twin = generate_live_ais_map
