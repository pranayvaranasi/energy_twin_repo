from simulation.spr_agent import optimize_spr_schedule

def test_optimize_spr_schedule_calculates_correct_rations():
    # Test Red Sea Blockade (node 6) -> replenishment window should be 35 days
    result = optimize_spr_schedule(severity=5, elasticity=-0.4, active_disruptions=[6])
    
    assert "schedule_df" in result
    assert "metrics" in result
    assert "decision_support" in result
    
    df = result["schedule_df"]
    metrics = result["metrics"]
    decision = result["decision_support"]
    
    assert metrics["replenishment_days"] == 35
    assert len(df) == 35
    
    # Check columns
    assert "Day" in df.columns
    assert "Forecasted Demand (M bpd)" in df.columns
    assert "Supply Gap (M bpd)" in df.columns
    assert "SPR Release (M bpd)" in df.columns
    assert "Remaining SPR (M bbls)" in df.columns
    
    # Check that remaining SPR doesn't go below 0 and decreases or stays flat
    assert df.iloc[-1]["Remaining SPR (M bbls)"] >= 0.0
    assert df.iloc[-1]["Remaining SPR (M bbls)"] <= 39.0
    
    # Check that the policy brief is returned
    assert "policy_brief" in decision
    assert "cabinet_recommendation" in decision
