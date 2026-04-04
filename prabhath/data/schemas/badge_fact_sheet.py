"""
Badge Fact Sheet Schema
Based on NJIT Digital Badge Taxonomy
Author: Prabhath Vipparthi

This module defines the normalized internal data structure for badge metadata.
All input sources (proposal forms, free text, OBv3 JSON) are converted to this format
before classification.

"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class Audience(str, Enum):
    """Target audience for the badge (from taxonomy Step 1)"""

    STUDENT = "student"
    FACULTY = "faculty"
    STAFF = "staff"
    EXTERNAL = "external"  # adult learners, working professionals
    PROFESSIONAL = "professional"  # working professionals in continuing education
    ALUMNI = "alumni"


class Context(str, Enum):
    """Institutional context where learning occurs (Step 1)"""

    ACADEMIC = "academic"  # credit-bearing courses
    CO_CURRICULAR = "co_curricular"  # student activities outside courses
    PROFESSIONAL_ED = "professional_ed"  # continuing education for external
    EMPLOYEE_DEV = "employee_development"  # faculty/staff training


class AssessmentType(str, Enum):
    """Type of assessment used (Step 2)"""

    NONE = "none"  # no assessment (souvenir)
    AUTO = "auto_graded"  # quiz, knowledge check (achievement)
    EXPERT_SKILL = "expert_skill"  # single skill evaluated by expert (skill)
    EXPERT_MULTI = "expert_multi"  # multiple dimensions evaluated (competency)


class EvidenceType(str, Enum):
    """Type of evidence required (Step 3)"""

    ATTENDANCE = "attendance_record"
    COMPLETION = "completion_record"
    QUIZ = "quiz_result"
    ASSIGNMENT = "assignment_submission"
    DEMONSTRATION = "demonstration"
    PORTFOLIO = "portfolio"
    PROJECT = "project_artifact"
    PRESENTATION = "presentation"
    EXPERT_REVIEW = "expert_review"
    PEER_FEEDBACK = "peer_feedback"
    EXTERNAL_EVAL = "external_evaluation"
    SUPERVISOR_EVAL = "supervisor_evaluation"
    CONCEPT_MAP = "concept_map"
    SCENARIO_RESPONSE = "scenario_response"
    CAPSTONE = "capstone"
    RUBRIC = "expert_rated_rubric"
    KSA_TAGGED_PORTFOLIO = "ksa_tagged_portfolio"
    CASE_STUDY = "case_study"
    LEADERSHIP_EVIDENCE = "leadership_evidence"
    _360_FEEDBACK = "360_feedback"


class BloomLevel(str, Enum):
    """Cognitive depth levels (for Skill badges)"""

    REMEMBER = "remember"
    UNDERSTAND = "understand"
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"


@dataclass
class BadgeFactSheet:
    """
    Normalized internal representation of badge metadata.
    All classification rules operate on instances of this class.
    """

    # Basic Information
    badge_name: str
    description: str
    issuing_department: Optional[str] = None

    # Step 1: Category (Audience + Context)
    audience: List[Audience] = field(default_factory=list)
    context: Optional[Context] = None

    # Step 2: Type (Criteria + Assessment)
    has_assessment: bool = False
    assessment_type: Optional[AssessmentType] = None
    assessment_description: Optional[str] = None
    completion_criteria: Optional[str] = None

    # Step 3: Level (Evidence + Cognitive Depth)
    evidence_required: List[EvidenceType] = field(default_factory=list)
    evidence_description: Optional[str] = None
    bloom_levels: List[BloomLevel] = field(default_factory=list)

    # Pathway information (for Achievement levels)
    prerequisites: List[str] = field(
        default_factory=list
    )  # required previous badge names/IDs
    is_terminal: bool = False  # final badge in pathway

    # Optional metadata
    hours_to_complete: Optional[float] = None
    source_format: str = "unknown"  # "proposal_form", "text", "obv3"
    confidence_scores: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "badge_name": self.badge_name,
            "description": self.description,
            "issuing_department": self.issuing_department,
            "audience": [a.value for a in self.audience],
            "context": self.context.value if self.context else None,
            "has_assessment": self.has_assessment,
            "assessment_type": (
                self.assessment_type.value if self.assessment_type else None
            ),
            "assessment_description": self.assessment_description,
            "completion_criteria": self.completion_criteria,
            "evidence_required": [e.value for e in self.evidence_required],
            "evidence_description": self.evidence_description,
            "bloom_levels": [b.value for b in self.bloom_levels],
            "prerequisites": self.prerequisites,
            "is_terminal": self.is_terminal,
            "hours_to_complete": self.hours_to_complete,
            "source_format": self.source_format,
            "confidence_scores": self.confidence_scores,
        }

    @classmethod
    def from_proposal_form(cls, form_data: Dict[str, Any]) -> "BadgeFactSheet":
        """
        Create a BadgeFactSheet from NJIT proposal form data.
        Maps form fields to schema fields.
        """
        # Basic fields
        fact = cls(
            badge_name=form_data.get("badge_name", ""),
            description=form_data.get("description", ""),
            issuing_department=form_data.get("issuing_dept"),
        )
# Map category (Q9) to audience and context
        category = form_data.get("badge_category", "")
        if "Academic" in category:
            fact.audience = [Audience.STUDENT]
            fact.context = Context.ACADEMIC
        elif "Co-Curricular" in category or "Extra-Curricular" in category:
            fact.audience = [Audience.STUDENT]
            fact.context = Context.CO_CURRICULAR
        elif "Continuing and Professional Education" in category:
            fact.audience = [Audience.EXTERNAL, Audience.PROFESSIONAL]
            fact.context = Context.PROFESSIONAL_ED
        elif "Faculty and Staff Development" in category:
            fact.audience = [Audience.FACULTY, Audience.STAFF]
            fact.context = Context.EMPLOYEE_DEV

        # Map level (Q18) – will be used later, but we store relevant fields
        # For now, we can extract assessment info from criteria (Q8)
        fact.completion_criteria = form_data.get("earning_criteria")

        # TODO: Add more mappings as needed

        return fact

    def validate(self) -> List[str]:
        """Basic validation: returns list of error messages."""
        errors = []
        if not self.badge_name:
            errors.append("Badge name is required.")
        if not self.audience:
            errors.append("At least one audience must be specified.")
        if not self.context:
            errors.append("Context must be specified.")
        if self.has_assessment and not self.assessment_type:
            errors.append(
                "Assessment type must be specified when has_assessment is True."
            )
        return errors


def create_fact_sheet_from_dict(data: Dict[str, Any]) -> BadgeFactSheet:
    """
    Create a BadgeFactSheet from a dictionary (JSON format).
    Used for loading badges from synthetic_badges.json or master_badges.json.
    """
    # Parse audience enum values
    audience_list = []
    for aud in data.get("audience", []):
        try:
            if isinstance(aud, str):
                audience_list.append(Audience(aud.lower()))
        except ValueError:
            pass  # Skip invalid audience values

    # Parse context enum
    context_val = data.get("context")
    context = None
    if context_val:
        try:
            context = Context(context_val.lower())
        except ValueError:
            pass

    # Parse assessment type
    assessment_type = None
    at = data.get("assessment_type")
    if at:
        at_map = {
            "none": AssessmentType.NONE,
            "auto_graded": AssessmentType.AUTO,
            "expert_skill": AssessmentType.EXPERT_SKILL,
            "expert_multi": AssessmentType.EXPERT_MULTI,
        }
        assessment_type = at_map.get(at.lower(), AssessmentType.AUTO)

    # Parse evidence types
    evidence_list = []
    ev_map = {
        "attendance_record": EvidenceType.ATTENDANCE,
        "completion_record": EvidenceType.COMPLETION,
        "quiz_result": EvidenceType.QUIZ,
        "assignment_submission": EvidenceType.ASSIGNMENT,
        "demonstration": EvidenceType.DEMONSTRATION,
        "portfolio": EvidenceType.PORTFOLIO,
        "project_artifact": EvidenceType.PROJECT,
        "presentation": EvidenceType.PRESENTATION,
        "expert_review": EvidenceType.EXPERT_REVIEW,
        "peer_feedback": EvidenceType.PEER_FEEDBACK,
        "external_evaluation": EvidenceType.EXTERNAL_EVAL,
        "supervisor_evaluation": EvidenceType.SUPERVISOR_EVAL,
        "concept_map": EvidenceType.CONCEPT_MAP,
        "scenario_response": EvidenceType.SCENARIO_RESPONSE,
        "capstone": EvidenceType.CAPSTONE,
        "expert_rated_rubric": EvidenceType.RUBRIC,
        "ksa_tagged_portfolio": EvidenceType.KSA_TAGGED_PORTFOLIO,
        "case_study": EvidenceType.CASE_STUDY,
        "leadership_evidence": EvidenceType.LEADERSHIP_EVIDENCE,
        "360_feedback": EvidenceType._360_FEEDBACK,
    }
    for ev in data.get("evidence_required", []):
        if isinstance(ev, str) and ev.lower() in ev_map:
            evidence_list.append(ev_map[ev.lower()])

    # Parse bloom levels
    bloom_list = []
    for bl in data.get("bloom_levels", []):
        try:
            if isinstance(bl, str):
                bloom_list.append(BloomLevel(bl.lower()))
        except ValueError:
            pass

    return BadgeFactSheet(
        badge_name=data.get("badge_name", ""),
        description=data.get("description", ""),
        issuing_department=data.get("issuing_department"),
        audience=audience_list,
        context=context,
        has_assessment=data.get("has_assessment", False),
        assessment_type=assessment_type,
        assessment_description=data.get("assessment_description"),
        completion_criteria=data.get("completion_criteria"),
        evidence_required=evidence_list,
        bloom_levels=bloom_list,
        prerequisites=data.get("prerequisites", []),
        is_terminal=data.get("is_terminal", False),
        hours_to_complete=data.get("hours_to_complete"),
        source_format=data.get("source_format", "unknown"),
    )
