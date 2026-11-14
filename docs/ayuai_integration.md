# AYUAI Integration Pipeline

## End-to-end flow

1. Independent provider analysis
2. Structured claim and contradiction analysis
3. Adversarial debate when unresolved issues exist
4. Deterministic decision synthesis

Provider failures are isolated. A final decision is marked for human review when evidence is weak, contradictions remain, debate fails, or no action can be extracted.

## Trading boundary

This pipeline produces analysis only. Market calculations, backtests and paper trading remain separate deterministic modules. No live order execution is enabled by this integration layer.
