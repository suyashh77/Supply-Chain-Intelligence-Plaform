from __future__ import annotations
from textblob import TextBlob

RISK_KEYWORDS = {
    "logistics": ["shipment", "delay", "port congestion", "container", "truck", "vessel", "berth", "backlog"],
    "political": ["sanction", "election", "government", "protest", "policy", "geopolitical", "ussc", "embargo"],
    "weather": ["hurricane", "storm", "flood", "earthquake", "typhoon", "cyclone"],
    "labor": ["strike", "union", "workers", "labor", "walkout", "dockworker"],
    "esg": ["environment", "emission", "spill", "pollution", "accident"],
}

def analyze_sentiment_textblob(text: str):
    if not text:
        return 0.0, 0.0, "neutral"
    blob = TextBlob(text)
    polarity = round(blob.sentiment.polarity, 4)
    subjectivity = round(blob.sentiment.subjectivity, 4)
    if polarity > 0.1:
        label = "positive"
    elif polarity < -0.1:
        label = "negative"
    else:
        label = "neutral"
    return polarity, subjectivity, label

def tag_keywords(text: str):
    found = {}
    text_lower = (text or "").lower()
    for cat, words in RISK_KEYWORDS.items():
        hits = [w for w in words if w.lower() in text_lower]
        if hits:
            found[cat] = hits
    return found
