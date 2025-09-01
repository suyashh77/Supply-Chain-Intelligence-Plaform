from __future__ import annotations
from datetime import datetime
import requests

def fetch_news_newsapi(query: str, from_dt: datetime, to_dt: datetime, api_key: str, page_size=100, max_pages=2):
    all_articles = []
    url = "https://newsapi.org/v2/everything"
    headers = {}
    for page in range(1, max_pages + 1):
        params = {
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": page_size,
            "page": page,
            "from": from_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "to": to_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "apiKey": api_key,
        }
        resp = requests.get(url, params=params, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        articles = data.get("articles", []) or []
        if not articles:
            break
        all_articles.extend(articles)
        if len(articles) < page_size:
            break
    return all_articles

def text_from_article(a: dict) -> str:
    parts = [
        a.get("title") or "",
        a.get("description") or "",
        (a.get("content") or "").split("…")[0],
    ]
    return " ".join([p for p in parts if p]).strip()
