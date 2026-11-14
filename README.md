# AYU-trade-AI

AYU-trade-AI is an experimental Python trading-analysis engine with real market-data ingestion, technical indicators, sentiment analysis, deterministic signal aggregation, risk checks, and paper trading.

## Current capabilities

- CCXT-based OHLCV market data
- Pluggable sentiment data provider
- Technical and sentiment signal aggregation
- Deterministic risk validation
- In-memory paper portfolio with trades, positions, cash, and equity calculation
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
python -m unittest discover -s tests
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

The current paper portfolio is in-memory and is not persistent. Live exchange execution requires explicit credentials and additional production hardening.
