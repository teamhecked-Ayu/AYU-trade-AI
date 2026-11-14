from ayuai.risk.engine import RiskEngine, TradeRequest


def request(**changes):
    data = dict(symbol="BTC/USDT", side="buy", quantity=0.1, entry_price=1000, stop_loss=980, take_profit=1040)
    data.update(changes)
    return TradeRequest(**data)


def test_approves_trade_inside_all_limits():
    decision = RiskEngine().evaluate(request(), portfolio_equity=10_000)
    assert decision.approved
    assert decision.risk_reward_ratio == 2


def test_rejects_oversized_position():
    decision = RiskEngine().evaluate(request(quantity=2), portfolio_equity=10_000)
    assert not decision.approved


def test_rejects_invalid_stop_loss():
    decision = RiskEngine().evaluate(request(stop_loss=1010), portfolio_equity=10_000)
    assert not decision.approved


def test_rejects_excessive_risk():
    decision = RiskEngine().evaluate(request(quantity=5), portfolio_equity=10_000)
    assert not decision.approved
