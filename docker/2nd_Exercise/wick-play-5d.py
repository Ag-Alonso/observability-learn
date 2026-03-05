# wick-play screening code (last 5 days)

import os
from typing import List, Tuple

import pandas as pd
import yfinance as yf


def find_wick_plays_5d(csv_path: str) -> List[Tuple[str, pd.Series, pd.Series]]:
    """Return list of (ticker, yesterday, today) for each Wick Play in the last 5 days."""

    # CSV validation & diagnostics
    print(f"Looking for CSV at: {csv_path}")
    print(f"CSV exists: {os.path.isfile(csv_path)}")
    csv_dir = os.path.dirname(csv_path) or "."
    if os.path.isdir(csv_dir):
        print(f"Files in {csv_dir}: {os.listdir(csv_dir)}")
    else:
        print(f"Directory does not exist: {csv_dir}")

    if not os.path.isfile(csv_path):
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    tickers = pd.read_csv(csv_path)["ticker"].astype(str).str.strip().tolist()
    print(f"Total tickers: {len(tickers)}")

    results: List[Tuple[str, pd.Series, pd.Series]] = []
    batch_size = 100

    for i in range(0, len(tickers), batch_size):
        batch = tickers[i : i + batch_size]
        batch_results: List[str] = []
        print(f"\nProcessing tickers {i+1} to {i+len(batch)}...")

        for ticker in batch:
            try:
                # Download with timeout to skip hanging requests
                df = yf.download(ticker, period="5d", interval="1d", progress=False, timeout=5)
                if df is None or len(df) < 2:
                    continue

                # Convert to float array once
                try:
                    ohlc = df[["Open", "Close", "High", "Low"]].astype(float).values
                except:
                    continue

                for j in range(1, len(ohlc)):
                    o_y, c_y, h_y, _ = ohlc[j - 1]
                    _, _, _, l_t = ohlc[j]
                    h_t = ohlc[j][2]

                    upper_start = max(o_y, c_y)
                    if (l_t >= upper_start) and (h_t <= h_y):
                        batch_results.append(ticker)
                        results.append((ticker, df.iloc[j - 1], df.iloc[j]))
                        break

            except Exception:
                continue

        if batch_results:
            print("Wick plays in this batch:", batch_results)
        else:
            print("No wick plays in this batch.")

        if results:
            print("Cumulative wick plays so far:", [r[0] for r in results])

    print("\nCheck all the wick plays, chief! Good luck!")
    return results


# --- Flask interface ------------------------------------------------
try:
    from flask import Flask, render_template_string
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    import io, base64

    app = Flask(__name__)

    def candle_image(yesterday, today):
        fig, ax = plt.subplots(figsize=(2, 1.5))
        for idx, candle in enumerate((yesterday, today)):
            o = float(candle["Open"])
            c = float(candle["Close"])
            h = float(candle["High"])
            l = float(candle["Low"])
            color = "green" if c >= o else "red"
            ax.add_patch(patches.Rectangle((idx - 0.3, min(o, c)), 0.6, abs(c - o) or 0.01, color=color))
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
        try:
            results = find_wick_plays_5d(csv_path)
        except Exception as e:
            return f"<pre>Error: {e}</pre>", 500
        template = """
        <html><head><title>Wick Plays (5D)</title></head><body>
        <h1>Wick Play candidates (Last 5 Days)</h1>
        {% if results %}
          <ul>
          {% for t, y, td in results %}
            <li><strong>{{t}}</strong><br>
                <img src="{{candle_image(y,td)}}" alt="{{t}}"></li>
          {% endfor %}
          </ul>
        {% else %}
          <p>No matches found.</p>
        {% endif %}
        </body></html>"""
        return render_template_string(template, results=results, candle_image=candle_image)

except ImportError:
    app = None


# ----------------------------------------------------------------------------
if __name__ == "__main__":
    if app is not None:
        port = int(os.environ.get("PORT", "5000"))
        app.run(host="0.0.0.0", port=port)
    else:
        csv_path = os.environ.get("CSV_PATH", "/data/r3000_tickers.csv")
        _ = find_wick_plays_5d(csv_path)
