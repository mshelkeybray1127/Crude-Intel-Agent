#!/usr/bin/env python3
"""Fetch WTI/Brent crude prices from yfinance and normalize them to the data
pool schema: {date, instrument, close, bid, ask}.
"""

import sys

import yfinance as yf

# Normalized instrument name -> yfinance futures ticker.
INSTRUMENT_TICKERS = {
    "WTI": "CL=F",
    "BRENT": "BZ=F",
}


def fetch_prices(days=5, instruments=None):
    """Return normalized price records for the last `days` trading days of
    each instrument in `instruments` (default: all of INSTRUMENT_TICKERS).

    Returns a list of dicts: {date, instrument, close, bid, ask}, most recent
    day first. yfinance only exposes live bid/ask (not historical), so bid
    and ask are populated on the most recent record for each instrument and
    left as None on older ones.
    """
    instruments = instruments or list(INSTRUMENT_TICKERS.keys())

    records = []
    for instrument in instruments:
        ticker_symbol = INSTRUMENT_TICKERS.get(instrument)
        if ticker_symbol is None:
            raise RuntimeError(f"Unknown instrument: {instrument}")

        ticker = yf.Ticker(ticker_symbol)
        history = ticker.history(period=f"{days}d")
        if history.empty:
            raise RuntimeError(f"yfinance returned no history for {instrument} ({ticker_symbol})")

        bid = ask = None
        try:
            info = ticker.info
            bid = info.get("bid")
            ask = info.get("ask")
        except Exception:
            pass  # live quote unavailable (e.g. market closed); bid/ask stay None

        chronological = list(history.itertuples())
        for i, row in enumerate(reversed(chronological)):
            records.append({
                "date": row.Index.strftime("%Y-%m-%d"),
                "instrument": instrument,
                "close": round(float(row.Close), 2),
                "bid": round(float(bid), 2) if i == 0 and bid is not None else None,
                "ask": round(float(ask), 2) if i == 0 and ask is not None else None,
            })

    return records


if __name__ == "__main__":
    import json

    try:
        records = fetch_prices(days=5)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(records, indent=2))
