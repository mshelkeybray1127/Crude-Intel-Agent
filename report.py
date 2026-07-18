#!/usr/bin/env python3
"""Query the data pool and compile a markdown report covering inventory,
prices, and headlines. No highlighting/thresholds yet — renders everything
currently in the pool.
"""

import datetime
import os

import data_pool as dp

REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")


def _inventory_section(rows):
    if not rows:
        return "## Inventory\n\n_No inventory data available._\n"
    lines = [
        "## Inventory\n",
        "| Date | Product | Volume (mbbl) | Change (mbbl) | Series ID |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['date']} | {r['product']} | {r['volume_mbbl']} | {r['change_mbbl']} | {r['series_id']} |"
        )
    return "\n".join(lines) + "\n"


def _prices_section(rows):
    if not rows:
        return "## Prices\n\n_No price data available._\n"
    lines = [
        "## Prices\n",
        "| Date | Instrument | Close | Bid | Ask |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['date']} | {r['instrument']} | {r['close']} | {r['bid']} | {r['ask']} |"
        )
    return "\n".join(lines) + "\n"


def _headlines_section(rows):
    if not rows:
        return "## Headlines\n\n_No headline data available._\n"
    lines = ["## Headlines\n"]
    for r in rows:
        lines.append(
            f"- **{r['date']}** [{r['title']}]({r['url']}) — {r['source']} "
            f"(relevance {r['relevance_score']})"
        )
        if r.get("snippet"):
            lines.append(f"  > {r['snippet']}")
    return "\n".join(lines) + "\n"


def compile_report(since_date=None, conn=None, generated_date=None):
    """Query the data pool and return a full markdown report as a string."""
    own_conn = conn is None
    conn = conn or dp.connect()

    inventory = dp.query_inventory(since_date=since_date, conn=conn)
    prices = dp.query_prices(since_date=since_date, conn=conn)
    headlines = dp.query_headlines(since_date=since_date, conn=conn)

    if own_conn:
        conn.close()

    generated_date = generated_date or datetime.date.today().isoformat()
    header = f"# Crude Oil Intelligence Report — {generated_date}\n"
    sections = [
        header,
        _inventory_section(inventory),
        _prices_section(prices),
        _headlines_section(headlines),
    ]
    return "\n".join(sections)


def write_report(report_md, date=None):
    """Write a compiled report to reports/{date}.md, creating the directory
    if needed. Returns the output path."""
    date = date or datetime.date.today().isoformat()
    os.makedirs(REPORTS_DIR, exist_ok=True)
    out_path = os.path.join(REPORTS_DIR, f"{date}.md")
    with open(out_path, "w") as f:
        f.write(report_md)
    return out_path


if __name__ == "__main__":
    today = datetime.date.today().isoformat()
    report_md = compile_report(generated_date=today)
    out_path = write_report(report_md, date=today)
    print(f"Report written to {out_path}")
