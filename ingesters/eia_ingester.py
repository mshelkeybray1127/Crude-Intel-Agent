#!/usr/bin/env python3
"""Fetch U.S. crude oil inventory data from the EIA v2 API and normalize it
to the data pool schema: {date, product, volume_mbbl, change_mbbl, series_id}.
"""

import os
import sys

import requests

EIA_BASE_URL = "https://api.eia.gov/v2/petroleum/stoc/wstk/data/"
ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")

# EIA facet code -> normalized product name (extend here for gasoline/distillate later)
PRODUCT_NAMES = {
    "EPC0": "crude_oil",
}


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
    api_key = os.environ.get("EIA_API_KEY")
    if not api_key:
        raise RuntimeError("EIA_API_KEY not set (checked environment and .env)")
    return api_key


def fetch_crude_inventory(weeks=4, api_key=None):
    """Hit the EIA v2 API and return normalized inventory records for the
    last `weeks` weeks of U.S. crude oil ending stocks (excl. SPR).

    Returns a list of dicts: {date, product, volume_mbbl, change_mbbl, series_id},
    most recent week first.
    """
    api_key = api_key or get_api_key()

    # Fetch one extra week so every requested week has a computed change_mbbl.
    params = {
        "api_key": api_key,
        "frequency": "weekly",
        "data[0]": "value",
        "facets[duoarea][]": "NUS",
        "facets[product][]": "EPC0",
        "facets[process][]": "SAX",
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "length": weeks + 1,
    }

    response = requests.get(EIA_BASE_URL, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()

    try:
        raw_records = payload["response"]["data"]
    except KeyError:
        raise RuntimeError(f"Unexpected EIA API response structure: {payload}")

    if len(raw_records) < 2:
        raise RuntimeError(f"EIA API returned insufficient data to compute change: {raw_records}")

    # API returns most-recent-first; reverse to chronological order for diffing.
    chronological = list(reversed(raw_records))

    normalized = []
    for prev, curr in zip(chronological, chronological[1:]):
        volume = float(curr["value"]) / 1000  # thousand barrels -> million barrels
        prev_volume = float(prev["value"]) / 1000
        normalized.append({
            "date": curr["period"],
            "product": PRODUCT_NAMES.get(curr["product"], curr["product"]),
            "volume_mbbl": round(volume, 3),
            "change_mbbl": round(volume - prev_volume, 3),
            "series_id": curr["series"],
        })

    normalized.reverse()  # most recent week first
    return normalized[:weeks]


if __name__ == "__main__":
    import json

    try:
        records = fetch_crude_inventory(weeks=4)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(records, indent=2))
