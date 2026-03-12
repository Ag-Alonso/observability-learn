from __future__ import annotations

import pandas as pd
import yfinance as yf

from db import get_connection, init_db, upsert_sessions
from indicators import calculate_indicators

SYMBOLS = ["SPY", "QQQ"]
LOOKBACK_DAYS = 26
RAW_COLUMNS = ["symbol", "date", "close_price", "volume"]


def fetch_raw_daily_data(symbol: str, lookback_days: int = LOOKBACK_DAYS) -> pd.DataFrame:
    """
    Download recent daily market data for one symbol using yfinance.

    Returns a clean DataFrame with the minimum fields needed by V1:
    - symbol
    - date (YYYY-MM-DD)
    - close_price
    - volume
    """
    # To get the latest 26 *trading sessions* (not calendar days),
    # download a slightly larger calendar window and keep the last rows.
    raw_df = yf.download(
        tickers=symbol,
        period="3mo",
        interval="1d",
        auto_adjust=False,
        progress=False,
    )

    if raw_df.empty:
        return pd.DataFrame(columns=RAW_COLUMNS)

    # Keep only the columns we need and normalize names.
    df = raw_df[["Close", "Volume"]].copy()
    df = df.rename(columns={"Close": "close_price", "Volume": "volume"})

    # Move date from index to a normal column and format for DB consistency.
    df = df.reset_index()
    df["date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")
    df["symbol"] = symbol

    # Keep only the latest trading sessions requested by V1.
    df = df.tail(lookback_days)

    # Keep output shape explicit and beginner-friendly.
    df = df[RAW_COLUMNS]

    # Basic type cleanup.
    df["close_price"] = df["close_price"].astype(float)
    df["volume"] = df["volume"].fillna(0).astype(int)

    return df


def fetch_symbols_data(symbols: list[str], lookback_days: int = LOOKBACK_DAYS) -> pd.DataFrame:
    """
    Download data for many symbols and return one combined DataFrame.
    """
    dataframes: list[pd.DataFrame] = []
    for symbol in symbols:
        symbol_df = fetch_raw_daily_data(symbol, lookback_days=lookback_days)
        if not symbol_df.empty:
            dataframes.append(symbol_df)

    if not dataframes:
        return pd.DataFrame(columns=RAW_COLUMNS)

    return pd.concat(dataframes, ignore_index=True)


def save_to_database(conn, enriched_df: pd.DataFrame) -> None:
    """
    Save calculated rows into PostgreSQL using upsert.
    """
    if enriched_df.empty:
        return
    upsert_sessions(conn, enriched_df.to_dict(orient="records"))


def print_symbol_summary(enriched_df: pd.DataFrame, symbol: str) -> None:
    """
    Print a simple summary for one symbol.
    """
    symbol_df = enriched_df[enriched_df["symbol"] == symbol].copy()

    if symbol_df.empty:
        print(f"{symbol}: no rows processed")
        return

    symbol_df = symbol_df.sort_values("date")
    latest = symbol_df.iloc[-1]

    rows_processed = len(symbol_df)
    latest_date = latest["date"]
    latest_distribution_count_25d = int(latest["distribution_count_25d"])
    latest_price_change_accum_25d = float(latest["price_change_accum_25d"])
    distribution_days_in_window = int(symbol_df["is_distribution_day"].sum())

    print(
        f"{symbol} | rows={rows_processed} | latest_date={latest_date} | "
        f"latest_distribution_count_25d={latest_distribution_count_25d} | "
        f"latest_price_change_accum_25d={latest_price_change_accum_25d:.2f}% | "
        f"distribution_days_in_26={distribution_days_in_window}"
    )


def run_manual_v1_flow() -> None:
    """
    Manual V1 execution flow:
    1) connect to PostgreSQL
    2) create table if needed
    3) download latest 26 trading sessions for SPY and QQQ
    4) calculate indicators
    5) save into PostgreSQL
    6) print terminal summary per symbol
    """
    # 1) Connect to PostgreSQL.
    conn = get_connection()
    try:
        # 2) Initialize table if it does not exist.
        init_db(conn)

        # 3) Download raw market data.
        market_df = fetch_symbols_data(SYMBOLS, lookback_days=LOOKBACK_DAYS)

        # 4) Calculate indicators.
        enriched_df = calculate_indicators(market_df)

        # 5) Save results.
        save_to_database(conn, enriched_df)

        # 6) Print summary for each symbol.
        for symbol in SYMBOLS:
            print_symbol_summary(enriched_df, symbol)
    finally:
        conn.close()


if __name__ == "__main__":
    run_manual_v1_flow()
