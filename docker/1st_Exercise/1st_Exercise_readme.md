# Wick Play Screener (Docker Exercise)

## Overview

This is a **simple Docker exercise** using a Python stock screener.

The script scans U.S. stocks and finds **Wick Play** patterns:

* Today’s candle trades inside the **upper wick** of the previous day.

The goal is to practice **Docker basics**, not trading or UI design.

---

## Goals

* Run a Python script inside Docker
* Expose a port to view results in a browser
* Use a **volume** to provide a CSV file
* Apply a **multistage Docker build**
* Run everything from a GitHub repository

---

## Project Structure

```text
/
├── wick-play.py
├── requirements.txt
├── Dockerfile
├── .dockerignore
└── README.md
```

---

## CSV Input

The script requires a CSV file with tickers:

```csv
ticker
AAPL
MSFT
NVDA
```

The CSV is mounted as a **volume** at runtime and is expected at:

```text
/data/r3000_tickers.csv
```

---

## How It Works

1. Read tickers from CSV
2. Download last 2 daily candles
3. Detect Wick Play pattern
4. Show results through a simple web page

---

## Docker Concepts Used

* Image
* Container
* Port exposure
* Volume
* Multistage build

---

## Notes

* Educational project only
* Minimal interface
* No database
* No production intent

---
