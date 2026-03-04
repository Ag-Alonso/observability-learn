# 1️⃣ Read tickers from CSV with header and strip spaces

import os
from typing import List, Tuple

import pandas as pd
import yfinance as yf


def find_wick_plays(csv_path: str) -> List[Tuple[str, pd.Series, pd.Series]]:
    """Return list of (ticker, yesterday, today) for each Wick Play."""
    tickers = (
        pd.read_csv(csv_path)["ticker"].astype(str).str.strip().tolist()
    )
    print(f"Total tickers: {len(tickers)}")

    results: List[Tuple[str, pd.Series, pd.Series]] = []
    batch_size = 100

    for i in range(0, len(tickers), batch_size):
        batch = tickers[i : i + batch_size]
        batch_results: List[str] = []
        print(f"\nProcessing tickers {i+1} to {i+len(batch)}...")

        for ticker in batch:
            try:
                df = yf.download(ticker, period="2d", interval="1d", progress=False)
                if len(df) < 2:
                    continue

                yesterday = df.iloc[-2]
                today = df.iloc[-1]

                upper_wick_start = max(yesterday["Open"], yesterday["Close"])
                upper_wick_end = yesterday["High"]
                wick_play = (today["Low"] >= upper_wick_start) and (
                    today["High"] <= upper_wick_end
                )
                if wick_play:
                    batch_results.append(ticker)
                    results.append((ticker, yesterday, today))

            except Exception as e:
                print(f"Error with {ticker}: {e}")
                continue

        if batch_results:
            print("Wick plays in this batch:", batch_results)
        else:
            print("No wick plays in this batch.")

        if results:
            print("Cumulative wick plays so far:", [r[0] for r in results])

    print("\nCheck all the wick plays, chief! Good luck!")
    return results


# --- optional Flask interface ------------------------------------------------
try:
    from flask import Flask, render_template_string
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    import io, base64

    app = Flask(__name__)

    def candle_image(yesterday, today):
        fig, ax = plt.subplots(figsize=(2, 1.5))
        for idx, candle in enumerate((yesterday, today)):
            o, c, h, l = (
                candle["Open"],
                candle["Close"],
                candle["High"],
                candle["Low"],
            )
            color = "green" if c >= o else "red"
            ax.add_patch(
                patches.Rectangle(
                    (idx - 0.3, min(o, c)), 0.6, abs(c - o) or 0.01, color=color
                )
            )
            ax.plot([idx, idx], [l, h], color="black")
        ax.set_xlim(-0.5, 1.5)
        ax.axis("off")
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=80)
        plt.close(fig)
        buf.seek(0)
        return "data:image/png;base64," + base64.b64encode(buf.read()).decode()

    @app.route("/")
    def index():
        csv_path = os.environ.get("CSV_PATH", "/data/r3000_tickers.csv")
        results = find_wick_plays(csv_path)
        template = """
        <html><head><title>Wick Plays</title></head><body>
        <h1>Wick Play candidates</h1>
        {% if results %}
          <ul>
          {% for t, y, td in results %}
            <li><strong>{{t}}</strong><br>
                <img src="{{candle_image(y,td)}}" alt="{{t}}"></li>
          {% endfor %}
          </ul>
        {% else %}
          <p>No matches today.</p>
        {% endif %}
        </body></html>"""
        return render_template_string(
            template, results=results, candle_image=candle_image
        )

except ImportError:
    app = None


# ----------------------------------------------------------------------------
if __name__ == "__main__":
    if app is not None:
        port = int(os.environ.get("PORT", "5000"))
        app.run(host="0.0.0.0", port=port)
    else:
        csv_path = os.environ.get("CSV_PATH", "/data/r3000_tickers.csv")
        _ = find_wick_plays(csv_path)


