"""
Schema Converter
Converts between Tanay's Pydantic schema and Prabhath's dataclass schema.

This module provides bidirectional conversion between:
- Tanay's BadgeFactSheet (Pydantic, loose types)
- Prabhath's BadgeFactSheet (dataclass, strict Enums)

Author: Prabhath Vipparthi
"""

from typing import List, Optional, Dict, Any


def _normalize_string(value: Optional[str]) -> Optional[str]:
    """Normalize string to lowercase for comparison."""
    if not value:
        return None
    return value.lower().strip()


def _convert_audience(audience_str: Optional[str]) -> List[str]:
    """Convert Tanay's audience string to Prabhath's Audience enum values."""
    if not audience_str:
        return []

    normalized = _normalize_string(audience_str)

    # Map Tanay's audience strings to Prabhath's enum values
    audience_map = {
        "student": "student",
        "students": "student",
        "faculty": "faculty",
        "staff": "staff",
        "external": "external",
        "professional": "professional",
        "alumni": "alumni",
    }

    if normalized in audience_map:
        return [audience_map[normalized]]
    return []


def _convert_context(context_str: Optional[str]) -> Optional[str]:
    """Convert Tanay's context string to Prabhath's Context enum value."""
    if not context_str:
        return None

    normalized = _normalize_string(context_str)

    # Map Tanay's context strings to Prabhath's enum values
    context_map = {
        "academic": "academic",
        "co_curricular": "co_curricular",
        "co-curricular": "co_curricular",
        "professional_ed": "professional_ed",
        "professional education": "professional_ed",
        "employee_development": "employee_development",
        "employee development": "employee_development",
    }

    return context_map.get(normalized)


def _convert_assessment_type(assessment_str: Optional[str]) -> tuple[bool, Optional[str]]:
    """Convert Tanay's assessment_type to (has_assessment, assessment_type)."""
    if not assessment_str:
        return False, None

    normalized = _normalize_string(assessment_str)

    if normalized in ["none", "no assessment", "souvenir"]:
        return False, "none"

    if normalized in ["auto_graded", "auto-graded", "quiz", "automated"]:
        return True, "auto_graded"

    if normalized in ["expert_skill", "expert-skill", "skill evaluation"]:
        return True, "expert_skill"

    if normalized in ["expert_multi", "expert-multi", "competency evaluation"]:
        return True, "expert_multi"

    # Default: assume assessment exists
    return True, normalized


def _convert_evidence_types(evidence_list: List[str]) -> List[str]:
    """Convert Tanay's evidence_type strings to Prabhath's EvidenceType enum values."""
    if not evidence_list:
        return []

    evidence_map = {
        "attendance": "attendance_record",
        "attendance_record": "attendance_record",
        "completion": "completion_record",
        "completion_record": "completion_record",
        "quiz": "quiz_result",
        "quiz_result": "quiz_result",
        "assignment": "assignment_submission",
        "assignment_submission": "assignment_submission",
        "demonstration": "demonstration",
        "portfolio": "portfolio",
        "project": "project_artifact",
        "project_artifact": "project_artifact",
        "presentation": "presentation",
        "expert_review": "expert_review",
        "peer_feedback": "peer_feedback",
        "external_evaluation": "external_evaluation",
        "supervisor_evaluation": "supervisor_evaluation",
        "concept_map": "concept_map",
        "scenario_response": "scenario_response",
        "capstone": "capstone",
        "rubric": "expert_rated_rubric",
        "expert_rated_rubric": "expert_rated_rubric",
        "ksa_tagged_portfolio": "ksa_tagged_portfolio",
        "case_study": "case_study",
        "leadership_evidence": "leadership_evidence",
        "360_feedback": "360_feedback",
    }

    result = []
    for ev in evidence_list:
        normalized = _normalize_string(ev)
        if normalized in evidence_map:
            result.append(evidence_map[normalized])

    return result


def _convert_bloom_levels(bloom_list: List[str]) -> List[str]:
    """Convert Tanay's bloom_level_indicators to Prabhath's BloomLevel enum values."""
    if not bloom_list:
        return []

    valid_levels = {
        "remember", "understand", "apply", "analyze", "evaluate", "create"
    }

    result = []
    for level in bloom_list:
        normalized = _normalize_string(level)
        if normalized in valid_levels:
            result.append(normalized)

    return result


def tanay_to_prabhath(tanay_badge: Any) -> Dict[str, Any]:
    """
    Convert Tanay's BadgeFactSheet (Pydantic) to dict for Prabhath's BadgeFactSheet.

    Args:
        tanay_badge: Pydantic model from Tanay's API

    Returns:
        Dictionary ready for create_fact_sheet_from_dict()
    """
    # Get attributes from Tanay's model
    title = getattr(tanay_badge, 'title', None) or getattr(tanay_badge, 'badge_name', '')
    description = getattr(tanay_badge, 'description', '') or getattr(tanay_badge, 'description_text', '')
    issuer = getattr(tanay_badge, 'issuer', None) or getattr(tanay_badge, 'issuing_department', None)
    audience = getattr(tanay_badge, 'audience', None)
    context = getattr(tanay_badge, 'context', None)
    assessment_type = getattr(tanay_badge, 'assessment_type', None)
    assessment_present = getattr(tanay_badge, 'assessment_present', False)
    evidence_type = getattr(tanay_badge, 'evidence_type', [])
    evidence_present = getattr(tanay_badge, 'evidence_present', False)
    bloom_indicators = getattr(tanay_badge, 'bloom_level_indicators', [])
    pathway_position = getattr(tanay_badge, 'pathway_position', None)
    source_type = getattr(tanay_badge, 'source_type', 'api')

    # Convert assessment
    has_assessment, prabhath_assessment_type = _convert_assessment_type(assessment_type)
    # If Tanay explicitly says no assessment, honor that
    if not assessment_present and not assessment_type:
        has_assessment = False

    # Build Prabhath-compatible dict
    prabhath_dict = {
        "badge_name": title or "",
        "description": description or "",
        "issuing_department": issuer,
        "audience": _convert_audience(audience),
        "context": _convert_context(context),
        "has_assessment": has_assessment,
        "assessment_type": prabhath_assessment_type,
        "evidence_required": _convert_evidence_types(evidence_type if evidence_present else []),
        "bloom_levels": _convert_bloom_levels(bloom_indicators),
        "pathway_position": pathway_position,
        "source_format": source_type,
        # Defaults
        "prerequisites": [],
        "is_terminal": False,
    }

    # Infer is_terminal from pathway_position
    if pathway_position:
        pos_lower = pathway_position.lower()
        if pos_lower == "terminal" or pos_lower == "capstone":
            prabhath_dict["is_terminal"] = True

    return prabhath_dict


def dict_to_tanay(prabhath_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert Prabhath's badge dict to Tanay's BadgeFactSheet-compatible dict.

    Args:
        prabhath_dict: Dictionary from Prabhath's schema

    Returns:
        Dictionary compatible with Tanay's schema
    """
    # Reverse the conversion for API responses
    audience_list = prabhath_dict.get("audience", [])
    audience_str = audience_list[0] if audience_list else None

    evidence_list = prabhath_dict.get("evidence_required", [])

    tanay_dict = {
        "source_type": prabhath_dict.get("source_format", "unknown"),
        "title": prabhath_dict.get("badge_name"),
        "description": prabhath_dict.get("description"),
        "issuer": prabhath_dict.get("issuing_department"),
        "audience": audience_str,
        "context": prabhath_dict.get("context"),
        "assessment_present": prabhath_dict.get("has_assessment", False),
        "assessment_type": prabhath_dict.get("assessment_type"),
        "evidence_present": len(evidence_list) > 0,
        "evidence_type": evidence_list,
        "bloom_level_indicators": prabhath_dict.get("bloom_levels", []),
        "pathway_position": prabhath_dict.get("pathway_position"),
        "extracted_keywords": [],
    }

    return tanay_dict
