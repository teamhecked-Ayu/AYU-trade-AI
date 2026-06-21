class RiskManager:
    def __init__(self):
        self.daily_loss = 0
        self.max_daily_loss = 0.05 # 5%

    def validate_signal(self, signal):
        # Implement Kelly Criterion and Risk Checks
        if signal["confidence"] > 0.7 and self.daily_loss < self.max_daily_loss:
            return True
        return False

    def calculate_position_size(self, balance, win_rate, risk_reward):
        # Kelly Criterion: f* = p/a - q/b
        # p = win probability, q = loss probability, b = odds
        p = win_rate
        q = 1 - win_rate
        b = risk_reward
        kelly_f = (p * b - q) / b
        return max(0, kelly_f * 0.5) # Fractional Kelly for safety
