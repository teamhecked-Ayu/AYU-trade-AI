import pytest
from ayuai.paper_trading.engine import PaperTradingEngine


def test_paper_buy_sell_and_equity():
    engine = PaperTradingEngine(starting_cash=1000, fee_rate=0)
    engine.buy("BTC/USDT", 5, 100)
    assert engine.portfolio.cash == 500
    assert engine.equity({"BTC/USDT": 120}) == 1100
    engine.sell("BTC/USDT", 5, 120)
    assert engine.portfolio.cash == 1100
    assert not engine.portfolio.positions


def test_paper_trade_rejects_insufficient_cash():
    engine = PaperTradingEngine(starting_cash=100)
    with pytest.raises(ValueError):
        engine.buy("BTC/USDT", 2, 100)
