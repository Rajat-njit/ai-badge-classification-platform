"""
NJIT AI-Assisted Digital Badge Classification Tool
Author: Rajat Ravindra Pednekar (rp2348@njit.edu)
Institution: New Jersey Institute of Technology
Capstone Project — Spring 2026

NLP Layer 2 — Regex pattern matching.

Handles paraphrased language that exact phrase matching misses.
All patterns from docs/nlp-phrase-dictionary.md — do not modify without
updating docs/nlp-phrase-dictionary.md.

PatternExtractor only sets fields that Layer 1 (PhraseExtractor) left blank,
so the two layers don't conflict. Signal source is set to "regex_pattern".
"""

import re

from app.models.badge_fact_sheet import BadgeFactSheet


# ---------------------------------------------------------------------------
# LEVEL_PATTERNS
# List of (compiled_regex, level_value, confidence)
# ---------------------------------------------------------------------------
LEVEL_PATTERNS: list[tuple[re.Pattern, str, str]] = [
    # ---- Foundational ----
    (re.compile(
        r"\bno\b.{0,30}\b(?:prior|previous|existing)\b.{0,20}"
        r"\b(?:experience|knowledge|background|prerequisites?)\b",
        re.IGNORECASE),
     "Foundational", "High"),

    (re.compile(
        r"\b(?:perfect|designed|ideal|suited)\b.{0,30}"
        r"\b(?:new|beginning|starting|those new)\b",
        re.IGNORECASE),
     "Foundational", "High"),

    (re.compile(
        r"\bfirst\b.{0,20}\b(?:course|module|badge|step|part|in the series)\b",
        re.IGNORECASE),
     "Foundational", "High"),

    (re.compile(
        r"\b(?:intro(?:duction)?|overview|basics?|fundamentals?)\b.{0,10}"
        r"\b(?:to|of|course)\b",
        re.IGNORECASE),
     "Foundational", "High"),

    (re.compile(r"\b(?:newcomer|novice|beginner|starter)\b", re.IGNORECASE),
     "Foundational", "High"),

    (re.compile(r"\bentry.{0,5}(?:level|point|badge|course)\b", re.IGNORECASE),
     "Foundational", "High"),

    (re.compile(
        r"\b(?:getting started|start(?:ing)? with|first look at|first exposure)\b",
        re.IGNORECASE),
     "Foundational", "Medium"),

    # ---- Milestone ----
    (re.compile(
        r"\b(?:builds?|building)\b.{0,20}\b(?:on|upon)\b.{0,30}"
        r"\b(?:foundation|foundational|previous|prior|existing)\b",
        re.IGNORECASE),
     "Milestone", "High"),

    (re.compile(
        r"\b(?:expands?|expanding)\b.{0,20}\b(?:on|upon)\b.{0,30}"
        r"\b(?:foundation|foundational|skills|knowledge)\b",
        re.IGNORECASE),
     "Milestone", "High"),

    (re.compile(
        r"\b(?:second|third|fourth|2nd|3rd|4th)\b.{0,20}"
        r"\b(?:course|module|step|badge|part|in)\b",
        re.IGNORECASE),
     "Milestone", "High"),

    (re.compile(
        r"\b(?:requires?|requiring)\b.{0,30}"
        r"\b(?:completion|prior|previous|prerequisite)\b",
        re.IGNORECASE),
     "Milestone", "Medium"),

    (re.compile(r"\b(?:continues?|continuing)\b.{0,20}\b(?:from|where)\b",
                re.IGNORECASE),
     "Milestone", "Medium"),

    (re.compile(r"\b(?:intermediate|mid.?level|mid.?course)\b", re.IGNORECASE),
     "Milestone", "High"),

    # ---- Terminal ----
    (re.compile(
        r"\b(?:final|last|culminat(?:ing|es?)|capstone)\b.{0,30}"
        r"\b(?:course|module|badge|step|achievement|experience)\b",
        re.IGNORECASE),
     "Terminal", "High"),

    (re.compile(
        r"\b(?:after|upon|following)\b.{0,20}"
        r"\b(?:completing|finishing|earning)\b.{0,20}"
        r"\b(?:all|the full|every|both)\b",
        re.IGNORECASE),
     "Terminal", "High"),

    (re.compile(
        r"\ball\b.{0,20}"
        r"\b(?:three|four|five|course|module|badge|milestone)\b.{0,20}"
        r"\b(?:required|complete|earned)\b",
        re.IGNORECASE),
     "Terminal", "High"),

    (re.compile(
        r"\bcomprehensive\b.{0,20}"
        r"\b(?:achievement|mastery|understanding|completion)\b",
        re.IGNORECASE),
     "Terminal", "Medium"),

    (re.compile(
        r"\bdemonstrates?\b.{0,20}"
        r"\b(?:mastery|fluency|comprehensive|complete)\b",
        re.IGNORECASE),
     "Terminal", "High"),
]


# ---------------------------------------------------------------------------
# ASSESSMENT_PATTERNS
# List of (compiled_regex, type_key, confidence)
# For patterns with a capture group (threshold %), group 1 is the number.
# ---------------------------------------------------------------------------
ASSESSMENT_PATTERNS: list[tuple[re.Pattern, str, str]] = [
    (re.compile(
        r"\bpassing\b.{0,10}\b(?:final|end.of.course|summative)\b.{0,20}"
        r"\b(?:assessment|exam|test)\b.{0,20}\b(\d+)%",
        re.IGNORECASE),
     "final_assessment", "High"),

    (re.compile(
        r"\bscore\b.{0,20}\b(?:at least|minimum|of)\b.{0,20}"
        r"\b(\d+)\b.{0,10}\b(?:out of|%|percent)\b",
        re.IGNORECASE),
     "scored_assessment", "High"),

    (re.compile(
        r"\b(?:show up|attend(?:ing)?|presence at|participating in)\b.{0,20}"
        r"\b(?:event|session|workshop|forum)\b",
        re.IGNORECASE),
     "attendance", "High"),

    (re.compile(
        r"\bexpert.{0,10}(?:scored|evaluated|assessed|verified|reviewed)\b",
        re.IGNORECASE),
     "expert_scored", "High"),

    (re.compile(
        r"\b(?:faculty|instructor|mentor|supervisor|assessor)\b.{0,20}"
        r"\b(?:evaluat|assess|review|score)\b",
        re.IGNORECASE),
     "expert_scored", "High"),

    (re.compile(
        r"\b(?:portfolio|collection of work|body of work)\b",
        re.IGNORECASE),
     "portfolio", "High"),

    (re.compile(
        r"\b(?:rubric|scoring guide|evaluation criteria)\b",
        re.IGNORECASE),
     "expert_scored", "High"),

    # ---- Explicit "no assessment" indicators ----
    # type_key "no_assessment" is handled separately in _extract_assessment:
    # sets assessment_required="no" and assessment_type="attendance",
    # overriding any previously set "unknown" value.
    (re.compile(
        r"\bno\b.{0,20}\b(?:test|assignment|assessment|evaluation|exam)\b",
        re.IGNORECASE),
     "no_assessment", "High"),

    (re.compile(r"\battendance[\s-]+only\b", re.IGNORECASE),
     "no_assessment", "High"),

    (re.compile(r"\b(?:just|simply)\s+attend\b", re.IGNORECASE),
     "no_assessment", "High"),

    (re.compile(r"\bshow\s+up\b", re.IGNORECASE),
     "no_assessment", "High"),
]

# ---------------------------------------------------------------------------
# BLOOM_PATTERNS
# Used as a lightweight fallback if spaCy is unavailable.
# PatternExtractor does NOT set bloom fields from these — that is
# BloomExtractor's responsibility. They are defined here for completeness.
# ---------------------------------------------------------------------------
BLOOM_PATTERNS: list[tuple[re.Pattern, str, str]] = [
    (re.compile(
        r"\b(?:identify|recall|list|name|define|recognize|state|describe|"
        r"explain|summarize|interpret|classify|compare)\b",
        re.IGNORECASE),
     "understanding", "Medium"),

    (re.compile(
        r"\b(?:apply|use|implement|execute|demonstrate|perform|practice|"
        r"analyze|examine|differentiate|investigate|calculate)\b",
        re.IGNORECASE),
     "applying", "Medium"),

    (re.compile(
        r"\b(?:evaluate|assess|judge|critique|justify|design|create|develop|"
        r"produce|build|construct|lead|mentor|teach)\b",
        re.IGNORECASE),
     "evaluating", "Medium"),
]

# ---------------------------------------------------------------------------
# OR criteria detection
# ---------------------------------------------------------------------------
_OR_PATTERN = re.compile(r"\bor\b", re.IGNORECASE)

# Patterns that use "or" in non-criteria-choice contexts — exclude before
# checking for true alternative earning criteria:
#   "80% or higher/lower"  — threshold specification, not an alternative
#   "no X or Y"             — negation list, not an alternative criterion
_OR_FALSE_POSITIVE = re.compile(
    r"\d+\s*%?\s+or\s+(?:higher|lower|above|more|less|greater)"
    r"|\bno\b.{0,50}\bor\b",
    re.IGNORECASE,
)


def detect_criteria_logic(criteria_text: str) -> str:
    """
    Return "OR" if any sentence in the criteria offers alternative earning
    paths (the word "or" in a context that is not a threshold or negation),
    otherwise return "AND".

    Used to reduce confidence and flag for human review when earning
    criteria offer alternatives (can't verify which was met).
    """
    for sentence in criteria_text.split("."):
        # Strip threshold/negation "or" before checking
        cleaned = _OR_FALSE_POSITIVE.sub("", sentence)
        if _OR_PATTERN.search(cleaned):
            return "OR"
    return "AND"


# ---------------------------------------------------------------------------
# PatternExtractor — applies Level and Assessment patterns
# ---------------------------------------------------------------------------

_ASSESSMENT_TYPE_VALUES = {
    "final_assessment", "knowledge_checks", "pre_post_assessment",
    "project_presentation", "attendance", "module_completion",
    "practical", "portfolio", "scored_assessment",
}


class PatternExtractor:
    """
    Layer 2: regex pattern matching.

    Only fills fields that Layer 1 left as None.
    Sets level_signal_source = "regex_pattern" for any level signal found here.
    """

    def extract(self, bfs: BadgeFactSheet, text: str) -> BadgeFactSheet:
        bfs = self._extract_level(bfs, text)
        bfs = self._extract_assessment(bfs, text)
        bfs = self._extract_criteria_logic(bfs)
        return bfs

    def _extract_level(self, bfs: BadgeFactSheet, text: str) -> BadgeFactSheet:
        """First matching pattern wins. Only runs if Level not already set."""
        if bfs.self_declared_level is not None:
            return bfs

        for pattern, level, conf in LEVEL_PATTERNS:
            m = pattern.search(text)
            if m:
                bfs.self_declared_level = level
                bfs.level_phrase_matched = m.group(0).strip()
                bfs.level_signal_source = "regex_pattern"
                return bfs

        return bfs

    def _extract_assessment(self, bfs: BadgeFactSheet, text: str) -> BadgeFactSheet:
        """Multiple patterns may fire — sets type, threshold, evaluator."""
        for pattern, type_key, _ in ASSESSMENT_PATTERNS:
            m = pattern.search(text)
            if not m:
                continue

            if type_key == "expert_scored":
                if bfs.assessment_evaluator is None:
                    bfs.assessment_evaluator = "expert_scored"

            elif type_key == "no_assessment":
                # Explicit negation of assessment — overrides "unknown" but
                # does not override a previously confirmed "yes".
                if bfs.assessment_required != "yes":
                    bfs.assessment_required = "no"
                if bfs.assessment_type is None:
                    bfs.assessment_type = "attendance"

            elif type_key in _ASSESSMENT_TYPE_VALUES:
                if bfs.assessment_type is None:
                    bfs.assessment_type = type_key
                    bfs.assessment_required = "yes" if type_key != "attendance" else "no"
                # Extract threshold from capture group if present
                if bfs.assessment_pass_threshold is None and m.lastindex:
                    bfs.assessment_pass_threshold = f"{m.group(1)}%"

        return bfs

    def _extract_criteria_logic(self, bfs: BadgeFactSheet) -> BadgeFactSheet:
        if bfs.criteria_logic is None and bfs.earning_criteria_text:
            bfs.criteria_logic = detect_criteria_logic(bfs.earning_criteria_text)
        return bfs
