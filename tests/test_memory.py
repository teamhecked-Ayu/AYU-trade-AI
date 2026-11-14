from ayuai.memory import PerformanceMemory

def test_decision_outcome_and_agent_score():
    memory = PerformanceMemory()
    decision = memory.record_decision("BTC?", "BUY", 0.7)
    memory.record_outcome(decision.id, 0.05)
    score = memory.record_agent_result("openai", True)
    assert memory.decisions[decision.id].outcome == 0.05
    assert score.accuracy == 1.0
