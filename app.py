from __future__ import annotations

import os
from datetime import datetime, timedelta
import json
import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

from services.news import fetch_news_newsapi, text_from_article
from services.nlp import analyze_sentiment_textblob, tag_keywords, RISK_KEYWORDS
from services.scoring import score_article
from services.utils import build_queries, build_df, normalize_datetime_column, aggregate_scores
from services.pdf_export import make_pdf_briefing
from services.openai_helpers import get_client, extract_article_meta, generate_briefing

# ---------------------------------------
# App config
# ---------------------------------------
st.set_page_config(page_title="Corridor Risk MVP", layout="wide")
st.title("Corridor Risk MVP — News → Sentiment → Risk Scores")

# Load env
load_dotenv()
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not NEWSAPI_KEY:
    st.warning("NEWSAPI_KEY is not set. Add it to your .env file to fetch articles.")

# ---------------------------------------
# Sidebar controls
# ---------------------------------------
with st.sidebar.form("controls"):
    origin = st.text_input("Origin (Port or City)", value="Shanghai")
    destination = st.text_input("Destination (Port or City)", value="Los Angeles")
    days = st.number_input("Days to analyze (max 30)", min_value=1, max_value=30, value=30)
    max_articles_per_query = st.number_input("Max articles per query", min_value=20, max_value=100, value=100)
    top_k_openai = st.number_input("OpenAI: analyze top K flagged", min_value=0, max_value=50, value=8)
    polarity_threshold_flag = st.slider("Flag if polarity ≤", -1.0, 0.0, -0.1, 0.05)
    run = st.form_submit_button("Fetch & Analyze")

if not run:
    st.info("Enter origin/destination, adjust options, then click **Fetch & Analyze**.")
    st.stop()

progress = st.sidebar.empty()
progress.text("Building queries…")

# ---------------------------------------
# Build queries & date range
# ---------------------------------------
to_dt = datetime.utcnow()
from_dt = to_dt - timedelta(days=int(days))
corridor_query, origin_query, destination_query = build_queries(origin, destination)

# ---------------------------------------
# Fetch articles
# ---------------------------------------
if not NEWSAPI_KEY:
    st.stop()

try:
    progress.text("Fetching corridor articles…")
    corridor_articles = fetch_news_newsapi(corridor_query, from_dt, to_dt, NEWSAPI_KEY, page_size=int(max_articles_per_query), max_pages=2)

    progress.text("Fetching origin articles…")
    origin_articles = fetch_news_newsapi(origin_query, from_dt, to_dt, NEWSAPI_KEY, page_size=int(max_articles_per_query), max_pages=1)

    progress.text("Fetching destination articles…")
    destination_articles = fetch_news_newsapi(destination_query, from_dt, to_dt, NEWSAPI_KEY, page_size=int(max_articles_per_query), max_pages=1)
except Exception as e:
    st.error(f"Error fetching articles: {e}")
    st.stop()

# ---------------------------------------
# Build DataFrames
# ---------------------------------------
df_corridor = build_df(corridor_articles, "corridor", text_from_article, analyze_sentiment_textblob, tag_keywords)
df_origin = build_df(origin_articles, "origin", text_from_article, analyze_sentiment_textblob, tag_keywords)
df_destination = build_df(destination_articles, "destination", text_from_article, analyze_sentiment_textblob, tag_keywords)

df_all = pd.concat([df_corridor, df_origin, df_destination], ignore_index=True, sort=False)
df_all = normalize_datetime_column(df_all, "publishedAt")
st.success(f"Analyzed {len(df_all)} articles total.")

# ---------------------------------------
# Flagging
# ---------------------------------------
df_all["flagged"] = df_all.apply(
    lambda r: (r["polarity"] <= polarity_threshold_flag) or (len(r["keyword_tags"]) > 0), axis=1
)
flagged = df_all[df_all["flagged"]].sort_values("publishedAt_dt", ascending=False)
st.sidebar.info(f"Flagged articles: {len(flagged)}")

# ---------------------------------------
# OpenAI enrichment (optional)
# ---------------------------------------
openai_client = get_client(OPENAI_API_KEY)
openai_meta_map: dict[str, dict] = {}

if openai_client and top_k_openai > 0 and not flagged.empty:
    st.sidebar.write("Enriching flagged articles with OpenAI…")
    for _, row in flagged.head(int(top_k_openai)).iterrows():
        pm = extract_article_meta(openai_client, row.get("title") or "", row.get("description") or "")
        openai_meta_map[row["url"]] = pm

# ---------------------------------------
# Scoring
# ---------------------------------------
scores_list = []
for _, row in df_all.iterrows():
    meta = openai_meta_map.get(row["url"], {})
    s = score_article(row["polarity"], row["keyword_tags"], meta)
    row_scores = s.copy()
    row_scores.update({
        "url": row["url"],
        "title": row["title"],
        "source_label": row["source_label"],
        "date": row["date"],
        "polarity": row["polarity"],
        "sentiment_label": row["sentiment_label"],
        "openai_summary": meta.get("summary", "") if meta else "",
    })
    scores_list.append(row_scores)

df_scores = pd.DataFrame(scores_list)

# ---------------------------------------
# Aggregations
# ---------------------------------------
categories = list(RISK_KEYWORDS.keys())
agg_corridor = aggregate_scores(df_all, df_scores, categories, "corridor")
agg_origin = aggregate_scores(df_all, df_scores, categories, "origin")
agg_destination = aggregate_scores(df_all, df_scores, categories, "destination")

# ---------------------------------------
# Visualizations
# ---------------------------------------
st.header(f"{days}-Day Trendlines — {origin} ↔ {destination}")

col1, col2 = st.columns(2)
with col1:
    st.subheader("Corridor — Overall Risk")
    if not agg_corridor.empty:
        fig = px.line(agg_corridor, x="date", y="overall_risk", markers=True, title="Corridor overall risk (avg categories)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("No corridor data.")

with col2:
    st.subheader("Corridor — Avg Sentiment (polarity)")
    if not agg_corridor.empty:
        fig2 = px.line(agg_corridor, x="date", y="avg_polarity", markers=True, title="Corridor avg polarity (-1..1)")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.write("No corridor data.")

st.subheader("Origin / Destination risk trends")
cols = st.columns(2)
with cols[0]:
    st.markdown(f"**Origin — {origin}**")
    if not agg_origin.empty:
        fig = px.line(agg_origin, x="date", y="overall_risk", title=f"{origin} overall risk (avg categories)", markers=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("No origin data.")

with cols[1]:
    st.markdown(f"**Destination — {destination}**")
    if not agg_destination.empty:
        fig = px.line(agg_destination, x="date", y="overall_risk", title=f"{destination} overall risk (avg categories)", markers=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("No destination data.")

# ---------------------------------------
# Table of flagged items
# ---------------------------------------
st.subheader("Top recent flagged articles (sample)")
if not flagged.empty:
    display_cols = ["publishedAt_dt", "source", "title", "sentiment_label", "polarity", "keyword_tags", "url"]
    st.dataframe(flagged[display_cols].head(20).sort_values("publishedAt_dt", ascending=False))
else:
    st.write("No flagged articles found.")

# ---------------------------------------
# Daily briefing (OpenAI optional)
# ---------------------------------------
st.subheader("Automated Daily Briefing (corridor-level)")
flagged_list = flagged.to_dict(orient="records")

if openai_client:
    with st.spinner("Generating briefing with OpenAI…"):
        briefing_text = generate_briefing(openai_client, origin, destination, flagged_list, top_k=3)
else:
    briefing_text = "OpenAI key not set. Configure OPENAI_API_KEY to generate the briefing."

st.text_area("Briefing", briefing_text, height=250)

# ---------------------------------------
# Exports
# ---------------------------------------
st.subheader("Export")
csv_bytes = df_all.to_csv(index=False).encode("utf-8")
st.download_button("Download raw articles CSV", csv_bytes, file_name="articles_raw.csv", mime="text/csv")

top_articles_for_pdf = flagged_list[:5]
pdf_bytes = make_pdf_briefing(f"Daily Briefing — {origin} ↔ {destination}", briefing_text, top_articles_for_pdf)
st.download_button("Download Briefing (PDF)", pdf_bytes, file_name="briefing.pdf", mime="application/pdf")

st.success("MVP run complete. Adjust parameters on the left to iterate.")
