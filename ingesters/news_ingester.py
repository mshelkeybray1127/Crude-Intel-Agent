#!/usr/bin/env python3
"""Fetch OPEC+ headlines from the newsapi.ai (Event Registry) API and
normalize them to the data pool schema:
{date, source, title, snippet, url, relevance_score}.
"""

import os
import sys
from datetime import datetime, timedelta

import requests

NEWSAPI_URL = "https://eventregistry.org/api/v1/article/getArticles"
ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")

# Query terms used both for the NewsAPI search and for the relevance scoring
# below (extend here to widen/narrow coverage).
QUERY_TERMS = ["OPEC", "OPEC+", "crude oil", "oil production cut"]


def load_dotenv(path=ENV_PATH):
    """Minimal .env loader (no external dependency)."""
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def get_api_key():
    load_dotenv()
    api_key = os.environ.get("NEWSAPI_KEY")
    if not api_key:
        raise RuntimeError("NEWSAPI_KEY not set (checked environment and .env)")
    return api_key


def _relevance_score(title, snippet):
    """Placeholder scoring until real NLP/sentiment is added: fraction of
    QUERY_TERMS that appear (case-insensitive) in the title or snippet."""
    text = f"{title} {snippet}".lower()
    hits = sum(1 for term in QUERY_TERMS if term.lower() in text)
    return round(min(hits / len(QUERY_TERMS), 1.0), 2)


def fetch_headlines(days=7, api_key=None):
    """Hit the NewsAPI /v2/everything endpoint and return normalized OPEC+
    headline records from the last `days` days.

    Returns a list of dicts: {date, source, title, snippet, url,
    relevance_score}, most recent first.
    """
    api_key = api_key or get_api_key()

    from_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
    body = {
        "action": "getArticles",
        "keyword": QUERY_TERMS,
        "keywordOper": "or",
        "lang": "eng",
        "dateStart": from_date,
        "articlesSortBy": "date",
        "articlesCount": 100,
        "articlesPage": 1,
        "resultType": "articles",
        "apiKey": api_key,
    }

    response = requests.post(NEWSAPI_URL, json=body, timeout=30)
    response.raise_for_status()
    payload = response.json()

    if "error" in payload:
        raise RuntimeError(f"newsapi.ai returned an error: {payload['error']}")

    normalized = []
    for article in payload.get("articles", {}).get("results", []):
        title = article.get("title") or ""
        snippet = article.get("body") or ""
        normalized.append({
            "date": article.get("date") or "",
            "source": (article.get("source") or {}).get("title", "unknown"),
            "title": title,
            "snippet": snippet,
            "url": article.get("url"),
            "relevance_score": _relevance_score(title, snippet),
        })

    return normalized


if __name__ == "__main__":
    import json

    try:
        records = fetch_headlines(days=7)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(records, indent=2))
