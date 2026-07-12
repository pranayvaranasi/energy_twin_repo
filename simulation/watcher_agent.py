import datetime
import json
import os
import random

# 1. Attempt to load Gemini LLM
try:
    import google.generativeai as genai
    LLM_AVAILABLE = True
except ImportError:
    genai = None
    LLM_AVAILABLE = False

# 2. Attempt to load Exa Search (Active Semantic Hunting)
try:
    from exa_py import Exa
    EXA_AVAILABLE = True
except ImportError:
    Exa = None
    EXA_AVAILABLE = False

# 3. Attempt to load Feedparser (Passive RSS Fallback)
try:
    import feedparser
    RSS_AVAILABLE = True
except ImportError:
    feedparser = None
    RSS_AVAILABLE = False

MOCK_NEWS_API_RESPONSE = [
    {"source": "Reuters", "headline": "BREAKING: Houthi rebels claim responsibility for attack on oil tanker near Bab el-Mandeb strait.", "highlight": ""},
    {"source": "Bloomberg", "headline": "OPEC+ holds emergency meeting in Vienna, unexpected 2M bpd quota cuts announced for next quarter.", "highlight": ""},
    {"source": "Al Jazeera", "headline": "Diplomatic tensions rise; military vessels temporarily block commercial lanes in Strait of Hormuz.", "highlight": ""},
]

LIVE_RSS_FEEDS = [
    {"source": "OilPrice.com (Live)", "url": "https://oilprice.com/rss/main"},
    {"source": "Al Jazeera (Live)", "url": "https://www.aljazeera.com/xml/rss/all.xml"},
]


def _active_exa_hunt():
    """Actively hunts for breaking geopolitical energy news using Exa's neural search."""
    exa_api_key = os.getenv("EXA_API_KEY")
    if not EXA_AVAILABLE or not exa_api_key:
        return None

    try:
        exa = Exa(exa_api_key)
        response = exa.search(
            query="breaking news today regarding Strait of Hormuz blockades, Red Sea shipping attacks, or OPEC oil production cuts",
            type="auto",
            category="news",
            num_results=1,
            contents={"highlights": True},
        )

        if getattr(response, "results", None):
            top_hit = response.results[0]
            domain = top_hit.url.split("/")[2].replace("www.", "") if getattr(top_hit, "url", None) else "unknown"
            highlights = getattr(top_hit, "highlights", []) or []
            return {
                "source": f"Exa Neural Search ({domain})",
                "headline": getattr(top_hit, "title", "Live geopolitical headline detected"),
                "highlight": highlights[0] if highlights else "",
            }
    except Exception as e:
        print(f"Exa search failed, cascading to RSS: {e}")

    return None


def _get_live_news(headline_override=None):
    """Multi-tier data ingestion: Exa Search -> Live RSS -> Local Mocks"""
    if headline_override:
        return {"source": "Manual Inject", "headline": headline_override, "highlight": ""}

    exa_result = _active_exa_hunt()
    if exa_result:
        return exa_result

    if RSS_AVAILABLE:
        try:
            feed_info = random.choice(LIVE_RSS_FEEDS)
            feed = feedparser.parse(feed_info["url"])
            if getattr(feed, "entries", None):
                latest_entry = feed.entries[0]
                return {
                    "source": feed_info["source"],
                    "headline": getattr(latest_entry, "title", "Live geopolitical headline detected"),
                    "highlight": "",
                }
        except Exception as e:
            print(f"Live RSS fetch failed, cascading to mocks: {e}")

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
    if "opec" in text or "quota" in text or "barrel" in text or "oil" in text:
        return {
            "trigger_event": "OPEC+ Emergency Supply Cut",
            "calculated_severity": 7,
            "confidence_score": 0.96,
            "reasoning": "Energy market pricing context identified; moderate severity applied.",
        }
    return {
        "trigger_event": "Baseline (No Disruption)",
        "calculated_severity": 1,
        "confidence_score": 0.99,
        "reasoning": "No geopolitical risk entities detected in the incoming text stream.",
    }


def ingest_and_classify_news(headline_override=None, api_key=None, headlines=None):
    """
    RAG-powered NLP agent that actively hunts for news via Exa, parses via Gemini,
    and gracefully falls back to local heuristics if APIs are unavailable.
    """
    if headlines:
        news_item = {"source": "List Input", "headline": headlines[0], "highlight": ""}
    else:
        news_item = _get_live_news(headline_override)

    latest_news = news_item["headline"]
    context_snippet = news_item.get("highlight", "")

    retrieved_context = """
    [KNOWLEDGE BASE MATCHES]
    - DOC_01: Houthi threats in the Red Sea typically disrupt 12-15% of global maritime chokepoint traffic. Historic severity: 8-10.
    - DOC_02: OPEC+ uses 1.5M - 2M bpd quota cuts to stabilize prices. Historic severity: 6-8.
    - DOC_03: Strait of Hormuz handles ~20% of global oil. Blockades trigger immediate contagion. Historic severity: 9-10.
    """

    system_prompt = f"""
    You are 'Watcher', a Geopolitical Risk Intelligence AI operating within an Energy Supply Chain Digital Twin.
    Your task is to synthesize live news feeds with retrieved historical context and output a strict JSON payload.

    RETRIEVED CONTEXT: 
    {retrieved_context}

    LIVE NEWS FEED HEADLINE: "{latest_news}"
    NEWS ARTICLE HIGHLIGHT: "{context_snippet}"

    Analyze the threat. You MUST map the event to one of the following exact 'trigger_event' strings if applicable:
    - "Red Sea Shipping Suspension (Houthi Threat)"
    - "Strait of Hormuz Partial Closure"
    - "OPEC+ Emergency Supply Cut"
    - "Baseline (No Disruption)"

    Return ONLY valid JSON matching this schema:
    {{"trigger_event": "String",
      "calculated_severity": "Integer (1-10)",
      "confidence_score": "Float (0.00-1.00)",
      "reasoning": "A 1-sentence explanation of your assessment based on the context."
    }}
    """

    gemini_key = api_key or os.getenv("GEMINI_API_KEY")
    extracted_data = None

    if LLM_AVAILABLE and gemini_key:
        try:
            genai.configure(api_key=gemini_key)
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
        except Exception as exc:
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
