import datetime
import json
import os
import random

# Attempt to load Generative AI library for live inference
try:
    import google.generativeai as genai
except ImportError:  # pragma: no cover - optional dependency
    genai = None

LLM_AVAILABLE = genai is not None

# Simulate a real API payload from a feed like GDELT or NewsAPI
MOCK_NEWS_API_RESPONSE = [
    {
        "source": "Reuters",
        "headline": "BREAKING: Houthi rebels claim responsibility for attack on oil tanker near Bab el-Mandeb strait.",
    },
    {
        "source": "Bloomberg",
        "headline": "OPEC+ holds emergency meeting in Vienna, unexpected 2M bpd quota cuts announced for next quarter.",
    },
    {
        "source": "Al Jazeera",
        "headline": "Diplomatic tensions rise; military vessels temporarily block commercial lanes in Strait of Hormuz.",
    },
    {
        "source": "Platts",
        "headline": "Global markets stabilize as Middle East supply chain routes resume normal operations.",
    },
]


def _get_live_news(headline_override=None):
    """Simulate fetching the latest news from a live endpoint."""
    if headline_override:
        return {"source": "Manual Inject", "headline": headline_override}
    return random.choice(MOCK_NEWS_API_RESPONSE)


def _mock_llm_extraction(news_text):
    """Zero-dependency fallback NLP heuristic."""
    text = news_text.lower()
    if "houthi" in text or "red sea" in text or "bab el-mandeb" in text:
        return {
            "trigger_event": "Red Sea Shipping Suspension (Houthi Threat)",
            "calculated_severity": 9,
            "confidence_score": 0.94,
            "reasoning": "Keywords strongly correlate with major maritime disruption via Red Sea vectors.",
        }
    if "hormuz" in text:
        return {
            "trigger_event": "Strait of Hormuz Partial Closure",
            "calculated_severity": 10,
            "confidence_score": 0.88,
            "reasoning": "Strait of Hormuz blockade detected; critical chokepoint macroeconomic severity applied.",
        }
    if "opec" in text:
        return {
            "trigger_event": "OPEC+ Emergency Supply Cut",
            "calculated_severity": 7,
            "confidence_score": 0.96,
            "reasoning": "OPEC quota cut identified; moderate severity applied per historical pricing context.",
        }
    return {
        "trigger_event": "Baseline (No Disruption)",
        "calculated_severity": 1,
        "confidence_score": 0.99,
        "reasoning": "No geopolitical risk entities detected in the incoming text stream.",
    }


def ingest_and_classify_news(headline_override=None, api_key=None, headlines=None):
    """
    RAG-powered NLP agent that attempts live LLM inference and gracefully falls back to a local heuristic.
    """
    if headlines:
        news_item = {"source": "List Input", "headline": headlines[0]}
    else:
        news_item = _get_live_news(headline_override)

    latest_news = news_item["headline"]

    retrieved_context = """
    [KNOWLEDGE BASE MATCHES]
    - DOC_01: Houthi threats in the Red Sea typically disrupt 12-15% of global maritime chokepoint traffic, severely impacting Suez transit times. Historic severity: 8-10.
    - DOC_02: OPEC+ has historically used 1.5M - 2M bpd quota cuts to stabilize prices during demand shocks. Historic severity: 6-8.
    - DOC_03: The Strait of Hormuz handles ~20% of global oil consumption. Any military blockade triggers immediate macroeconomic contagion. Historic severity: 9-10.
    """

    system_prompt = f"""
    You are 'Watcher', a Geopolitical Risk Intelligence AI operating within an Energy Supply Chain Digital Twin.
    Your task is to synthesize live news feeds with retrieved historical context and output a strict JSON payload.

    RETRIEVED CONTEXT:
    {retrieved_context}

    LIVE NEWS FEED:
    "{latest_news}"

    Analyze the threat. You MUST map the event to one of the following exact 'trigger_event' strings if applicable:
    - "Red Sea Shipping Suspension (Houthi Threat)"
    - "Strait of Hormuz Partial Closure"
    - "OPEC+ Emergency Supply Cut"
    - "Baseline (No Disruption)"

    Return ONLY valid JSON matching this schema:
    {{
        "trigger_event": "String",
        "calculated_severity": "Integer (1-10)",
        "confidence_score": "Float (0.00-1.00)",
        "reasoning": "A 1-sentence explanation of your assessment based on the context."
    }}
    """

    api_key = api_key or os.getenv("GEMINI_API_KEY")
    extracted_data = None

    if LLM_AVAILABLE and api_key:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(
                "gemini-1.5-flash",
                generation_config={"response_mime_type": "application/json"},
            )
            response = model.generate_content(system_prompt)
            parsed = json.loads(response.text)
            extracted_data = {
                "trigger_event": parsed.get("trigger_event", "Baseline (No Disruption)"),
                "calculated_severity": int(parsed.get("calculated_severity", 1)),
                "confidence_score": float(parsed.get("confidence_score", 0.90)),
                "reasoning": parsed.get("reasoning", "Live LLM response parsed successfully."),
            }
        except Exception as exc:  # pragma: no cover - fallback path
            print(f"LLM API failed, falling back to heuristic: {exc}")

    if not extracted_data:
        extracted_data = _mock_llm_extraction(latest_news)

    return {
        "source": news_item["source"],
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "headline": latest_news,
        "trigger_event": extracted_data.get("trigger_event", "Baseline (No Disruption)"),
        "calculated_severity": int(extracted_data.get("calculated_severity", 1)),
        "confidence_score": f"{extracted_data.get('confidence_score', 0.90) * 100:.1f}%",
        "reasoning": extracted_data.get("reasoning", "Fallback heuristic applied due to API unavailability."),
    }
