# Distribution Days Tracker

## Project Overview

Distribution Days Tracker is a small market analysis application focused on monitoring the short-term health of the market through two major ETFs: **SPY** and **QQQ**.

The application is designed to track **Distribution Days** over the most recent **25 trading sessions**, store the underlying market data in a database, and display the results through a simple frontend with charts and summary metrics.

This project is also part of a broader learning path covering:

- Python
- Docker
- Docker Compose
- databases
- multi-container applications
- persistent and ephemeral volumes

The architecture is intentionally simple at first, but structured in a way that can later evolve into a more scalable setup with Kubernetes and observability tooling.

---

## Distribution Day Definition

In this project, a **Distribution Day** is defined as a session where:

- the closing price falls by **0.20% or more** compared to the previous session
- and the trading volume is **higher than the previous session**

This rule is applied daily to both:

- **SPY**
- **QQQ**

The application also tracks the **total number of Distribution Days in the last 25 sessions**, which can be used as a simple market pressure / risk signal.

---

## Project Objectives

The application should:

- collect and store market data for **SPY** and **QQQ**
- calculate Distribution Days automatically
- track the rolling number of Distribution Days over the latest 25 sessions
- store historical data in a database
- display recent market data in a frontend
- show charts for the latest 25 sessions
- include **10-day EMA** and **20-day EMA**
- store additional context for future market analysis
- create a structured dataset that may later support trading research or agent development

---

## Core Features

### Daily Market Data
For each symbol and session, the application should track:

- date
- close price
- daily volume
- 50-day average volume
- daily price change percentage
- 10-day EMA
- 20-day EMA
- Distribution Day status
- rolling Distribution Day count over the last 25 sessions
- accumulated price variation over the last 25 sessions

---

### Initial Historical Load
The system will perform a **one-time initial load of the last 90 trading days**.

This initial load is meant to:

- avoid starting with an empty database
- provide enough historical context to calculate:
  - 50-day average volume
  - 10-day EMA
  - 20-day EMA
  - rolling Distribution Day counts
- establish a meaningful starting point before daily updates begin

After this initial backfill, the application will continue operating on a day-by-day basis.

---

### Frontend
The frontend should provide a lightweight market dashboard including:

- a chart for **SPY**
- a chart for **QQQ**
- the latest **25 trading sessions**
- price action
- 10-day EMA
- 20-day EMA
- Distribution Day markers or indicators
- total Distribution Day count over the latest 25 sessions
- accumulated price variation over the same period

Because the visible window is limited to 25 sessions, charting should remain simple and efficient.

---

### Manual Market Sentiment Input
The frontend will also include a simple manual sentiment input so the user can record a short-term market view for the day.

Available values:

- **Bullish**
- **Neutral**
- **Bearish**

This creates a small layer of subjective market context that can later be compared against the objective market data stored by the system.

Potential future uses include:

- market journaling
- decision review
- pattern recognition
- agent training

---

## Data Model

At a minimum, the database should store the following fields for each symbol and session:

- `symbol`
- `date`
- `close_price`
- `volume`
- `volume_ma_50`
- `price_change_pct`
- `ema_10`
- `ema_20`
- `is_distribution_day`
- `distribution_count_25d`
- `price_change_accum_25d`
- `market_sentiment`

This structure creates a useful historical dataset that may later support:

- market review
- custom filters
- trading analysis
- automation
- AI / agent experimentation

---

## Architecture

This project starts as a **two-container Docker Compose application**.

### 1. Application Container
The application container runs the Python app and contains the main business logic.

Its responsibilities include:

- retrieving market data for SPY and QQQ
- calculating:
  - daily price change
  - 50-day average volume
  - 10-day EMA
  - 20-day EMA
  - Distribution Day status
  - rolling 25-day Distribution Day count
  - accumulated 25-day price variation
- performing the initial 90-day historical load
- updating the system with new daily sessions
- serving the frontend and/or API
- handling manual sentiment input

This container is responsible for **processing and application logic**.

### 2. Database Container
The database container runs the database service, most likely PostgreSQL.

Its responsibilities include storing:

- historical prices
- historical volumes
- calculated indicators
- Distribution Day flags
- rolling counts
- accumulated price variation
- user sentiment entries

This container is responsible for **persistent storage**.

### Container Interaction
Both containers are connected through Docker Compose.

The workflow is simple:

1. the application container retrieves and processes market data
2. the application container calculates the required indicators
3. the application container writes results into the database container
4. the frontend displays processed data through the application layer
5. the database keeps the historical state of the project across restarts

This gives the project a clear and realistic multi-container structure:

- one container for **logic**
- one container for **data**

---

## Volume Management

The project uses both **persistent** and **ephemeral** volumes.

### Persistent Volume
The persistent volume is attached to the database container.

It stores long-term project data, including:

- historical price data
- historical volume data
- calculated indicators
- Distribution Day history
- rolling counts
- sentiment inputs

This ensures that all important data survives container restarts.

### Ephemeral Volume
The ephemeral volume is used by the application container for temporary processing tasks.

Typical uses include:

- intermediate calculation files
- temporary datasets used during updates
- short-lived processing artifacts
- temporary chart-related files if needed

This data is not meant to be stored permanently. If the container restarts, this temporary data can be discarded safely without affecting the historical database.

This separation helps distinguish between:

- **temporary processing data**
- **persistent application data**

It also supports the Docker Compose learning goal of working with both ephemeral and persistent storage.

---

## Why This Project

## Current Implementation (Step 1)

The first working slice includes:

- Docker Compose with two services: `app` and `db`
- PostgreSQL as persistent storage (named volume: `pg_data`)
- App ephemeral storage volume (named volume: `app_tmp`)
- Minimal Python API with DB bootstrap and table creation
- Endpoints:
  - `GET /health`
  - `POST /sessions`
  - `GET /sessions?symbol=SPY&limit=25`

### Run

From project root (`docker_compose`):

```bash
docker compose up --build
```

### Quick Test

```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/sessions -H "Content-Type: application/json" -d "{\"symbol\":\"SPY\",\"date\":\"2026-03-05\",\"close_price\":505.12,\"volume\":72345678}"
curl "http://localhost:8000/sessions?symbol=SPY&limit=25"
```

This project was chosen because it combines:

- a real use case from a daily trading routine
- a simple but meaningful market rule
- structured historical data
- a database-backed application
- frontend charting and summaries
- clear Docker Compose requirements
- future scalability into Kubernetes and observability

It keeps the domain logic focused while still providing enough engineering depth to practice real system design concepts.

---

## Future Direction

This project is expected to evolve over time.

Possible future improvements include:

- scheduled daily updates
- a cleaner API layer
- improved frontend views
- logging, metrics, and tracing
- observability instrumentation
- Kubernetes deployment
- a worker process for background jobs
- integration with a future trading agent

The long-term goal is for this project to become both:

1. a learning platform for containers and observability
2. a useful personal market-tracking tool
