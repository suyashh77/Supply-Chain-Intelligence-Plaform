from __future__ import annotations
from services.nlp import RISK_KEYWORDS

def score_article(polarity: float, keyword_tags: dict, openai_meta: dict | None = None) -> dict:
    """
    Returns per-category risk score in [0,1].
    - Negative sentiment increases risk.
    - Keyword presence adds a bump.
    - OpenAI severity ("high"/"medium"/"low") adds a boost.
    """
    if openai_meta is None:
        openai_meta = {}
    sentiment_risk = max(0.0, -float(polarity))
    sev = (openai_meta.get("severity") or "").lower()
    severity_boost = 0.5 if sev == "high" else (0.25 if sev == "medium" else 0.0)

    scores = {}
    for cat in RISK_KEYWORDS.keys():
        k_hits = 1.0 if cat in (keyword_tags or {}) else 0.0
        keyword_contrib = min(1.0, k_hits * 0.4)
        base = sentiment_risk * 0.6 + keyword_contrib + severity_boost * 0.4
        scores[cat] = round(min(1.0, base), 4)
    return scores
