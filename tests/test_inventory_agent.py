from simulation.inventory_agent import calculate_stranded_inventory


def test_calculate_stranded_inventory_reports_downstream_deficit():
    result = calculate_stranded_inventory([6], severity=5, current_brent_price=80.0)

    assert result is not None
    assert "affected_dependents" in result
    assert "stranded_volume" in result
    assert "daily_financial_deficit" in result
    assert result["inventory_status"].startswith("CRITICAL") or result["inventory_status"].startswith("WARNING")
