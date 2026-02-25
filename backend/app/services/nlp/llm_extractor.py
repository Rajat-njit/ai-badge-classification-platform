"""
NLP Layer 4 — LLM extractor stub.

Enabled only when USE_LLM=true environment variable is set.
Returns the BFS unchanged until implemented.

.md rules:
- R2: LLM never makes classification decisions
- R3: LLM extracts signals only
- All signals extracted here must be marked source="llm_extraction"

Future implementation notes (.md Section 10):
  1. Only request fields listed in bfs.missing_signals
  2. Return structured JSON only — no prose
  3. Mark every returned signal with source="llm_extraction"
  4. Model: -sonnet-4-6 (current production model)
"""

from app.models.badge_fact_sheet import BadgeFactSheet


class LLMExtractor:
    """
    Stub — returns bfs unchanged.
    Missing signals will trigger follow-up questions in the UI instead.
    """

    def extract(self, bfs: BadgeFactSheet) -> BadgeFactSheet:
        # Stub — no-op until USE_LLM=true and this is implemented
        return bfs
