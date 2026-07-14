from simulation.procurement_agent import calculate_landed_economics, generate_agentic_recommendations

def test_calculate_landed_economics():
    results = calculate_landed_economics("Jamnagar Refinery", [])
    assert len(results) > 0
    # verify fields in returned dicts
    first = results[0]
    assert "supplier" in first
    assert "crude_grade" in first
    assert "logistics_corridor" in first
    assert "landed_cost" in first
    assert "assay_fit_score" in first
    assert "executability_index" in first
    assert "port_delay" in first

def test_generate_agentic_recommendations():
    recommendation = generate_agentic_recommendations("Jamnagar Refinery", [])
    assert "matrix" in recommendation
    assert "brief" in recommendation
    brief = recommendation["brief"]
    assert "executive_summary" in brief
    assert "actionable_manifest" in brief
    assert len(brief["actionable_manifest"]) > 0
    first_item = brief["actionable_manifest"][0]
    assert "priority_rank" in first_item
    assert "supplier" in first_item
    assert "crude_grade" in first_item
    assert "corridor" in first_item
    assert "landed_cost_adjusted" in first_item
    assert "action_item" in first_item
    assert "urgency_window" in first_item
