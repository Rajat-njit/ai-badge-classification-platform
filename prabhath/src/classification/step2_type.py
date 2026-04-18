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
    # Priority 1: No assessment = Souvenir (attendance/participation only)
    if not badge.has_assessment:
        return "Souvenir"

    # Priority 2: Makerspace workshop badges (Make 101, 102, 103, 242) = Skill
    if badge.issuing_department and "makerspace" in badge.issuing_department.lower():
        if badge.badge_name and "make " in badge.badge_name.lower():
            return "Skill"

    # Priority 3: Check description keywords before assessment type
    # This catches special cases even with auto_graded assessment type
    if badge.assessment_description:
        desc = badge.assessment_description.lower()
        # Multi-dimension indicators = Competency
        if "competency" in desc or "ksa" in desc or "real-world" in desc or "(or)" in desc:
            return "Competency"
        # Skill indicators
        if "skill" in desc or "demonstrate" in desc or "lab" in desc or "workshop" in desc:
            return "Skill"

    if badge.assessment_type == AssessmentType.AUTO:
        return "Achievement"

    if badge.assessment_type == AssessmentType.EXPERT_SKILL:
        return "Skill"

    if badge.assessment_type == AssessmentType.EXPERT_MULTI:
        return "Competency"

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
