from __future__ import annotations
import json
from openai import OpenAI

def get_client(api_key: str | None) -> OpenAI | None:
    if not api_key:
        return None
    return OpenAI(api_key=api_key)

def extract_article_meta(client: OpenAI, title: str, description: str, max_tokens: int = 200) -> dict:
    """
    Returns JSON: {categories: [...], summary: "...", severity: "low|medium|high"}
    """
    prompt = f"""
You are an analyst. Given the following article title and description, return a JSON object with keys:
- categories: list chosen from ["logistics","political","weather","labor","esg","security","other"]
- summary: one-sentence summary of the issue
- severity: "low", "medium", or "high"

Article:
{json.dumps({"title": title, "description": description}, ensure_ascii=False)}
"""
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content  # str
        return json.loads(content)
    except Exception as e:
        return {"categories": [], "summary": "", "severity": "unknown", "error": str(e)}

def generate_briefing(client: OpenAI, origin: str, destination: str, flagged_articles: list[dict], top_k: int = 3) -> str:
    bullets = "\n".join([f"- {a.get('title')} ({a.get('source')})\n  {a.get('url')}" for a in flagged_articles[:top_k]])
    snippet = f"""
You are a supply chain analyst. Produce a concise daily briefing (3–6 short paragraphs) for the corridor between {origin} and {destination}.
- Use any provided risk and sentiment context implied by the flagged headlines.
- Mention the most likely disruption categories (logistics, political, weather, labor, esg) if present.
- Then add 2–3 recommended actions for a logistics manager (short bullets).
- Finally, list the top {top_k} flagged articles (title + source + url).

Flagged items:
{bullets}

Return plaintext only.
"""
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": snippet}],
            temperature=0.2,
            max_tokens=500,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return "Briefing unavailable (OpenAI error)."
