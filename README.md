# AYU-trade-AI

AYU-trade-AI is an experimental Python trading-analysis engine with real market-data ingestion, technical indicators, sentiment analysis, deterministic signal aggregation, risk checks, and paper trading.

## Current capabilities

- CCXT-based OHLCV market data
- Pluggable sentiment data provider
- Technical and sentiment signal aggregation
- Deterministic risk validation
- SQLite-persisted paper portfolio with trades, positions, cash, and equity calculation
- Minimal FastAPI health and paper-trading API
- Automated test workflow
- Docker development deployment

## Safety model

Paper trading is enabled by default. This repository does not claim profitable trading performance. Historical tests, simulated results, and AI signals are not guarantees of future outcomes.

## Quick start

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m pytest tests -q
uvicorn api:app --host 0.0.0.0 --port 8000
```

Health check: `GET /health`

## Architecture

```text
Market Data ─┐
             ├─> Technical + Sentiment Signals
News Data ───┘              ↓
                     Signal Aggregator
                            ↓
                       Risk Manager
                            ↓
                    Paper Portfolio/API
```

## Known limitations

Paper portfolio state is persisted locally with SQLite. Live exchange execution requires explicit credentials and additional production hardening. Protected API endpoints require an `AYU_API_KEY`; keep the key in environment configuration and do not expose it in source control.


## Deployment checks

Before deployment:

- Set a strong `AYU_API_KEY` in a local environment file or secret manager.
- Keep `PAPER_TRADE=true` for controlled paper-trading deployments.
- Run `python -m pytest tests -q`.
- Start with Docker using `docker compose up --build`.
- Use `GET /health` for liveness and `GET /ready` for deployment readiness.

The SQLite database is mounted as persistent local storage in the Docker Compose setup. Back up the `data/` directory before upgrades.
