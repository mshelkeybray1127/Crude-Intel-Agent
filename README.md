# Crude Oil Intelligence Agent

A daily intelligence pipeline for physical commodity market positioning. Pulls EIA inventory data, WTI/Brent prices, and OPEC+ headlines—compiles into a structured report.

## Architecture

```
DATA SOURCES (pluggable)
├── EIA API (inventory data, weekly)
├── yfinance (WTI/Brent spot + calendar spreads)
└── NewsAPI (OPEC+ headlines, filtered)
        ↓
INGESTION LAYER (normalize to schema)
├── eia_ingester.py (parse JSON → data pool schema)
├── price_ingester.py (parse yfinance → data pool schema)
└── news_ingester.py (parse NewsAPI → data pool schema)
        ↓
DATA POOL (single source of truth)
└── SQLite or in-memory dict
    - Inventory records (date, product, volume, change)
    - Price snapshots (date, instrument, bid, ask, spread)
    - Headlines (date, source, title, snippet, url, relevance_score)
        ↓
REPORT COMPILER
└── query_pool() → format markdown/HTML → output
```

## Data Pool Schema

### Inventory
```python
{
    "date": "2026-07-11",
    "product": "crude_oil",  # or "gasoline", "distillate"
    "volume_mbbl": 423.5,
    "change_mbbl": 2.3,
    "series_id": "WCSSTIS1"
}
```

### Prices
```python
{
    "date": "2026-07-17",
    "instrument": "WTI",  # or "BRENT"
    "close": 78.45,
    "bid": 78.43,
    "ask": 78.47
}
```

### Headlines
```python
{
    "date": "2026-07-17",
    "source": "Reuters",
    "title": "OPEC+ agrees to extend production cuts",
    "snippet": "Members of the cartel...",
    "url": "https://...",
    "relevance_score": 0.9  # 0-1, for filtering later
}
```

## Data Flow

1. **Fetch** (daily, scheduled)
   - EIA API → last 4 weeks of inventory
   - yfinance → last 5 days of prices
   - NewsAPI → last 7 days of OPEC+ headlines

2. **Ingest** (transform to schema)
   - Each source has its own `_ingester.py`
   - Validates, normalizes, deduplicates
   - Writes to data pool

3. **Compile** (generate report)
   - Query data pool for recent changes
   - Highlight key moves (price spikes, inventory swings, policy news)
   - Output markdown or HTML

## Scalability Notes

**Adding new sources later:**
- Write a new ingester that outputs the same schema
- Plug into the fetch step
- No changes to data pool or report compiler

**Examples:**
- Add RSS feed ingester → deduplicates headlines against pool before insert
- Add Bloomberg/Refinitiv scraper → same ingester pattern
- Add geopolitical event data → extend schema with new table, report pulls it

**Current limitations (by design):**
- No ML/sentiment analysis (can add later)
- No web fetch for full article text (snippets only)
- Deduplication only on exact title match (can improve)

## Setup

### Dependencies
```bash
pip install requests yfinance newsapi-python
```

### API Keys
- `EIA_API_KEY` (you have)
- `NEWSAPI_KEY` (sign up at newsapi.org, free tier)
- yfinance (no key needed)

### Run
```bash
python main.py
```

## Project Structure
```
crude-intel-agent/
├── README.md
├── main.py                 # Entry point, orchestrates fetch→ingest→compile
├── data_pool.py            # In-memory or SQLite storage
├── ingesters/
│   ├── eia_ingester.py
│   ├── price_ingester.py
│   └── news_ingester.py
├── report.py               # Query pool, format output
└── config.py               # API keys, constants
```

## Next Steps

1. Get NewsAPI key
2. Write data_pool.py (simple dict or SQLite)
3. Write three ingesters
4. Write report.py
5. Write main.py
6. Test locally
7. Add cron/scheduler for daily runs