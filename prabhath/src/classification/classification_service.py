"""
Classification Service
Main entry point for badge classification from Tanay's API.

This module provides the bridge between external API calls and the
internal classification pipeline.

Author: Prabhath Vipparthi
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from typing import Dict, Any, Optional
from dataclasses import dataclass

from src.adapters.schema_converter import tanay_to_prabhath
from data.schemas.badge_fact_sheet import create_fact_sheet_from_dict
from src.classification.step1_category import classify_category, get_category_explanation
from src.classification.step2_type import classify_type, get_type_explanation
from src.classification.step3_level import classify_level, get_level_explanation


@dataclass
class ClassificationResult:
    """Result of badge classification."""
    badge_name: str
    category: str
    type: str
    level: str
    category_explanation: str
    type_explanation: str
    level_explanation: str
    confidence: float
    raw_input: Dict[str, Any]


def classify_badge_from_tanay(tanay_input: Any) -> ClassificationResult:
    """
    Main API endpoint for classifying badges from Tanay's service.

    Args:
        tanay_input: Pydantic model from Tanay's API (BadgeFactSheet or dict)

    Returns:
        ClassificationResult with full classification and explanations

    Example:
        >>> from pydantic import BaseModel
        >>> class TanayBadge(BaseModel):
        ...     title: str
        ...     description: str
        ...     issuer: str
        >>> tanay_badge = TanayBadge(title="AI Badge", description="Learn AI", issuer="LDI")
        >>> result = classify_badge_from_tanay(tanay_badge)
        >>> print(result.category)  # "Faculty & Staff Development"
    """
    # Step 1: Convert Tanay's schema to Prabhath's schema
    prabhath_dict = tanay_to_prabhath(tanay_input)

    # Step 2: Create BadgeFactSheet
    fact_sheet = create_fact_sheet_from_dict(prabhath_dict)

    # Step 3: Run 3-step classification pipeline
    category = classify_category(fact_sheet)
    badge_type = classify_type(fact_sheet)
    level = classify_level(fact_sheet, badge_type)

    # Step 4: Get explanations
    category_explanation = get_category_explanation(fact_sheet, category)
    type_explanation = get_type_explanation(fact_sheet, badge_type)
    level_explanation = get_level_explanation(fact_sheet, badge_type, level)

    # Step 5: Calculate confidence (simple heuristic for now)
    confidence = _calculate_confidence(category, badge_type, level, fact_sheet)

    return ClassificationResult(
        badge_name=fact_sheet.badge_name,
        category=category,
        type=badge_type,
        level=level,
        category_explanation=category_explanation,
        type_explanation=type_explanation,
        level_explanation=level_explanation,
        confidence=confidence,
        raw_input=prabhath_dict,
    )


def classify_from_dict(input_dict: Dict[str, Any]) -> ClassificationResult:
    """
    Alternative entry point for raw dictionary input.

    Args:
        input_dict: Dictionary with Tanay's schema fields

    Returns:
        ClassificationResult
    """
    # Create a simple object with attributes from dict
    class SimpleNamespace:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    tanay_obj = SimpleNamespace(**input_dict)
    return classify_badge_from_tanay(tanay_obj)


def _calculate_confidence(category: str, badge_type: str, level: str, fact_sheet) -> float:
    """
    Calculate confidence score based on classification completeness.

    Higher confidence when:
    - Category is not "Unknown"
    - Type is not default "Achievement" (has clear indicators)
    - Level has pathway data or evidence
    """
    confidence = 0.7  # Base confidence

    # Boost if category is determined (not Unknown)
    if category and not category.startswith("Unknown"):
        confidence += 0.1

    # Boost if type has clear indicators (not default)
    if badge_type != "Achievement" or fact_sheet.assessment_type:
        confidence += 0.1

    # Boost if level has pathway data
    if fact_sheet.pathway_position or (fact_sheet.prerequisites and len(fact_sheet.prerequisites) > 0):
        confidence += 0.1

    return min(confidence, 1.0)


# For direct testing
if __name__ == "__main__":
    # Example usage
    test_input = {
        "title": "AI for Administrative Efficiency",
        "description": "Learn AI for admin tasks",
        "issuer": "LDI",
        "audience": "faculty",
        "context": "employee_development",
        "assessment_type": "auto_graded",
        "assessment_present": True,
        "evidence_type": ["attendance_record"],
        "evidence_present": True,
        "bloom_level_indicators": ["apply"],
    }

    result = classify_from_dict(test_input)
    print(f"Badge: {result.badge_name}")
    print(f"Category: {result.category}")
    print(f"Type: {result.type}")
    print(f"Level: {result.level}")
    print(f"Confidence: {result.confidence:.1%}")
