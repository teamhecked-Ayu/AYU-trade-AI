import pytest

from ayuai.paper_trading.engine import PaperTradingEngine
from core.portfolio_store import SQLitePortfolioStore


def test_paper_buy_sell_and_equity_in_memory():
    engine = PaperTradingEngine(starting_cash=1000, fee_rate=0, in_memory=True)
    engine.buy("BTC/USDT", 5, 100)
    assert engine.portfolio.cash == 500
    assert engine.equity({"BTC/USDT": 120}) == 1100
    engine.sell("BTC/USDT", 5, 120)
    assert engine.portfolio.cash == 1100
    assert not engine.portfolio.positions


def test_paper_trade_rejects_insufficient_cash_in_memory():
    engine = PaperTradingEngine(starting_cash=100, in_memory=True)
    with pytest.raises(ValueError):
        engine.buy("BTC/USDT", 2, 100)


def test_default_engine_uses_shared_sqlite_store_and_reloads_between_instances(
    tmp_path,
    monkeypatch,
):
    database_path = tmp_path / "shared-paper.db"
    monkeypatch.setenv("PAPER_PORTFOLIO_DB", str(database_path))

    first = PaperTradingEngine(starting_cash=500, fee_rate=0)
    first.buy("BTC/USDT", 2, 100)

    second = PaperTradingEngine(starting_cash=9999, fee_rate=0)
    assert second.store is not None
    assert second.portfolio.cash == 300
    assert second.portfolio.positions["BTC/USDT"].quantity == 2

    second.buy("ETH/USDT", 1, 50)
    first.equity({"BTC/USDT": 110, "ETH/USDT": 60})
    assert first.portfolio.cash == 250
    assert first.portfolio.positions["ETH/USDT"].quantity == 1


def test_explicit_store_is_used_for_shared_portfolio(tmp_path):
    store = SQLitePortfolioStore(str(tmp_path / "injected.db"))
    engine = PaperTradingEngine(starting_cash=750, fee_rate=0, store=store)

    engine.buy("SOL/USDT", 2, 100)

    reloaded = store.load(initial_cash=750, fee_rate=0)
    assert reloaded.cash == 550
    assert reloaded.positions["SOL/USDT"].quantity == 2


def test_store_and_in_memory_cannot_be_combined(tmp_path):
    store = SQLitePortfolioStore(str(tmp_path / "conflict.db"))
    with pytest.raises(ValueError, match="cannot both"):
        PaperTradingEngine(store=store, in_memory=True)
