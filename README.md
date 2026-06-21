# AYU-trade-AI

AYU-trade-AI is a self-learning, multi-strategy execution engine designed for 24/7 autonomous warfare in the crypto markets.

## Key Features
- **Real-time Data Processing**: Processes terabytes of live data across 20+ exchanges.
- **Deep AI Sentiment Fusion**: Ensemble of FinBERT + VADER for market psychology decoding.
- **Arbitrage Detection**: Sub-second latency for triangular and spatial arbitrage.
- **Advanced Technical Indicators**: 50+ indicators via TA-Lib on tick-level streaming.
- **Institutional Precision**: Aggregates order-book depth, funding rates, and open interest.
- **Professional Risk Management**: Kelly Criterion, trailing stops, and daily loss limits.

## Quick Start
1. **Clone the Repo**: `git clone https://github.com/teamhecked-Ayu/AYU-trade-AI.git`
2. **Setup Environment**: `python -m venv venv && source venv/bin/activate`
3. **Install Dependencies**: `pip install -r requirements.txt`
4. **Configure**: Copy `.env.example` to `.env` and add your API keys.
5. **Launch**: 
   - Interactive: `python cli.py --mode interactive`
   - Daemon: `python daemon.py --exchanges binance --strategies sentiment,technical`

## Architecture
- **Language**: Python 3.11+
- **Concurrency**: Asyncio & WebSockets
- **Decision Layer**: Ensemble signal aggregator with Kalman filtering.
- **Broker Bridge**: CCXT integration for 20+ exchanges.

## License
MIT
