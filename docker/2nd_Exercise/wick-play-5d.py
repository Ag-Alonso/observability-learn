# wick-play screening code (last 5 days)

import os
from typing import List, Tuple

import pandas as pd
import yfinance as yf

def find_wick_plays_5d(csv_path: str) -> List[Tuple[str, pd.Series, pd.Series]]:
    """Return list of (ticker, yesterday, today) for each Wick Play in the last 5 days."""
    
    # ✅ Validación de existencia del CSV
    print(f"Looking for CSV at: {csv_path}")
    print(f"CSV exists: {os.path.isfile(csv_path)}")
    
    # Listar contenido del directorio del CSV para debug
    csv_dir = os.path.dirname(csv_path)
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
                # Download last 5 days of OHLC data
                df = yf.download(ticker, period="5d", interval="1d", progress=False)
                
                if len(df) < 2:
                    continue

                # Loop through consecutive days to find wick plays
                for j in range(1, len(df)):
                    yesterday = df.iloc[j - 1]
                    today = df.iloc[j]

                    # define upper wick range of yesterday
                    upper_wick_start = max(yesterday["Open"], yesterday["Close"])
                    upper_wick_end = yesterday["High"]

                    # wick play condition: today closes within yesterday's upper wick
                    wick_play = (today["Low"] >= upper_wick_start) and (today["High"] <= upper_wick_end)
                    
                    if wick_play:
                        batch_results.append(ticker)
                        results.append((ticker, yesterday, today))
                        break  # stop checking this ticker once detected

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
            o, c, h, l = candle["Open"], candle["Close"], candle["High"], candle["Low"]
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
        # ✅ siempre apunta al path del contenedor
        csv_path = os.environ.get("CSV_PATH", "/data/r3000_tickers.csv")
        results = find_wick_plays_5d(csv_path)
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
        # ✅ path absoluto dentro del contenedor
        csv_path = os.environ.get("CSV_PATH", "/data/r3000_tickers.csv")
        _ = find_wick_plays_5d(csv_path)
