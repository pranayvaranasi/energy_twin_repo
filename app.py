import streamlit as st
from simulation.mcts_engine import run_mcts_scenario
from routing.wrapper import get_optimized_corridors

st.set_page_config(page_title="Supply Chain Digital Twin", layout="wide")

st.title("🌍 Energy Supply Chain Resilience Twin")
st.markdown("Dynamic MCTS scenario modelling & adaptive procurement routing.")

# --- SIDEBAR: DISRUPTION MODELLER ---
st.sidebar.header("Geopolitical Risk Modeller")
st.sidebar.markdown("Inject a disruption signal to test supply chain resilience.")

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
    st.markdown("Top alternative logistics corridors identified by the high-speed routing backend.")

    st.dataframe(routes, use_container_width=True)
else:
    st.info("👈 Awaiting disruption trigger from the control panel.")
