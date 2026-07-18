#!/usr/bin/env python3
"""Single source of truth for ingested data: SQLite-backed data pool with
one table per source (inventory, prices, headlines), matching the schema
documented in README.md.
"""

import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_pool.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS inventory (
    date TEXT NOT NULL,
    product TEXT NOT NULL,
    volume_mbbl REAL NOT NULL,
    change_mbbl REAL NOT NULL,
    series_id TEXT NOT NULL,
    PRIMARY KEY (date, product, series_id)
);

CREATE TABLE IF NOT EXISTS prices (
    date TEXT NOT NULL,
    instrument TEXT NOT NULL,
    close REAL NOT NULL,
    bid REAL,
    ask REAL,
    PRIMARY KEY (date, instrument)
);

CREATE TABLE IF NOT EXISTS headlines (
    date TEXT NOT NULL,
    source TEXT NOT NULL,
    title TEXT NOT NULL,
    snippet TEXT,
    url TEXT,
    relevance_score REAL,
    PRIMARY KEY (date, title)
);
"""


def connect(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def insert_inventory(records, conn=None):
    """Insert normalized inventory records, deduplicating on (date, product, series_id)."""
    own_conn = conn is None
    conn = conn or connect()
    conn.executemany(
        """INSERT OR IGNORE INTO inventory (date, product, volume_mbbl, change_mbbl, series_id)
           VALUES (:date, :product, :volume_mbbl, :change_mbbl, :series_id)""",
        records,
    )
    conn.commit()
    if own_conn:
        conn.close()


def insert_prices(records, conn=None):
    """Insert normalized price records, deduplicating on (date, instrument)."""
    own_conn = conn is None
    conn = conn or connect()
    conn.executemany(
        """INSERT OR IGNORE INTO prices (date, instrument, close, bid, ask)
           VALUES (:date, :instrument, :close, :bid, :ask)""",
        records,
    )
    conn.commit()
    if own_conn:
        conn.close()


def insert_headlines(records, conn=None):
    """Insert normalized headline records, deduplicating on (date, title) — exact
    title match only, per README's known limitation."""
    own_conn = conn is None
    conn = conn or connect()
    conn.executemany(
        """INSERT OR IGNORE INTO headlines (date, source, title, snippet, url, relevance_score)
           VALUES (:date, :source, :title, :snippet, :url, :relevance_score)""",
        records,
    )
    conn.commit()
    if own_conn:
        conn.close()


def query_inventory(since_date=None, conn=None):
    own_conn = conn is None
    conn = conn or connect()
    if since_date:
        rows = conn.execute(
            "SELECT * FROM inventory WHERE date >= ? ORDER BY date DESC", (since_date,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM inventory ORDER BY date DESC").fetchall()
    if own_conn:
        conn.close()
    return [dict(row) for row in rows]


def query_prices(since_date=None, conn=None):
    own_conn = conn is None
    conn = conn or connect()
    if since_date:
        rows = conn.execute(
            "SELECT * FROM prices WHERE date >= ? ORDER BY date DESC", (since_date,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM prices ORDER BY date DESC").fetchall()
    if own_conn:
        conn.close()
    return [dict(row) for row in rows]


def query_headlines(since_date=None, min_relevance=0.0, conn=None):
    own_conn = conn is None
    conn = conn or connect()
    if since_date:
        rows = conn.execute(
            """SELECT * FROM headlines WHERE date >= ? AND relevance_score >= ?
               ORDER BY date DESC""",
            (since_date, min_relevance),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM headlines WHERE relevance_score >= ? ORDER BY date DESC",
            (min_relevance,),
        ).fetchall()
    if own_conn:
        conn.close()
    return [dict(row) for row in rows]


if __name__ == "__main__":
    conn = connect()
    print(f"data pool initialized at {DB_PATH}")
    print(f"inventory rows: {conn.execute('SELECT COUNT(*) FROM inventory').fetchone()[0]}")
    print(f"price rows:     {conn.execute('SELECT COUNT(*) FROM prices').fetchone()[0]}")
    print(f"headline rows:  {conn.execute('SELECT COUNT(*) FROM headlines').fetchone()[0]}")
    conn.close()
