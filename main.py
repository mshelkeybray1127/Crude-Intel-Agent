#!/usr/bin/env python3
"""Orchestrator: fetch from all sources, ingest into the data pool, compile
and write the report. Each source is isolated — one failing (e.g. an API
outage) doesn't block the others or prevent a report from being generated.
"""

import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "ingesters"))

import data_pool as dp
import report
from eia_ingester import fetch_crude_inventory
from news_ingester import fetch_headlines
from price_ingester import fetch_prices

SOURCES = [
    ("eia", fetch_crude_inventory, dp.insert_inventory),
    ("price", fetch_prices, dp.insert_prices),
    ("news", fetch_headlines, dp.insert_headlines),
]


def _run_source(name, fetch_fn, insert_fn, conn):
    try:
        records = fetch_fn()
        insert_fn(records, conn=conn)
        print(f"[main] {name}: ingested {len(records)} records")
        return True
    except Exception as e:
        print(f"[main] WARNING: {name} failed: {e}", file=sys.stderr)
        return False


def run():
    conn = dp.connect()
    results = {name: _run_source(name, fetch_fn, insert_fn, conn)
               for name, fetch_fn, insert_fn in SOURCES}

    today = datetime.date.today().isoformat()
    report_md = report.compile_report(generated_date=today, conn=conn)
    out_path = report.write_report(report_md, date=today)
    conn.close()

    succeeded = [name for name, ok in results.items() if ok]
    failed = [name for name, ok in results.items() if not ok]
    summary = f"[main] sources succeeded: {succeeded or 'none'}, failed: {failed or 'none'}; report: {out_path}"
    print(summary)
    return out_path


if __name__ == "__main__":
    run()
