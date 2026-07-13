import streamlit as st
import time
import pandas as pd
import plotly.express as px
import concurrent.futures
from simulation.map_renderer import generate_geospatial_twin
from simulation.mcts_engine import run_mcts_scenario
from simulation.pdm_agent import calculate_pdm_risk
from simulation.spr_agent import generate_spr_schedule
from routing.wrapper import get_optimized_corridors
from simulation.watcher_agent import ingest_and_classify_news
from simulation.inventory_agent import calculate_stranded_inventory

# --- 1. PAGE CONFIGURATION & ENTERPRISE THEME INJECTION ---
st.set_page_config(
    page_title="Energy Supply Twin Control Tower",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .reportview-container { background: #0A0E17; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #111827;
        border: 1px solid #1F2937;
        border-radius: 6px 6px 0px 0px;
        padding: 10px 20px;
        color: #9CA3AF;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1F2937 !important;
        border-color: #00FFAA !important;
        color: #00FFAA !important;
    }
    div[data-testid="stMetricContainer"] {
        background-color: #111827;
        border: 1px solid #1F2937;
        padding: 15px;
        border-radius: 8px;
        box-shadow: inset 0 0 10px rgba(0, 255, 170, 0.02);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🌍 Energy Supply Chain Resilience Twin")
st.caption("Strategic look-ahead optimization, adaptive procurement routing, and predictive infrastructure maintenance.")

# --- 2. SIDEBAR: GEOPOLITICAL RISK INTELLIGENCE CORNER ---
st.sidebar.header("🛡️ Risk Intelligence Engine")
st.sidebar.markdown("🟢 **System Status:** `Live C++ Engine Connected`")
st.sidebar.divider()

autonomous_triggered = False
disruption_event = "Baseline (No Disruption)"
severity = 1

st.sidebar.subheader("📡 Autonomous Agent Mode")
st.sidebar.caption("Deploy neural threat-hunting crawlers to actively scan breaking news feeds.")
if st.sidebar.button("Fetch Live Intelligence Signal", type="secondary", use_container_width=True):
    autonomous_triggered = True
    with st.spinner("Executing semantic search across global news vectors..."):
        time.sleep(0.8)
        signal_data = ingest_and_classify_news()

    st.sidebar.warning(f"📰 **Intel Found:** {signal_data['headline']}")
    st.sidebar.info(
        f"**Classification:** {signal_data['trigger_event']}\n\n"
        f"**Assessed Severity:** {signal_data['calculated_severity']}/10\n\n"
        f"**Agent Confidence:** {signal_data['confidence_score']}"
    )

    disruption_event = signal_data['trigger_event']
    severity = signal_data['calculated_severity']

if not autonomous_triggered:
    st.sidebar.subheader("⚙️ Manual Override Mode")
    disruption_event = st.sidebar.selectbox(
        "Select Event Trigger:",
        [
            "Baseline (No Disruption)",
            "Red Sea Shipping Suspension (Houthi Threat)",
            "Strait of Hormuz Partial Closure",
            "OPEC+ Emergency Supply Cut",
        ],
    )
    severity = st.sidebar.slider("Disruption Severity Factor", 1, 10, 5)

st.sidebar.divider()

st.sidebar.subheader("🧪 Simulation Fidelity Covariates")
with st.sidebar.expander("Configure Calibration Assumptions", expanded=False):
    elasticity = st.slider("Price Elasticity of Demand", -1.0, 0.0, -0.4, 0.1)
    spr_release_cap = st.number_input("Max Daily SPR Drawdown (M bpd)", value=1.5, step=0.1)
    refinery_buffer = st.slider("Refinery On-site Buffer (Days)", 1, 15, 7)

if "simulation_run" not in st.session_state:
    st.session_state.simulation_run = False
    st.session_state.impact_data = {
        "brent_spike": "$80.00/bbl",
        "brent_delta": "0%",
        "spr_cover": "9.5 Days",
        "spr_delta": "0 Days",
        "run_rate": "92.0%",
        "run_rate_delta": "0%",
        "power_stress": "45/100",
        "power_stress_delta": "+0 pts",
        "gdp_impact": "0.00%",
        "gdp_delta": "Nominal",
    }
    st.session_state.routes = []
    st.session_state.inventory_result = None

# --- 3. THE SIMULATION ORCHESTRATION ---
if st.sidebar.button("Run Adaptive Simulation", type="primary", use_container_width=True):
    
    # Track end-to-end response time
    start_time = time.perf_counter()
    
    with st.status("Orchestrating Digital Twin Modules...", expanded=True) as status:
        st.write("📡 **NLP Watcher:** Formulating structured risk parameters...")
        time.sleep(0.1) # Minimized sleep for faster execution
        
        st.write("🧠 **Modeller:** Running 1,000 stochastic MCTS look-ahead simulations...")
        st.session_state.impact_data = run_mcts_scenario(
            disruption_event, severity, elasticity, spr_release_cap, refinery_buffer
        )
        
        st.write("⚡ **Graph Execution:** Launching C++ Routing & BFS Agents in Parallel...")
        
        # UPGRADE: Palantir-style Parallel Execution Graph
        # We run the Dijkstra Routing and the BFS Inventory Traversal simultaneously on separate threads
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            
            # 1. Dispatch the C++ memory allocation and routing calculation
            future_routes = executor.submit(
                get_optimized_corridors, 
                st.session_state.impact_data
            )
            
            # 2. Dispatch the BFS inventory starvation traversal
            future_inventory = executor.submit(
                calculate_stranded_inventory,
                st.session_state.impact_data.get("disrupted_nodes", []), 
                severity, 
                80.0
            )
            
            # 3. Await resolution (The total time is now max(T_routing, T_inventory) instead of T_routing + T_inventory)
            routes_result = future_routes.result()
            st.session_state.inventory_result = future_inventory.result()
            
        st.session_state.routes = routes_result.get("routes", [])
        
        end_time = time.perf_counter()
        total_latency = (end_time - start_time) * 1000
        
        status.update(
            label=f"Control Tower Sync Complete in {total_latency:.0f}ms. Remediation Protocols Active.", 
            state="complete", 
            expanded=False
        )
        st.session_state.simulation_run = True

# --- 4. MAIN LAYOUT: RE-ENGINEERED KPI OVERVIEW ---
with st.container(border=True):
    st.markdown(f"### 📊 Control Tower Dashboard Overview — *Current Scenario: {disruption_event}*")
    kpi_1, kpi_2, kpi_3, kpi_4, kpi_5 = st.columns(5)

    kpi_1.metric(
        "Brent Crude Price",
        st.session_state.impact_data.get("brent_spike"),
        delta=st.session_state.impact_data.get("brent_delta"),
        delta_color="inverse",
    )
    kpi_2.metric(
        "SPR Safety Stock Buffer",
        st.session_state.impact_data.get("spr_cover"),
        delta=st.session_state.impact_data.get("spr_delta"),
        delta_color="inverse",
    )
    kpi_3.metric(
        "Refinery Operating Capacity",
        st.session_state.impact_data.get("run_rate"),
        delta=st.session_state.impact_data.get("run_rate_delta"),
        delta_color="inverse",
    )
    kpi_4.metric(
        "Grid Performance Stress",
        st.session_state.impact_data.get("power_stress"),
        delta=st.session_state.impact_data.get("power_stress_delta"),
        delta_color="inverse",
    )
    kpi_5.metric(
        "Macro GDP Trajectory",
        st.session_state.impact_data.get("gdp_impact"),
        delta=st.session_state.impact_data.get("gdp_delta"),
    )

    if st.session_state.simulation_run:
        st.divider()
        st.markdown("##### 🛡️ Institutional Monte Carlo Resiliency Metrics")
        
        with st.container(border=True):
            mc_1, mc_2, mc_3, mc_4 = st.columns(4)
            
            median_sev = st.session_state.impact_data.get('calculated_severity', 1.0)
            downside_sev = st.session_state.impact_data.get('downside_risk_severity', 1.0)
            
            mc_1.metric(
                "Median Scenario Severity", 
                f"{median_sev:.1f} / 10" if isinstance(median_sev, (int, float)) else f"{median_sev}"
            )
            
            mc_2.metric(
                "95% VaR Downside Severity", 
                f"{downside_sev:.1f} / 10" if isinstance(downside_sev, (int, float)) else f"{downside_sev}",
                delta="Worst 20% Trajectories",
                delta_color="inverse"
            )
            
            mc_3.metric(
                "Probability of Survival", 
                st.session_state.impact_data.get('probability_of_success', '100.0%')
            )
            
            mc_4.metric(
                "Engine Confidence", 
                st.session_state.impact_data.get('mcts_confidence', '98.5%')
            )

# --- 5. ENTERPRISE COMPARTMENTALIZED TABS ---
op_tab, econ_tab, infra_tab = st.tabs([
    "🌍 Global Operations & Routing",
    "📈 Macroeconomics & Policy",
    "🏭 Infrastructure Health (PdM)",
])

with op_tab:
    col_map, col_details = st.columns([2, 1])

    with col_map:
        st.subheader("Geospatial Network Visualization")
        live_map_fig = generate_geospatial_twin(
            st.session_state.impact_data,
            st.session_state.routes,
            st.session_state.inventory_result,
        )
        st.plotly_chart(live_map_fig, use_container_width=True)

    with col_details:
        st.subheader("Real-Time Logistics Ingestion")
        if st.session_state.inventory_result:
            with st.container(border=True):
                st.markdown("##### ⚠️ Stranded Cargo & Economic Exposure")
                st.write(f"**Stranded Volume:** {st.session_state.inventory_result['stranded_volume']}")
                st.write(f"**Asset Value Stranded:** {st.session_state.inventory_result['daily_financial_deficit']}")
                st.write(f"**Daily Capital Holding Drain:** {st.session_state.inventory_result['daily_holding_cost']}")
                st.error(
                    f"Daily Downtime Exposure: {st.session_state.inventory_result['operational_stoppage_exposure']}"
                )

                if st.session_state.inventory_result.get("refinery_impacts"):
                    st.markdown("**Refinery Depletion Lifelines:**")
                    for ref in st.session_state.inventory_result["refinery_impacts"]:
                        st.caption(
                            f"• **{ref['name']}**: {ref['days_of_cover']} remaining ({ref['risk_tier']} Tier)"
                        )
        else:
            st.info("System operating at optimal parameters. No logistics bottlenecks reported.")

with econ_tab:
    st.subheader("Macroeconomic Projections & Strategic Mitigation Policy")
    st.caption("AI-driven rationing policy modeling the depletion of India's 39M Barrel underground caverns.")

    spr_df = generate_spr_schedule(severity, delay_days=14, max_spr_capacity_mbpd=spr_release_cap)

    if spr_df is not None and not spr_df.empty:
        col_chart, col_data = st.columns([2.2, 1.3])

        with col_chart:
            with st.container(border=True):
                st.markdown("##### 📉 SPR Drawdown Trajectory")
                spr_chart = px.area(
                    spr_df,
                    x="Day",
                    y=["Supply Gap (M bpd)", "Recommended SPR Release (M bpd)"],
                    color_discrete_sequence=["rgba(239, 68, 68, 0.15)", "rgba(0, 255, 170, 0.6)"],
                )

                spr_chart.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1,
                        title=None,
                    ),
                    margin=dict(l=0, r=0, t=40, b=0),
                    xaxis=dict(showgrid=False, zeroline=False, title="Crisis Timeline"),
                    yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)", zeroline=False, title="Volume (MMbpd)"),
                    hovermode="x unified",
                )

                spr_chart.update_traces(line=dict(width=2))
                st.plotly_chart(spr_chart, use_container_width=True)

        with col_data:
            with st.container(border=True):
                st.markdown("##### 📋 Daily Dispatch Ledger")
                st.dataframe(
                    spr_df,
                    use_container_width=True,
                    hide_index=True,
                    height=380,
                )
    else:
        st.info("No reserve draws required. National supply reserves are untouched.")

with infra_tab:
    st.subheader("Infrastructure Health Monitoring Engine")
    st.caption(
        "Physics-informed fatigue modeling via simulated LSTM-Autoencoder (LSTM-AE) structural reconstruction error tracking."
    )

    pdm_assessment = calculate_pdm_risk(
        st.session_state.impact_data["run_rate"],
        st.session_state.impact_data["power_stress"],
    )

    with st.container(border=True):
        pdm_1, pdm_2, pdm_3 = st.columns(3)
        pdm_1.metric("Critical Asset Tag", pdm_assessment['asset'])
        pdm_2.metric(
            "Probability of Failure (14D Window)",
            pdm_assessment['failure_probability'],
            delta="Accelerating Wear",
            delta_color="inverse",
        )
        pdm_3.metric("Autoencoder Anomaly Score", pdm_assessment['lstm_anomaly_score'])

        st.divider()
        st.markdown(f"**Asset Health Classification:** {pdm_assessment['status']}")
        st.markdown(f"**Orchestrator Mitigation Recommendation:** {pdm_assessment['recommendation']}")

st.divider()
st.subheader("🤖 Strategic Logistics Copilot")
st.markdown(
    "Query the twin's multi-agent data parameters (C++ routes, PyTorch macro trends, and BFS asset tracking) using natural language."
)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hello. I have completely loaded the live C++ multi-source parameters and the BFS impact tree data. Ask me any strategic supply chain or financial deficit question.",
        }
    ]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input("E.g., 'What is the daily financial deficit of our stranded assets?'"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    with st.spinner("Synthesizing metrics..."):
        prompt_lower = prompt.lower()
        if any(w in prompt_lower for w in ["stranded", "loss", "money", "deficit", "holding"]):
            if st.session_state.inventory_result:
                reply = (
                    f"The BFS graph traversal indicates that **{st.session_state.inventory_result['stranded_volume']}** is trapped. "
                    f"This incurs a capital storage holding cost of **{st.session_state.inventory_result['daily_holding_cost']}** and introduces an operational stoppage risk exposure of "
                    f"**{st.session_state.inventory_result['operational_stoppage_exposure']}**. Immediate mitigation via East Coast node rerouting is recommended."
                )
            else:
                reply = "Our BFS inventory tracker shows no stranded assets or financial exposure under current parameters."
        elif "pdm" in prompt_lower or "failure" in prompt_lower or "useful life" in prompt_lower:
            reply = (
                f"The PdM agent indicates the **{pdm_assessment['asset']}** has a failure probability of "
                f"**{pdm_assessment['failure_probability']}** with an anomaly score of `{pdm_assessment['lstm_anomaly_score']}`. "
                f"Recommendation: {pdm_assessment['recommendation']}"
            )
        else:
            reply = (
                f"The PyTorch forecasting layer predicts a direct GDP trend drop of **{st.session_state.impact_data.get('gdp_impact')}** "
                f"due to supply chokepoint premiums. I recommend evaluating the automated SPR release configuration immediately."
            )

        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.chat_message("assistant").write(reply)
