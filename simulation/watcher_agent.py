import random
import time
import json

# Mock live news stream. In production, this connects to a News API or GDELT.
MOCK_LIVE_FEED = [
    "BREAKING: Houthi rebels claim responsibility for attack on oil tanker near Bab el-Mandeb strait.",
    "OPEC+ holds emergency meeting, unexpected 2M bpd quota cuts announced for next quarter.",
    "Diplomatic tensions rise; military vessels temporarily block commercial lanes in Strait of Hormuz.",
    "Global markets stabilize as Middle East supply chain routes resume normal operations.",
    "US Gulf Coast refineries report standard operating capacities following minor storm warnings."
]

# Entity mapping to our MCTS scenarios
EVENT_MAPPING = {
    "houthi": "Red Sea Shipping Suspension (Houthi Threat)",
    "red sea": "Red Sea Shipping Suspension (Houthi Threat)",
    "hormuz": "Strait of Hormuz Partial Closure",
    "opec": "OPEC+ Emergency Supply Cut"
}

def ingest_and_classify_news(headlines=None):
    """
    Simulates passing unstructured news data to an LLM to extract
    geopolitical entities and risk severity in strict JSON format.
    """
    if not headlines:
        headlines = [random.choice(MOCK_LIVE_FEED)]
        
    latest_news = headlines[0]

    # NEW: Mocking the Retrieval step of RAG
    # In production, this queries a vector database containing historical OSINT data.
    mock_retrieved_context = """
    Document 1 (OPEC+ Policy): OPEC+ has historically used 1.5M - 2M bpd quota cuts to stabilize prices during demand shocks.
    Document 2 (Maritime Security): Houthi threats in the Red Sea typically disrupt 12-15% of global maritime chokepoint traffic, severely impacting Suez transit.
    """

    extraction_prompt = f"""
    You are a Geopolitical Risk Intelligence AI utilizing Retrieval-Augmented Generation (RAG).

    RETRIEVED CONTEXT:
    {mock_retrieved_context}

    LIVE NEWS FEED:
    \"{latest_news}\"

    Task: Synthesize the live news with the retrieved historical context.
    Extract the intelligence into the following strict JSON schema:
    {{
        "trigger_event": "String",
        "calculated_severity": "Integer (1-10 based on economic threat level)"
    }}
    """

    # In a live environment, you would call:
    # response = gemini_model.generate_content(extraction_prompt)
    # extracted_data = json.loads(response.text)
    # Here we mock the parsed LLM output for the prototype.

    news_lower = latest_news.lower()
    if "houthi" in news_lower or "red sea" in news_lower:
        extracted_data = {"trigger_event": "Red Sea Shipping Suspension (Houthi Threat)", "calculated_severity": random.randint(8, 10)}
    elif "opec" in news_lower:
        extracted_data = {"trigger_event": "OPEC+ Emergency Supply Cut", "calculated_severity": random.randint(6, 8)}
    else:
        extracted_data = {"trigger_event": "Baseline (No Disruption)", "calculated_severity": 1}

    return {
        "headline": latest_news,
        "trigger_event": extracted_data["trigger_event"],
        "calculated_severity": extracted_data["calculated_severity"],
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
