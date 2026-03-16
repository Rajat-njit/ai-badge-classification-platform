"""
Step 3: Badge Level Classification
Based on NJIT Digital Badge Taxonomy
Author: Prabhath Vipparthi

Decision Factors: Type + Evidence + Cognitive Depth
Output depends on badge type:
    - Souvenir → Souvenir
    - Achievement → Foundational / Milestone / Terminal
    - Skill → Awareness / Application / Mastery
    - Competency → Demonstrated / Integrated / Exemplary
"""

from data.schemas.badge_fact_sheet import BadgeFactSheet, EvidenceType, BloomLevel


def classify_level(badge: BadgeFactSheet, badge_type: str) -> str:
    """
    Determine badge level based on type and evidence.

    Args:
        badge: Normalized badge fact sheet
        badge_type: Result from step2

    Returns:
        Level name as string
    """
    if badge_type == "Souvenir":
        return "Souvenir"

    if badge_type == "Achievement":
        return _classify_achievement_level(badge)

    if badge_type == "Skill":
        return _classify_skill_level(badge)

    if badge_type == "Competency":
        return _classify_competency_level(badge)

    return "Unknown"


def _classify_achievement_level(badge: BadgeFactSheet) -> str:
    """Foundational / Milestone / Terminal based on prerequisites and terminal flag."""
    if badge.is_terminal:
        return "Terminal"
    if badge.prerequisites and len(badge.prerequisites) > 0:
        return "Milestone"
    return "Foundational"


def _classify_skill_level(badge: BadgeFactSheet) -> str:
    """Awareness / Application / Mastery based on Bloom levels."""
    if not badge.bloom_levels:
        # Fallback: look at evidence types
        if any(
            e
            in [EvidenceType.DEMONSTRATION, EvidenceType.PROJECT, EvidenceType.CAPSTONE]
            for e in badge.evidence_required
        ):
            return "Mastery"
        if any(
            e in [EvidenceType.ASSIGNMENT, EvidenceType.QUIZ]
            for e in badge.evidence_required
        ):
            return "Application"
        return "Awareness"

    # Use highest Bloom level present
    if any(l in [BloomLevel.EVALUATE, BloomLevel.CREATE] for l in badge.bloom_levels):
        return "Mastery"
    if any(l in [BloomLevel.APPLY, BloomLevel.ANALYZE] for l in badge.bloom_levels):
        return "Application"
    return "Awareness"


def _classify_competency_level(badge: BadgeFactSheet) -> str:
    """Demonstrated / Integrated / Exemplary based on evidence and description."""
    # Look for leadership or innovation evidence
    if any(
        e in [EvidenceType.LEADERSHIP_EVIDENCE, EvidenceType._360_FEEDBACK]
        for e in badge.evidence_required
    ):
        return "Exemplary"

    # Look for cross-context evidence
    if any(
        e in [EvidenceType.KSA_TAGGED_PORTFOLIO, EvidenceType.CASE_STUDY]
        for e in badge.evidence_required
    ):
        return "Integrated"

    return "Demonstrated"


def get_level_explanation(badge: BadgeFactSheet, badge_type: str, level: str) -> str:
    """Generate explanation for level classification."""
    if badge_type == "Achievement":
        if level == "Foundational":
            return "Foundational level: first in pathway, no prerequisites."
        elif level == "Milestone":
            return f"Milestone level: requires previous badges: {', '.join(badge.prerequisites)}"
        elif level == "Terminal":
            return "Terminal level: final achievement in pathway."

    elif badge_type == "Skill":
        if level == "Awareness":
            return "Awareness level: demonstrates basic understanding (Remember/Understand)."
        elif level == "Application":
            return "Application level: demonstrates task performance (Apply/Analyze)."
        elif level == "Mastery":
            return "Mastery level: demonstrates fluency and problem-solving (Evaluate/Create)."

    elif badge_type == "Competency":
        if level == "Demonstrated":
            return "Demonstrated: verified KSAs in one context."
        elif level == "Integrated":
            return "Integrated: applies KSAs across multiple contexts."
        elif level == "Exemplary":
            return "Exemplary: models or leads the competency."

    return f"Level '{level}' based on evidence and taxonomy rules."
