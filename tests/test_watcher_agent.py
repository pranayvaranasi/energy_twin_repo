from simulation.watcher_agent import ingest_and_classify_news


def test_watcher_agent_falls_back_gracefully_without_api_key():
    result = ingest_and_classify_news(
        headline_override="Houthi rebels attack a tanker near Bab el-Mandeb",
        api_key=None,
    )

    assert result["trigger_event"] == "Red Sea Shipping Suspension (Houthi Threat)"
    assert isinstance(result["calculated_severity"], int)
    assert result["confidence_score"].endswith("%")
    assert isinstance(result["reasoning"], str)
    assert result["reasoning"]
