from simulation.spr_agent import generate_spr_schedule


def test_generate_spr_schedule_enforces_cavern_limits_and_rationing():
    schedule = generate_spr_schedule(severity_score=8, delay_days=20, max_spr_capacity_mbpd=1.5)

    assert schedule is not None
    assert "Recommended SPR Release (M bpd)" in schedule.columns
    assert "SPR Remaining (M Barrels)" in schedule.columns
    assert "Status" in schedule.columns

    assert schedule.iloc[0]["Recommended SPR Release (M bpd)"] > 0
    assert schedule.iloc[-1]["SPR Remaining (M Barrels)"] >= 0.0
    assert schedule.iloc[-1]["SPR Remaining (M Barrels)"] <= schedule.iloc[0]["SPR Remaining (M Barrels)"]
    assert schedule.iloc[-1]["Recommended SPR Release (M bpd)"] <= schedule.iloc[0]["Recommended SPR Release (M bpd)"]
    assert any("Stable" in status or "Critical Rationing" in status or "DEPLETED" in status for status in schedule["Status"].values)
