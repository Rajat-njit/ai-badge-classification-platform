"""
Step 1: Badge Category Classification
Based on NJIT Digital Badge Taxonomy
Author: Prabhath Vipparthi

Decision Factors: Audience + Context
Output: One of four categories:
    - Academic
    - Co-Curricular and Extra-Curricular
    - Continuing & Professional Education
    - Faculty & Staff Development
"""

from typing import Optional
from data.schemas.badge_fact_sheet import BadgeFactSheet, Audience, Context


def classify_category(badge: BadgeFactSheet) -> str:
    """
    Determine badge category based on audience and context.

    Args:
        badge: Normalized badge fact sheet

    Returns:
        Category name as string
    """
    # Special case: OGI issuer requires manual review (Open Question Q001)
    if badge.issuing_department and "OGI" in badge.issuing_department:
        return "Unknown - Open Question Q001"

    # Academic: students + academic context
    if badge.context == Context.ACADEMIC and any(
        a in [Audience.STUDENT] for a in badge.audience
    ):
        return "Academic"

    # Co-Curricular: students + co-curricular context
    if badge.context == Context.CO_CURRICULAR and any(
        a in [Audience.STUDENT] for a in badge.audience
    ):
        return "Co-Curricular and Extra-Curricular"

    # Continuing & Professional Education: external/professional audience + professional_ed context
    if badge.context == Context.PROFESSIONAL_ED and any(
        a in [Audience.EXTERNAL, Audience.PROFESSIONAL] for a in badge.audience
    ):
        return "Continuing & Professional Education"

    # Faculty & Staff Development: faculty/staff audience + employee_development context
    if badge.context == Context.EMPLOYEE_DEV and any(
        a in [Audience.FACULTY, Audience.STAFF] for a in badge.audience
    ):
        return "Faculty & Staff Development"

    # Default/fallback (should not happen with valid data)
    return "Uncategorized"


def get_category_explanation(badge: BadgeFactSheet, category: str) -> str:
    """Generate human-readable explanation for the classification."""
    audience_str = ", ".join([a.value for a in badge.audience])
    context_str = badge.context.value if badge.context else "unknown"

    return (
        f"Category '{category}' determined by:\n"
        f"- Audience: {audience_str}\n"
        f"- Context: {context_str}\n"
        f"Based on NJIT Taxonomy Step 1 rules."
    )
