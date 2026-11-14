from ayuai.math_engine.quant_engine import QuantEngine

def test_quant_engine_returns_deterministic_metrics():
    prices = [100, 102, 101, 105, 108, 107, 111, 115, 114, 118]
    report = QuantEngine().analyze_prices(prices, simulations=200, horizon=5, seed=42)
    assert report.annualized_volatility >= 0
    assert report.value_at_risk >= 0
    assert report.max_drawdown <= 0
    assert report.monte_carlo["simulations"] == 200

def test_quant_engine_rejects_invalid_prices():
    try:
        QuantEngine().analyze_prices([100, -1, 105])
    except ValueError:
        return
    raise AssertionError("invalid prices must be rejected")
