import asyncio

import pytest

from core.broker_bridge import BrokerBridge
from core.paper_portfolio import PaperPortfolio
from core.portfolio_store import SQLitePortfolioStore


@pytest.mark.asyncio
async def test_broker_bridge_and_paper_api_store_share_one_persistent_portfolio(tmp_path):
    path = str(tmp_path / "shared.db")
    engine_store = SQLitePortfolioStore(path)
    api_store = SQLitePortfolioStore(path)
    bridge = BrokerBridge(paper_trade=True, paper_store=engine_store)

    result = await bridge.execute_order(
        exchange_id="paper",
        symbol="BTC/USDT",
        side="buy",
        amount=1,
        price=100,
    )

    assert result["status"] == "paper"
    assert api_store.load().cash < 10_000
    assert api_store.load().positions["BTC/USDT"].quantity == 1
    assert len(api_store.load().trades) == 1


@pytest.mark.asyncio
async def test_injected_in_memory_portfolio_remains_supported():
    portfolio = PaperPortfolio(cash=500, fee_rate=0)
    bridge = BrokerBridge(paper_trade=True, paper_portfolio=portfolio)

    result = await bridge.execute_order(
        exchange_id="test",
        symbol="BTC/USDT",
        side="buy",
        amount=1,
        price=100,
    )

    assert result["status"] == "paper"
    assert portfolio.cash == 400


def test_sqlite_store_execute_is_atomic_and_visible_to_other_instances(tmp_path):
    path = str(tmp_path / "atomic.db")
    first = SQLitePortfolioStore(path)
    second = SQLitePortfolioStore(path)

    first.execute("BTC/USDT", "buy", 2, 100, fee_rate=0)
    second.execute("BTC/USDT", "buy", 1, 50, fee_rate=0)

    loaded = SQLitePortfolioStore(path).load(fee_rate=0)
    assert loaded.cash == 9_750
    assert loaded.positions["BTC/USDT"].quantity == 3
    assert len(loaded.trades) == 2

    with pytest.raises(ValueError):
        first.execute("BTC/USDT", "buy", 1000, 100, fee_rate=0)

    after_failure = second.load(fee_rate=0)
    assert after_failure.cash == 9_750
    assert after_failure.positions["BTC/USDT"].quantity == 3


def test_ayuai_paper_engine_uses_core_portfolio_rules_and_shared_store(tmp_path):
    from ayuai.paper_trading.engine import PaperTradingEngine

    store = SQLitePortfolioStore(str(tmp_path / "ayuai.db"))
    engine = PaperTradingEngine(starting_cash=500, fee_rate=0, store=store)

    trade = engine.buy("ETH/USDT", 2, 100)

    assert trade.side == "buy"
    assert engine.portfolio.cash == 300
    assert store.load(initial_cash=500).positions["ETH/USDT"].quantity == 2
    assert engine.equity({"ETH/USDT": 150}) == 600
