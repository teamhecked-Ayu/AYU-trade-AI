from datetime import datetime, timedelta, timezone

from ayuai.backtesting.engine import BacktestEngine
from ayuai.market_data.models import MarketCandle


def candles(prices):
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return [MarketCandle(start + timedelta(hours=i), p, p, p, p, 1) for i, p in enumerate(prices)]


def test_buy_and_hold_backtest_calculates_return():
    def strategy(data, index):
        return "buy" if index == 0 else "hold"

    result = BacktestEngine(initial_cash=1000, fee_rate=0).run(candles([100, 110]), strategy)
    assert result.final_equity == 1100
    assert result.total_return_pct == 10
    assert len(result.trades) == 1


def test_backtest_rejects_invalid_signal():
    def strategy(data, index):
        return "maybe"

    try:
        BacktestEngine().run(candles([100, 101]), strategy)
        assert False, "Expected ValueError"
    except ValueError:
        pass
