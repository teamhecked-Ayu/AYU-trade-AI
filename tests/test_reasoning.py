from ayuai.providers.base import ProviderResponse
from ayuai.reasoning.reasoning_engine import ReasoningEngine

def test_reasoning_detects_conflicting_actions():
    responses = [
        ProviderResponse("a", "test", "CONCLUSION\nBUY now\nKEY CLAIMS\nTrend is positive\nASSUMPTIONS\nData is current\nRISKS\nVolatility\nUNCERTAINTIES\nNews"),
        ProviderResponse("b", "test", "CONCLUSION\nWAIT for confirmation\nKEY CLAIMS\nTrend is positive\nASSUMPTIONS\nData is current\nRISKS\nVolatility\nUNCERTAINTIES\nNews"),
    ]
    report = ReasoningEngine().analyze(responses)
    assert report.contradictions
    assert report.agreements
