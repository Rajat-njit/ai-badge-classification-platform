"""
NLP Layer 1 — Exact phrase matching.

All phrases are case-insensitive exact substring matches.
Dictionaries are from .md Section 10 — do not modify without
updating the taxonomy documentation.

PhraseExtractor applies all dictionaries to a BFS and returns
the updated BFS with signal fields populated.

Matching rules:
- Phrases are sorted longest-first so the most specific phrase wins.
  ("foundation-level badge" beats "foundation-level")
- For LEVEL_PHRASES: first match only — stop scanning after one hit.
- For ASSESSMENT_PHRASES: multiple matches allowed (type + threshold).
- For AUDIENCE_PHRASES: first match wins.
- For PURPOSE_PHRASES: multiple matches allowed (purpose + workflow).
"""

from app.models.badge_fact_sheet import BadgeFactSheet


# ---------------------------------------------------------------------------
# LEVEL_PHRASES — from .md Section 10
# Tuple: (level_value, confidence)
# ---------------------------------------------------------------------------
LEVEL_PHRASES: dict[str, tuple[str, str]] = {
    # Foundational
    "foundation-level badge":            ("Foundational", "High"),
    "this foundation-level":             ("Foundational", "High"),
    "foundation-level":                  ("Foundational", "High"),
    "foundational understanding":        ("Foundational", "High"),
    "foundational knowledge":            ("Foundational", "High"),
    "lays the groundwork":               ("Foundational", "High"),
    "build essential":                   ("Foundational", "High"),
    "equips emerging leaders":           ("Foundational", "High"),
    "readiness to begin":                ("Foundational", "High"),
    "introduction to":                   ("Foundational", "Medium"),
    "introductory":                      ("Foundational", "High"),
    "beginner":                          ("Foundational", "High"),
    "entry-level":                       ("Foundational", "High"),
    "entry level":                       ("Foundational", "High"),
    "no prior experience":               ("Foundational", "High"),
    "no experience required":            ("Foundational", "High"),
    "getting started":                   ("Foundational", "Medium"),
    "first step":                        ("Foundational", "Medium"),
    "fundamentals of":                   ("Foundational", "High"),
    "basics of":                         ("Foundational", "Medium"),
    "first in":                          ("Foundational", "Medium"),
    "first course":                      ("Foundational", "High"),

    # Milestone
    "building on foundational concepts": ("Milestone", "High"),
    "building on the foundational series": ("Milestone", "High"),
    "building on foundational":          ("Milestone", "High"),
    "expanding on the foundational series": ("Milestone", "High"),
    "expanding on the foundational":     ("Milestone", "High"),
    "intermediate-level":                ("Milestone", "High"),
    "intermediate credential":           ("Milestone", "High"),
    "intermediate level":                ("Milestone", "High"),
    "deepens skills":                    ("Milestone", "High"),
    "deepens understanding":             ("Milestone", "High"),
    "advances skills":                   ("Milestone", "High"),
    "builds upon":                       ("Milestone", "High"),
    "prior knowledge required":          ("Milestone", "High"),
    "second course":                     ("Milestone", "High"),
    "second in":                         ("Milestone", "High"),
    "continues from":                    ("Milestone", "High"),

    # Terminal
    "after completing the foundational and intermediate": ("Terminal", "High"),
    "comprehensive foundational understanding across all": ("Terminal", "High"),
    "comprehensive achievement":         ("Terminal", "High"),
    "demonstrates comprehensive":        ("Terminal", "High"),
    "demonstrates mastery":              ("Terminal", "High"),
    "completion of all":                 ("Terminal", "High"),
    "upon completing all":               ("Terminal", "High"),
    "culminating the":                   ("Terminal", "High"),
    "completes the series":              ("Terminal", "High"),
    "final course":                      ("Terminal", "High"),
    "capstone":                          ("Terminal", "High"),
}

# Pre-sorted: longest phrase first so the most specific match wins
_LEVEL_PHRASES_SORTED: list[tuple[str, str, str]] = sorted(
    ((phrase, level, conf) for phrase, (level, conf) in LEVEL_PHRASES.items()),
    key=lambda x: len(x[0]),
    reverse=True,
)


# ---------------------------------------------------------------------------
# ASSESSMENT_PHRASES — from .md Section 10
# Tuple: (type_key, threshold_or_None, confidence)
#
# type_key values and how they're used:
#   "final_assessment" | "knowledge_checks" | "pre_post_assessment" |
#   "project_presentation" | "attendance" | "module_completion" | "practical"
#     → sets assessment_type
#   "expert_scored"
#     → sets assessment_evaluator
#   "compliance"
#     → sets badge_purpose (handled also by PURPOSE_PHRASES)
#   "downstream_workflow"
#     → signals a downstream workflow exists (handled also by PURPOSE_PHRASES)
# ---------------------------------------------------------------------------
ASSESSMENT_PHRASES: dict[str, tuple[str, str | None, str]] = {
    "passing the final assessment with an 80% or higher": ("final_assessment", "80%", "High"),
    "passing the final assessment with an 90% or higher": ("final_assessment", "90%", "High"),
    "passing knowledge checks with an 80% or higher":    ("knowledge_checks", "80%", "High"),
    "passing knowledge checks with a 80% or higher":     ("knowledge_checks", "80%", "High"),
    "pre- and post-assessment":  ("pre_post_assessment", None, "High"),
    "pre and post assessment":   ("pre_post_assessment", None, "High"),
    "capstone project and present": ("project_presentation", None, "High"),
    "attend the full":           ("attendance", None, "High"),
    "attended the full":         ("attendance", None, "High"),
    "mandatory to apply":        ("compliance", None, "High"),
    "required to apply":         ("compliance", None, "High"),
    "share their digital badge to": ("downstream_workflow", None, "High"),
    "module quizzes":            ("module_completion", None, "Medium"),
    "in person practical":       ("practical", None, "High"),
    "in-person practical":       ("practical", None, "High"),
    "expert-verified":           ("expert_scored", None, "High"),
    "evaluated by":              ("expert_scored", None, "Medium"),
    "assessed by":               ("expert_scored", None, "Medium"),
}

_ASSESSMENT_PHRASES_SORTED: list[tuple[str, str, str | None, str]] = sorted(
    ((phrase, type_key, threshold, conf)
     for phrase, (type_key, threshold, conf) in ASSESSMENT_PHRASES.items()),
    key=lambda x: len(x[0]),
    reverse=True,
)

# Valid assessment_type values (not special-case signals)
_ASSESSMENT_TYPE_VALUES = {
    "final_assessment", "knowledge_checks", "pre_post_assessment",
    "project_presentation", "attendance", "module_completion", "practical",
}


# ---------------------------------------------------------------------------
# AUDIENCE_PHRASES — from .md Section 10
# Tuple: (audience_type, audience_signal_detail, confidence)
# ---------------------------------------------------------------------------
AUDIENCE_PHRASES: dict[str, tuple[str, str | None, str]] = {
    "faculty and instructors":    ("njit_employee", "faculty", "High"),
    "healthcare professional":    ("external_professional", "healthcare", "High"),
    "f-1 international students": ("njit_student", "international", "High"),
    "f-1 students":               ("njit_student", "international", "High"),
    "working professionals":      ("external_professional", "professional", "High"),
    "international students":     ("njit_student", "international", "High"),
    "njit employees":             ("njit_employee", "staff", "High"),
    "njit students":              ("njit_student", "student", "High"),
    "njit staff":                 ("njit_employee", "staff", "High"),
    "in partnership with":        ("external_partner", None, "High"),
    "workforce":                  ("external_professional", "professional", "Medium"),
    "industry":                   ("external_professional", "professional", "Medium"),
    "clinical":                   ("external_professional", "healthcare", "Medium"),
    "instructor":                 ("njit_employee", "faculty", "Medium"),
    "educator":                   ("njit_employee", "faculty", "Medium"),
    "faculty":                    ("njit_employee", "faculty", "Medium"),
    "students":                   ("njit_student", "student", "Low"),
}

_AUDIENCE_PHRASES_SORTED: list[tuple[str, str, str | None, str]] = sorted(
    ((phrase, aud_type, detail, conf)
     for phrase, (aud_type, detail, conf) in AUDIENCE_PHRASES.items()),
    key=lambda x: len(x[0]),
    reverse=True,
)


# ---------------------------------------------------------------------------
# PURPOSE_PHRASES — from .md Section 10
# Maps phrase → badge_purpose value or "downstream_workflow" sentinel
# ---------------------------------------------------------------------------
PURPOSE_PHRASES: dict[str, str] = {
    "mandatory to apply":          "compliance",
    "required to apply":           "compliance",
    "prerequisite for":            "prerequisite_gate",
    "required before":             "prerequisite_gate",
    "share their digital badge to": "downstream_workflow",
    "share your badge to":         "downstream_workflow",
}

_PURPOSE_PHRASES_SORTED: list[tuple[str, str]] = sorted(
    PURPOSE_PHRASES.items(),
    key=lambda x: len(x[0]),
    reverse=True,
)


# ---------------------------------------------------------------------------
# PhraseExtractor — applies all four dictionaries to a BFS
# ---------------------------------------------------------------------------

class PhraseExtractor:
    """
    Layer 1: case-insensitive exact phrase matching.

    Operates on the concatenation of badge_description and
    earning_criteria_text — the same text surface used by all NLP layers.
    """

    def extract(self, bfs: BadgeFactSheet, text: str) -> BadgeFactSheet:
        lower = text.lower()

        bfs = self._extract_level(bfs, lower)
        bfs = self._extract_assessment(bfs, lower, text)
        bfs = self._extract_audience(bfs, lower)
        bfs = self._extract_purpose(bfs, lower, text)

        return bfs

    # ------------------------------------------------------------------
    # Level signals
    # ------------------------------------------------------------------

    def _extract_level(self, bfs: BadgeFactSheet, lower: str) -> BadgeFactSheet:
        """First match wins — longest phrase has priority."""
        if bfs.self_declared_level is not None:
            # Already set by a structured field — don't overwrite
            return bfs

        for phrase, level, conf in _LEVEL_PHRASES_SORTED:
            if phrase.lower() in lower:
                bfs.self_declared_level = level
                bfs.level_phrase_matched = phrase
                bfs.level_signal_source = "keyword_rule"
                return bfs

        return bfs

    # ------------------------------------------------------------------
    # Assessment signals
    # ------------------------------------------------------------------

    def _extract_assessment(
        self, bfs: BadgeFactSheet, lower: str, original: str
    ) -> BadgeFactSheet:
        """Multiple matches allowed — sets type, threshold, evaluator."""
        for phrase, type_key, threshold, _ in _ASSESSMENT_PHRASES_SORTED:
            if phrase.lower() not in lower:
                continue

            if type_key in _ASSESSMENT_TYPE_VALUES:
                if bfs.assessment_type is None:
                    bfs.assessment_type = type_key
                    bfs.assessment_required = "yes" if type_key != "attendance" else "no"
                if threshold and bfs.assessment_pass_threshold is None:
                    bfs.assessment_pass_threshold = threshold

            elif type_key == "expert_scored":
                if bfs.assessment_evaluator is None:
                    bfs.assessment_evaluator = "expert_scored"

            # compliance and downstream_workflow are handled by _extract_purpose

        return bfs

    # ------------------------------------------------------------------
    # Audience signals
    # ------------------------------------------------------------------

    def _extract_audience(self, bfs: BadgeFactSheet, lower: str) -> BadgeFactSheet:
        """First match wins — longest phrase has priority."""
        if bfs.audience_type is not None:
            return bfs

        for phrase, aud_type, detail, conf in _AUDIENCE_PHRASES_SORTED:
            if phrase.lower() in lower:
                bfs.audience_type = aud_type
                bfs.audience_signal = detail or phrase
                bfs.audience_signal_source = "keyword_rule"
                return bfs

        return bfs

    # ------------------------------------------------------------------
    # Purpose / downstream workflow signals
    # ------------------------------------------------------------------

    def _extract_purpose(
        self, bfs: BadgeFactSheet, lower: str, original: str
    ) -> BadgeFactSheet:
        for phrase, purpose_value in _PURPOSE_PHRASES_SORTED:
            if phrase.lower() not in lower:
                continue

            if purpose_value in ("compliance", "prerequisite_gate"):
                bfs.badge_purpose = purpose_value

            elif purpose_value == "downstream_workflow":
                # Capture text that follows the trigger phrase as the workflow description
                idx = lower.find(phrase.lower())
                if idx != -1:
                    after = original[idx + len(phrase):].strip().rstrip(".")
                    bfs.downstream_workflow = after[:120] if after else "detected"

        return bfs
