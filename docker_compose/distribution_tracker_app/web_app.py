from __future__ import annotations

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
import plotly.graph_objects as go
from plotly.io import to_html

from db import (
    get_connection,
    get_latest_sessions_by_symbols,
    get_recent_sessions_by_symbol,
    init_db,
    update_latest_sentiment,
)


app = FastAPI(title="Distribution Tracker")
SYMBOLS = ["SPY", "QQQ"]
SENTIMENT_OPTIONS = ["Bullish", "Neutral", "Bearish"]


@app.on_event("startup")
def startup() -> None:
    """
    Ensure the database table exists when the web app starts.
    """
    conn = get_connection()
    try:
        init_db(conn)
    finally:
        conn.close()


def format_metric(value: object) -> str:
    """
    Format values for the minimal homepage.
    """
    if value is None:
        return "N/A"

    if isinstance(value, float):
        return f"{value:.2f}"

    return str(value)


def build_symbol_chart(symbol: str, rows: list[dict], include_plotly_js: bool) -> str:
    """
    Build a simple Plotly chart for one symbol.
    """
    if not rows:
        return "<p>No chart data available yet.</p>"

    dates = [str(row["date"]) for row in rows]
    close_prices = [row["close_price"] for row in rows]
    ema_10_values = [row["ema_10"] for row in rows]
    ema_20_values = [row["ema_20"] for row in rows]

    figure = go.Figure()
    figure.add_trace(go.Scatter(x=dates, y=close_prices, mode="lines", name="Close"))
    figure.add_trace(go.Scatter(x=dates, y=ema_10_values, mode="lines", name="EMA 10"))
    figure.add_trace(go.Scatter(x=dates, y=ema_20_values, mode="lines", name="EMA 20"))
    figure.update_layout(
        title=f"{symbol} Recent Price",
        height=320,
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h"),
    )

    return to_html(figure, full_html=False, include_plotlyjs=include_plotly_js)


def build_sentiment_form(symbol: str, current_sentiment: object) -> str:
    """
    Build a minimal HTML form to save manual sentiment.
    """
    options_html: list[str] = []
    for option in SENTIMENT_OPTIONS:
        selected = "selected" if current_sentiment == option else ""
        options_html.append(f'<option value="{option}" {selected}>{option}</option>')

    return f"""
    <form method="post" action="/sentiment">
      <input type="hidden" name="symbol" value="{symbol}">
      <label for="sentiment-{symbol}">Sentiment:</label>
      <select id="sentiment-{symbol}" name="sentiment">
        {''.join(options_html)}
      </select>
      <button type="submit">Save</button>
    </form>
    """


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    """
    Minimal server-rendered homepage.
    """
    conn = get_connection()
    try:
        latest_rows = get_latest_sessions_by_symbols(conn, SYMBOLS)
        chart_rows_by_symbol = {
            symbol: get_recent_sessions_by_symbol(conn, symbol, limit=26) for symbol in SYMBOLS
        }
    finally:
        conn.close()

    rows_by_symbol = {row["symbol"]: row for row in latest_rows}
    include_plotly_js = True
    sections: list[str] = []

    for symbol in SYMBOLS:
        row = rows_by_symbol.get(symbol)
        chart_rows = chart_rows_by_symbol.get(symbol, [])
        chart_html = build_symbol_chart(symbol, chart_rows, include_plotly_js)
        if chart_rows:
            include_plotly_js = False

        if row is None:
            sections.append(
                f"""
                <section>
                  <h2>{symbol}</h2>
                  <p>No data available yet.</p>
                  {chart_html}
                </section>
                """
            )
            continue

        sections.append(
            f"""
            <section>
              <h2>{symbol}</h2>
              <p>Latest date: {format_metric(row.get("date"))}</p>
              <p>Distribution count: {format_metric(row.get("distribution_count_25d"))}</p>
              <p>Accumulated price change: {format_metric(row.get("price_change_accum_25d"))}%</p>
              <p>EMA 10: {format_metric(row.get("ema_10"))}</p>
              <p>EMA 20: {format_metric(row.get("ema_20"))}</p>
              <p>Current sentiment: {format_metric(row.get("market_sentiment"))}</p>
              {build_sentiment_form(symbol, row.get("market_sentiment"))}
              {chart_html}
            </section>
            """
        )

    return f"""
    <html>
      <head>
        <title>Distribution Tracker</title>
      </head>
      <body>
        <h1>Distribution Tracker</h1>
        <p>Simple V2 homepage reading the latest SPY and QQQ data from PostgreSQL.</p>
        {''.join(sections)}
      </body>
    </html>
    """


@app.post("/sentiment")
def save_sentiment(symbol: str = Form(...), sentiment: str = Form(...)) -> RedirectResponse:
    """
    Save sentiment and redirect back to the homepage.
    """
    if symbol not in SYMBOLS or sentiment not in SENTIMENT_OPTIONS:
        return RedirectResponse(url="/", status_code=303)

    conn = get_connection()
    try:
        update_latest_sentiment(conn, symbol, sentiment)
    finally:
        conn.close()

    return RedirectResponse(url="/", status_code=303)
