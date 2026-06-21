# AYU-trade-AI Architecture

## 1. Data Ingestion Layer
- **WebSockets**: Real-time tick-level streaming from 20+ exchanges via CCXT.
- **Scrapers**: Deep sentiment scraping using `BeautifulSoup` and `Requests` for Twitter, Reddit, and News.

## 2. Decision Layer (The Brain)
- **Sentiment Fusion**: Ensemble of FinBERT (Transformer-based) and VADER (Rule-based).
- **Technical Analysis**: Over 50 indicators computed via `TA-Lib`.
- **Signal Aggregator**: A multi-input consensus engine using **Kalman Filtering** to minimize market noise.

## 3. Risk & Execution Layer
- **Risk Manager**: Position sizing via **Kelly Criterion**, daily drawdown limits, and trailing stop-loss logic.
- **Broker Bridge**: Unified interface for CEXs (Binance, Kraken) and Indian Brokers (Zerodha, Angel One).

## 4. Performance
- **Asynchronous**: Built on `Python 3.11 asyncio` for non-blocking I/O.
- **Latency**: Sub-50ms execution pipeline.
