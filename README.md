# AYU-trade-AI

AYU-trade-AI is a production-grade, self-learning, multi-strategy execution engine designed for 24/7 autonomous warfare in the crypto and equity markets.

## 🚀 Stability Verified
The engine has been rigorously tested in a sandbox environment. Core functionalities including **FinBERT Sentiment Fusion**, **TA-Lib Technical Analysis**, and the **Kalman Filter Signal Aggregator** are confirmed stable and operational.

## Key Features
- **Real-time Data Processing**: Processes terabytes of live data across 20+ exchanges.
- **Deep AI Sentiment Fusion**: Ensemble of FinBERT + VADER for market psychology decoding.
- **Arbitrage Detection**: Sub-second latency for triangular and spatial arbitrage.
- **Advanced Technical Indicators**: 50+ indicators via TA-Lib on tick-level streaming.
- **Institutional Precision**: Aggregates order-book depth, funding rates, and open interest.
- **Professional Risk Management**: Kelly Criterion, trailing stops, and daily loss limits.
- **Stylish Dashboard**: Interactive CLI UI built with `Rich` for real-time monitoring.

## 🚀 Quick Start
For detailed OS-specific instructions (Linux, macOS, Windows), see [INSTALL.md](docs/INSTALL.md).

1. **Clone & Setup**:
   ```bash
   git clone https://github.com/teamhecked-Ayu/AYU-trade-AI.git
   cd AYU-trade-AI
   python -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Launch the Oracle**:
   - **Interactive Dashboard**: `python cli.py --mode interactive`
   - **Headless Daemon**: `python cli.py --mode daemon`

## Architecture
- **Language**: Python 3.11+
- **Concurrency**: Asyncio & WebSockets
- **Decision Layer**: Ensemble signal aggregator with Kalman filtering.
- **Broker Bridge**: CCXT integration for 20+ exchanges and KiteConnect for equity.

## License
MIT
