# 1️⃣ Read tickers from CSV with header and strip spaces

import pandas as pd
import yfinance as yf

tickers = pd.read_csv("r3000_tickers.csv")["ticker"].tolist()
print(f"Total tickers: {len(tickers)}")

batch_size = 100
all_wick_plays = []  # accumulated list of all wick plays

# 2️⃣ Process tickers in batches
for i in range(0, len(tickers), batch_size):
    batch = tickers[i:i+batch_size]
    batch_results = []

    print(f"\nProcessing tickers {i+1} to {i+len(batch)}...")

    # 3️⃣ Iterate through each ticker in the batch
    for ticker in batch:
        try:
            # Download last 2 days of OHLC data
            df = yf.download(ticker, period="2d", interval="1d", progress=False)

            if len(df) < 2:
                continue  # skip if not enough data

            yesterday = df.iloc[-2]
            today = df.iloc[-1]

            # define upper wick range of yesterday
            upper_wick_start = max(yesterday["Open"].item(), yesterday["Close"].item())
            upper_wick_end = yesterday["High"].item()

            # wick play: today's candle within yesterday's upper wick range
            wick_play = (today["Low"].item() >= upper_wick_start) and (today["High"].item() <= upper_wick_end)

            if wick_play:
                batch_results.append(ticker)
                all_wick_plays.append(ticker)

        except Exception as e:
            print(f"Error with {ticker}: {e}")
            continue

    # 4️⃣ Results of the current batch
    if batch_results:
        print("Wick plays in this batch:", batch_results)
    else:
        print("No wick plays in this batch.")

    # 5️⃣ Accumulated results so far
    if all_wick_plays:
        print("Cumulative wick plays so far:", all_wick_plays)

# 6️⃣ Final message
print("\nCheck all the wick plays, chief! Good luck!")


