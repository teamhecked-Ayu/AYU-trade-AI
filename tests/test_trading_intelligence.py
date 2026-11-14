import pandas as pd
from ayuai.trading_intelligence import TradingIntelligence

def test_mixed_market_returns_wait_or_bounded_signal():
    n = 60
    frame = pd.DataFrame({
        "close": [100 + i * 0.1 for i in range(n)],
        "ema_50": [100 + i * 0.08 for i in range(n)],
        "ema_200": [99.0] * n,
        "atr": [1.0] * n,
    })
    report = TradingIntelligence.analyze(frame, 0.3, 0.1)
    assert report.action in {"BUY", "SELL", "WAIT"}
    assert -1 <= report.score <= 1
    assert 0 <= report.confidence <= 1
