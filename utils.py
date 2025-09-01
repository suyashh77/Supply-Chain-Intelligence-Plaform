from __future__ import annotations
from datetime import datetime
import pandas as pd

def build_queries(origin: str, destination: str):
    origin = origin.strip()
    destination = destination.strip()
    corridor_query = f'("{origin}" AND "{destination}") OR "{origin} {destination}" OR {origin} OR {destination}'
    origin_query = f'"{origin}"'
    destination_query = f'"{destination}"'
    return corridor_query, origin_query, destination_query

def normalize_datetime_column(df: pd.DataFrame, column: str = "publishedAt") -> pd.DataFrame:
    if column not in df.columns:
        df[column] = None
    # NewsAPI returns ISO UTC; coerce safely and drop tz for plotting
    df["publishedAt_dt"] = pd.to_datetime(df[column], errors="coerce", utc=True).dt.tz_convert(None)
    df["date"] = df["publishedAt_dt"].dt.date
    return df

def build_df(articles: list[dict], source_label: str, text_from_article, analyze_sentiment_textblob, tag_keywords):
    rows = []
    for a in articles:
        text = text_from_article(a)
        polarity, subjectivity, s_label = analyze_sentiment_textblob(text)
        tags = tag_keywords(text)
        rows.append({
            "source_label": source_label,
            "publishedAt": a.get("publishedAt"),
            "title": a.get("title"),
            "description": a.get("description"),
            "url": a.get("url"),
            "source": (a.get("source") or {}).get("name"),
            "content_text": text,
            "polarity": polarity,
            "subjectivity": subjectivity,
            "sentiment_label": s_label,
            "keyword_tags": tags
        })
    df = pd.DataFrame(rows)
    return df

def aggregate_scores(df_all: pd.DataFrame, df_scores: pd.DataFrame, categories: list[str], scope_label: str) -> pd.DataFrame:
    scope_articles = df_all[df_all["source_label"] == scope_label]
    if scope_articles.empty:
        return pd.DataFrame()

    scope_scores = df_scores[df_scores["source_label"] == scope_label]
    if scope_scores.empty:
        return pd.DataFrame()

    agg = scope_scores.groupby("date")[categories].mean().reset_index()
    agg["overall_risk"] = agg[categories].mean(axis=1)
    pol = scope_articles.groupby("date")["polarity"].mean().reset_index().rename(columns={"polarity": "avg_polarity"})
    merged = agg.merge(pol, on="date", how="left").sort_values("date")
    return merged
