import random
import time

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
    Ingests text feeds, extracts geopolitical entities, and calculates a severity score 
    to trigger the supply chain digital twin.
    """
    if not headlines:
        # Simulate fetching the latest breaking news
        headlines = [random.choice(MOCK_LIVE_FEED)]
        
    latest_news = headlines[0]
    news_lower = latest_news.lower()
    
    detected_event = "Baseline (No Disruption)"
    severity = 1
    
    # 1. Entity Extraction & Event Mapping
    for keyword, mapped_event in EVENT_MAPPING.items():
        if keyword in news_lower:
            detected_event = mapped_event
            
            # 2. Simple Sentiment/Severity Scoring
            # If the news contains aggressive or urgent keywords, spike the severity
            high_risk_words = ["attack", "military", "emergency", "block", "cut"]
            if any(word in news_lower for word in high_risk_words):
                severity = random.randint(7, 10)
            else:
                severity = random.randint(4, 6)
            break
            
    return {
        "headline": latest_news,
        "trigger_event": detected_event,
        "calculated_severity": severity,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
