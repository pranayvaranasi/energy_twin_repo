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

def test_trans_shipment_and_resilient_corridors():
    # 1. Test baseline: no disruptions.
    results_baseline = calculate_landed_economics("Jamnagar Refinery", [])
    
    # Locate Sumed Pipeline Bypass results for WTI Houston
    sumed_wti_baseline = [r for r in results_baseline if r["crude_grade"] == "WTI Houston" and r["logistics_corridor"] == "Sumed Pipeline Bypass (Egypt)"]
    assert len(sumed_wti_baseline) == 1
    # Landed cost calculation: 
    # base_price(81.20) + base_freight(1.85) + trans_shipment_fee(0.45) + demurrage(3.5 * 0.35 = 1.225) + compatibility(sulfur=0.0 + api_dev=8.0*0.40=3.20) = 87.925 -> 87.92
    assert sumed_wti_baseline[0]["landed_cost"] == 87.92

    # 2. Test Suez Canal disruption (node 6)
    results_disrupted = calculate_landed_economics("Jamnagar Refinery", [6])
    
    # Locate Sumed Pipeline Bypass results for WTI Houston under disruption
    sumed_wti_disrupted = [r for r in results_disrupted if r["crude_grade"] == "WTI Houston" and r["logistics_corridor"] == "Sumed Pipeline Bypass (Egypt)"]
    assert len(sumed_wti_disrupted) == 1
    # spot premium multiplier is 1.35.
    # base_freight = (1.85 * 1.35) + 0.45 - 1.50 = 1.4475
    # demurrage = 1.225, compatibility = 3.20.
    # landed_cost = 81.20 + 1.4475 + 1.225 + 3.20 = 87.0725 -> 87.07
    assert sumed_wti_disrupted[0]["landed_cost"] == 87.07

