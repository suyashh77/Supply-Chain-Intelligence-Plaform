# Supply Chain Risk Intelligence Platform

**Tagline for Pitch Deck:**  
*From Headlines to Supply Chain Risk Signals — Anticipate Disruptions Before They Happen.*

---

## 🚀 Executive Summary
Global supply chains are increasingly vulnerable to shocks — geopolitical tensions, labor unrest, logistics bottlenecks, ESG risks, and extreme weather. Current monitoring solutions are reactive, identifying disruptions after delays and cost spikes occur.

This platform transforms global news, trade data, and event signals into **real-time, forward-looking risk intelligence**. By converting unstructured news into structured Risk Indices and Alerts, we empower supply chain leaders to **anticipate disruptions, diversify suppliers, and reroute logistics proactively.**

---

## 🔑 Features
- Multi-source News Ingestion (MVP: NewsAPI).
- Risk Scoring Engine (sentiment + GPT + keyword/entity patterns).
- Aggregation layer (risk indices by corridor, port, supplier).
- Executive summaries (auto-generated with GPT).
- Dashboard (corridor risk graphs, heatmaps, flagged events).
- Export (CSV/PDF/Email digest).

---

## 🏗 MVP Flow
1. **User Input:** Enter Origin/Destination (port or city).
2. **Data Ingestion:** Fetch daily news related to corridor + ports.
3. **Risk Processing:** NLP sentiment + keyword/entity scoring.
4. **Visualization:** 30-day trendlines for corridor + ports.
5. **Summaries:** Corridor-level insights in plain language.

---

## 📊 Key Outputs
- **Risk Table:** Corridor + ports daily risk scores.
- **Trendlines:** Sentiment & risk intensity.
- **Daily Brief:** Auto summary + top flagged articles.
- **Export:** CSV / PDF / Power BI integration.

---

## 🛠 Tech Stack
- **Frontend:** Streamlit
- **Backend:** FastAPI (optional for services), Python
- **NLP:** TextBlob, OpenAI GPT, custom keyword scoring
- **Data:** NewsAPI, YFinance (stretch), other APIs
- **Visualization:** Plotly
- **Reports:** ReportLab PDF
- **Infra:** dotenv for API keys

---

## 📦 Installation
Clone the repo and install dependencies:

```bash
git clone https://github.com/yourusername/supply-chain-risk.git
cd supply-chain-risk
pip install -r requirements.txt
