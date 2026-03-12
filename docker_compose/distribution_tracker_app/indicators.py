from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import pandas as pd


TMP_DIR = Path("/tmp")
RECENT_WINDOW = 26


def export_symbol_csvs(processed_df: pd.DataFrame) -> None:
    """
    Save one temporary CSV file per symbol in /tmp.

    Example files:
    - /tmp/SPY_indicators.csv
    - /tmp/QQQ_indicators.csv
    """
    if processed_df.empty:
        return

    # Make sure the temporary directory exists before writing files.
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    for symbol in processed_df["symbol"].unique():
        symbol_df = processed_df[processed_df["symbol"] == symbol].copy()
        output_path = TMP_DIR / f"{symbol}_indicators.csv"
        symbol_df.to_csv(output_path, index=False)


def _extract_single_column(df: pd.DataFrame, column_name: str) -> pd.Series:
    """
    Return one clean Series for a logical column name.

    Some upstream pandas/yfinance operations can produce duplicate column names.
    In that case, df[column_name] becomes a DataFrame instead of a Series.
    Here we collapse duplicates by taking the first non-null value across them.
    """
    column_data = df.loc[:, column_name]

    if isinstance(column_data, pd.DataFrame):
        return column_data.bfill(axis=1).iloc[:, 0]

    return column_data


def _normalize_input_dataframe(market_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build a clean input DataFrame with one column per required field.

    This keeps the V1 logic unchanged while protecting the indicator code from
    duplicate labels or multi-source formatting quirks in the raw input.
    """
    df = market_df.copy()

    return pd.DataFrame(
        {
            "symbol": _extract_single_column(df, "symbol"),
            "date": _extract_single_column(df, "date"),
            "close_price": _extract_single_column(df, "close_price"),
            "volume": _extract_single_column(df, "volume"),
        }
    )


def calculate_indicators(market_df: pd.DataFrame) -> pd.DataFrame:
    """
    Receive raw market data and return a DataFrame ready for DB insertion.

    Required input columns:
    - symbol
    - date (YYYY-MM-DD or datetime)
    - close_price
    - volume
    """
    if market_df.empty:
        return pd.DataFrame(
            columns=[
                "symbol",
                "date",
                "close_price",
                "volume",
                "price_change_pct",
                "ema_10",
                "ema_20",
                "is_distribution_day",
                "distribution_count_25d",
                "price_change_accum_25d",
                "market_sentiment",
            ]
        )

    # Normalize the input first so each required field is a single column.
    # This guarantees that later group calculations work with one aligned Series.
    df = _normalize_input_dataframe(market_df)

    # Ensure consistent order and types before any calculation.
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["symbol", "date"]).reset_index(drop=True)
    df["close_price"] = df["close_price"].astype(float)
    df["volume"] = df["volume"].astype(float)

    grouped = df.groupby("symbol")

    # Use transform(...) for group calculations that must come back as one
    # aligned column. Each symbol is calculated independently, and pandas
    # returns one value per original row in the same order as df.
    df["price_change_pct"] = grouped["close_price"].transform(
        lambda series: series.pct_change() * 100
    )

    # V1 note: we intentionally skip 50-day average volume because
    # this version only works with the latest 25 sessions.

    # Exponential moving averages on close price.
    df["ema_10"] = grouped["close_price"].transform(
        lambda series: series.ewm(span=10, adjust=False).mean()
    )
    df["ema_20"] = grouped["close_price"].transform(
        lambda series: series.ewm(span=20, adjust=False).mean()
    )

    # Distribution day:
    # 1) price change <= -0.20%
    # 2) volume > previous day volume
    previous_volume = grouped["volume"].shift(1)
    df["is_distribution_day"] = (
        (df["price_change_pct"] <= -0.20) & (df["volume"] > previous_volume)
    ).astype(int)

    # Rolling count of distribution days in the latest recent window.
    df["distribution_count_25d"] = grouped["is_distribution_day"].transform(
        lambda series: series.rolling(window=RECENT_WINDOW, min_periods=1).sum()
    )
    df["distribution_count_25d"] = df["distribution_count_25d"].astype(int)

    # Accumulated price change over the same recent window.
    # For early rows (<RECENT_WINDOW), we use the first available close as baseline.
    def _accum_change_25(series: pd.Series) -> pd.Series:
        baseline = series.shift(RECENT_WINDOW - 1)
        baseline = baseline.fillna(series.iloc[0])
        return ((series - baseline) / baseline) * 100

    df["price_change_accum_25d"] = grouped["close_price"].transform(_accum_change_25)

    # Keep date as string for easy DB insertion and set sentiment placeholder.
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    df["volume"] = df["volume"].fillna(0).astype(int)
    df["market_sentiment"] = None

    # Final column order, ready for db.upsert_sessions(...)
    final_df = df[
        [
            "symbol",
            "date",
            "close_price",
            "volume",
            "price_change_pct",
            "ema_10",
            "ema_20",
            "is_distribution_day",
            "distribution_count_25d",
            "price_change_accum_25d",
            "market_sentiment",
        ]
    ]

    # Also export one temporary CSV per symbol for debugging/learning purposes.
    export_symbol_csvs(final_df)

    return final_df


def enrich_rows(symbol: str, rows: List[Dict]) -> List[Dict]:
    """
    Backward-compatible wrapper for current V1 flow.
    It converts list[dict] -> DataFrame, runs pandas calculations, and returns list[dict].
    """
    if not rows:
        return []

    market_df = pd.DataFrame(rows)
    market_df["symbol"] = symbol
    final_df = calculate_indicators(market_df)
    return final_df.to_dict(orient="records")
