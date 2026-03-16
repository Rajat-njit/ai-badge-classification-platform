"""
Step 2: Badge Type Classification
Based on NJIT Digital Badge Taxonomy
Author: Prabhath Vipparthi

Decision Factors: Criteria + Assessment
Output: One of four types:
    - Souvenir
    - Achievement
    - Skill
    - Competency
"""

from data.schemas.badge_fact_sheet import BadgeFactSheet, AssessmentType


def classify_type(badge: BadgeFactSheet) -> str:
    """
    Determine badge type based on assessment presence and type.

    Args:
        badge: Normalized badge fact sheet

    Returns:
        Type name as string
    """
    if not badge.has_assessment:
        return "Souvenir"

    if badge.assessment_type == AssessmentType.AUTO:
        return "Achievement"

    if badge.assessment_type == AssessmentType.EXPERT_SKILL:
        return "Skill"

    if badge.assessment_type == AssessmentType.EXPERT_MULTI:
        return "Competency"

    # Fallback based on description keywords (simple rule)
    if badge.assessment_description:
        desc = badge.assessment_description.lower()
        # Check more specific terms first
        if "competency" in desc or "ksa" in desc:
            return "Competency"
        if "skill" in desc or "demonstrate" in desc:
            return "Skill"
        if "quiz" in desc or "assignment" in desc:
            return "Achievement"

    return "Achievement"  # default


def get_type_explanation(badge: BadgeFactSheet, badge_type: str) -> str:
    """Generate explanation for type classification."""
    if not badge.has_assessment:
        return "Type 'Souvenir' because no assessment is required (attendance/participation only)."

    if badge.assessment_type:
        return (
            f"Type '{badge_type}' determined by assessment type: {badge.assessment_type.value}.\n"
            f"Based on NJIT Taxonomy Step 2 rules."
        )

    return f"Type '{badge_type}' inferred from description."
