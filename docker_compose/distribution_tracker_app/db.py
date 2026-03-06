from __future__ import annotations

import os
from typing import Any, Iterable, Mapping

import psycopg2
from psycopg2.extras import execute_values


def get_connection():
    """
    Create a PostgreSQL connection using environment variables.

    Supported names (first non-empty wins):
    - host: POSTGRES_HOST, DB_HOST, PGHOST
    - port: POSTGRES_PORT, DB_PORT, PGPORT
    - db:   POSTGRES_DB, DB_NAME, PGDATABASE
    - user: POSTGRES_USER, DB_USER, PGUSER
    - pass: POSTGRES_PASSWORD, DB_PASSWORD, PGPASSWORD
    """
    host = os.getenv("POSTGRES_HOST") or os.getenv("DB_HOST") or os.getenv("PGHOST") or "localhost"
    port = int(os.getenv("POSTGRES_PORT") or os.getenv("DB_PORT") or os.getenv("PGPORT") or 5432)
    dbname = os.getenv("POSTGRES_DB") or os.getenv("DB_NAME") or os.getenv("PGDATABASE") or "distribution_tracker"
    user = os.getenv("POSTGRES_USER") or os.getenv("DB_USER") or os.getenv("PGUSER") or "postgres"
    password = (
        os.getenv("POSTGRES_PASSWORD")
        or os.getenv("DB_PASSWORD")
        or os.getenv("PGPASSWORD")
        or "postgres"
    )

    return psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password,
    )


def init_db(conn) -> None:
    """
    Create the table if it does not exist.
    """
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS market_sessions (
        symbol TEXT NOT NULL,
        date DATE NOT NULL,
        close_price DOUBLE PRECISION NOT NULL,
        volume BIGINT NOT NULL,
        price_change_pct DOUBLE PRECISION,
        ema_10 DOUBLE PRECISION,
        ema_20 DOUBLE PRECISION,
        is_distribution_day INTEGER,
        distribution_count_25d INTEGER,
        price_change_accum_25d DOUBLE PRECISION,
        market_sentiment TEXT,
        PRIMARY KEY (symbol, date)
    )
    """
    with conn.cursor() as cur:
        cur.execute(create_table_sql)
    conn.commit()


def upsert_sessions(conn, rows: Iterable[Mapping[str, Any]]) -> None:
    """
    Insert or update market session rows.

    Input rows are dictionaries from indicators.calculate_indicators(...),
    so the existing business logic can stay unchanged.
    """
    rows_list = list(rows)
    if not rows_list:
        return

    values = [
        (
            row["symbol"],
            row["date"],
            row["close_price"],
            row["volume"],
            row.get("price_change_pct"),
            row.get("ema_10"),
            row.get("ema_20"),
            row.get("is_distribution_day"),
            row.get("distribution_count_25d"),
            row.get("price_change_accum_25d"),
            row.get("market_sentiment"),
        )
        for row in rows_list
    ]

    upsert_sql = """
    INSERT INTO market_sessions (
        symbol,
        date,
        close_price,
        volume,
        price_change_pct,
        ema_10,
        ema_20,
        is_distribution_day,
        distribution_count_25d,
        price_change_accum_25d,
        market_sentiment
    ) VALUES %s
    ON CONFLICT (symbol, date) DO UPDATE SET
        close_price = EXCLUDED.close_price,
        volume = EXCLUDED.volume,
        price_change_pct = EXCLUDED.price_change_pct,
        ema_10 = EXCLUDED.ema_10,
        ema_20 = EXCLUDED.ema_20,
        is_distribution_day = EXCLUDED.is_distribution_day,
        distribution_count_25d = EXCLUDED.distribution_count_25d,
        price_change_accum_25d = EXCLUDED.price_change_accum_25d,
        market_sentiment = COALESCE(market_sessions.market_sentiment, EXCLUDED.market_sentiment)
    """

    try:
        with conn.cursor() as cur:
            execute_values(cur, upsert_sql, values)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
