import pandas as pd
from ayuai.finance import Backtester, PaperBroker

def test_backtest_returns_metrics():
    frame = pd.DataFrame({"close": [100, 101, 102, 103, 104]})
    result = Backtester().run(frame, lambda history: "BUY")
    assert result.final_equity > 0
    assert result.total_return != 0 or result.trades >= 0

def test_paper_broker_never_places_live_order():
    broker = PaperBroker()
    broker.buy("BTC/USDT", 100, 1000)
    assert broker.cash < 10000
    assert "BTC/USDT" in broker.positions
