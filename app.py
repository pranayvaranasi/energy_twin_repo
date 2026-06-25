import streamlit as st
import time
from simulation.map_renderer import generate_geospatial_twin
from simulation.mcts_engine import run_mcts_scenario
from routing.wrapper import get_optimized_corridors
from simulation.watcher_agent import ingest_and_classify_news

st.set_page_config(page_title="Supply Chain Digital Twin", layout="wide")

st.title("🌍 Energy Supply Chain Resilience Twin")
st.markdown("Dynamic MCTS scenario modelling & adaptive procurement routing.")

# --- SIDEBAR: DISRUPTION MODELLER ---
st.sidebar.header("Geopolitical Risk Modeller")
st.sidebar.markdown("Inject a disruption signal manually, or let the NLP Watcher scan live feeds.")

# Track if autonomous mode was triggered
autonomous_triggered = False
disruption_event = None
severity = None

# NEW: Autonomous AI Mode
st.sidebar.subheader("📡 Autonomous Mode")
if st.sidebar.button("Fetch Live Intelligence Signal"):
    autonomous_triggered = True
    with st.spinner("NLP Agent scanning global news feeds..."):
        time.sleep(1)  # Simulate API latency
        signal_data = ingest_and_classify_news()
        
        st.sidebar.warning(f"**Latest Intel:** {signal_data['headline']}")
        st.sidebar.info(f"**AI Classification:** {signal_data['trigger_event']}\n\n**Severity:** {signal_data['calculated_severity']}/10")
        
        # Override manual settings with AI detected settings
        disruption_event = signal_data['trigger_event']
        severity = signal_data['calculated_severity']

if not autonomous_triggered:
    # Existing Manual Mode
    st.sidebar.subheader("⚙️ Manual Mode")
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

if st.sidebar.button("Simulate & Optimize", type="primary"):
    with st.spinner("Running MCTS to predict cascading economic impacts..."):
        impact_data = run_mcts_scenario(disruption_event, severity)

    with st.spinner("Executing C++ graph traversal for alternative corridors..."):
        routes = get_optimized_corridors(impact_data)

    st.success("Simulation Complete. Adaptive Procurement Protocol Engaged.")
    st.divider()

    st.subheader(f"Scenario Impact: {disruption_event}")
    col1, col2, col3 = st.columns(3)

    col1.metric(
        label="Predicted Brent Crude Spike",
        value=impact_data["brent_spike"],
        delta=impact_data["brent_delta"],
        delta_color="inverse",
    )
    col2.metric(
        label="Strategic Petroleum Reserve Cover",
        value=impact_data["spr_cover"],
        delta=impact_data["spr_delta"],
        delta_color="inverse",
    )
    col3.metric(
        label="Refinery Run Rate",
        value=impact_data["run_rate"],
        delta=impact_data["run_rate_delta"],
        delta_color="inverse",
    )

    st.divider()
    st.subheader("Adaptive Procurement Orchestrator")
    st.markdown("Dynamic corridor identification bypassing disrupted geopolitical zones.")

    with st.container():
        live_map_fig = generate_geospatial_twin(impact_data, routes)
        st.plotly_chart(live_map_fig, use_container_width=True)

    st.dataframe(routes, use_container_width=True)
else:
    st.info("👈 Awaiting disruption trigger from the control panel.")
