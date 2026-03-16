"""
Basic tests for classification pipeline.
Run with: pytest tests/test_classification.py
"""

import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data.schemas.badge_fact_sheet import BadgeFactSheet
from src.classification import step1_category, step2_type, step3_level


def load_synthetic_badges():
    """Load the 20 synthetic badges from JSON."""
    with open("data/synthetic/synthetic_badges.json", "r") as f:
        data = json.load(f)
    return data


def create_fact_sheet_from_dict(d):
    """Convert dict to BadgeFactSheet (simplified)."""
    # This is a minimal conversion; in real code you'd map enums properly
    from data.schemas.badge_fact_sheet import (
        Audience,
        Context,
        AssessmentType,
        EvidenceType,
        BloomLevel,
    )

    fact = BadgeFactSheet(
        badge_name=d["badge_name"],
        description=d["description"],
        issuing_department=d.get("issuing_department"),
        has_assessment=d.get("has_assessment", False),
    )

    # Map audience strings to enums
    audience_map = {
        "student": Audience.STUDENT,
        "faculty": Audience.FACULTY,
        "staff": Audience.STAFF,
        "external": Audience.EXTERNAL,
        "professional": Audience.PROFESSIONAL,
        "alumni": Audience.ALUMNI,
    }
    fact.audience = [
        audience_map[a] for a in d.get("audience", []) if a in audience_map
    ]

    context_map = {
        "academic": Context.ACADEMIC,
        "co_curricular": Context.CO_CURRICULAR,
        "professional_ed": Context.PROFESSIONAL_ED,
        "employee_development": Context.EMPLOYEE_DEV,
    }
    fact.context = context_map.get(d.get("context"))

    assessment_map = {
        "none": AssessmentType.NONE,
        "auto_graded": AssessmentType.AUTO,
        "expert_skill": AssessmentType.EXPERT_SKILL,
        "expert_multi": AssessmentType.EXPERT_MULTI,
    }
    fact.assessment_type = assessment_map.get(d.get("assessment_type"))

    # Evidence mapping (simplified)
    evidence_map = {
        "attendance_record": EvidenceType.ATTENDANCE,
        "quiz_result": EvidenceType.QUIZ,
        "assignment_submission": EvidenceType.ASSIGNMENT,
        "demonstration": EvidenceType.DEMONSTRATION,
        "portfolio": EvidenceType.PORTFOLIO,
        "project_artifact": EvidenceType.PROJECT,
        "presentation": EvidenceType.PRESENTATION,
        "expert_review": EvidenceType.EXPERT_REVIEW,
        "expert_rated_rubric": EvidenceType.RUBRIC,
        "supervisor_evaluation": EvidenceType.SUPERVISOR_EVAL,
        "_360_feedback": EvidenceType._360_FEEDBACK,
        "leadership_evidence": EvidenceType.LEADERSHIP_EVIDENCE,
        "ksa_tagged_portfolio": EvidenceType.KSA_TAGGED_PORTFOLIO,
        "case_study": EvidenceType.CASE_STUDY,
    }
    fact.evidence_required = [
        evidence_map[e] for e in d.get("evidence_required", []) if e in evidence_map
    ]

    bloom_map = {
        "remember": BloomLevel.REMEMBER,
        "understand": BloomLevel.UNDERSTAND,
        "apply": BloomLevel.APPLY,
        "analyze": BloomLevel.ANALYZE,
        "evaluate": BloomLevel.EVALUATE,
        "create": BloomLevel.CREATE,
    }
    fact.bloom_levels = [
        bloom_map[b] for b in d.get("bloom_levels", []) if b in bloom_map
    ]

    fact.prerequisites = d.get("prerequisites", [])
    fact.is_terminal = d.get("is_terminal", False)

    return fact


def test_classification_pipeline():
    """Test that all 20 badges can be classified without errors."""
    badges_data = load_synthetic_badges()

    for i, bd in enumerate(badges_data):
        badge = create_fact_sheet_from_dict(bd)

        # Step 1
        category = step1_category.classify_category(badge)
        assert category in [
            "Academic",
            "Co-Curricular and Extra-Curricular",
            "Continuing & Professional Education",
            "Faculty & Staff Development",
            "Uncategorized",
        ]

        # Step 2
        badge_type = step2_type.classify_type(badge)
        assert badge_type in ["Souvenir", "Achievement", "Skill", "Competency"]

        # Step 3
        level = step3_level.classify_level(badge, badge_type)
        if badge_type == "Souvenir":
            assert level == "Souvenir"
        elif badge_type == "Achievement":
            assert level in ["Foundational", "Milestone", "Terminal"]
        elif badge_type == "Skill":
            assert level in ["Awareness", "Application", "Mastery"]
        elif badge_type == "Competency":
            assert level in ["Demonstrated", "Integrated", "Exemplary"]

        print(
            f"✓ {i+1:2d} {badge.badge_name[:30]:30} -> {category:15} {badge_type:12} {level:12}"
        )


def test_explanation_functions():
    """Test that explanation functions work and return strings."""
    from data.schemas.badge_fact_sheet import Audience, Context, AssessmentType

    # Create a sample badge
    badge = BadgeFactSheet(
        badge_name="Test Badge",
        description="A test badge",
        audience=[Audience.STUDENT],
        context=Context.ACADEMIC,
        has_assessment=True,
        assessment_type=AssessmentType.AUTO,
    )

    # Test category explanation
    category = step1_category.classify_category(badge)
    cat_exp = step1_category.get_category_explanation(badge, category)
    assert isinstance(cat_exp, str)
    assert "Academic" in cat_exp

    # Test type explanation
    badge_type = step2_type.classify_type(badge)
    type_exp = step2_type.get_type_explanation(badge, badge_type)
    assert isinstance(type_exp, str)
    assert "Achievement" in type_exp

    # Test level explanation
    level = step3_level.classify_level(badge, badge_type)
    level_exp = step3_level.get_level_explanation(badge, badge_type, level)
    assert isinstance(level_exp, str)
    assert level in level_exp


def test_edge_cases_uncategorized():
    """Test Uncategorized fallback when no rules match."""
    from data.schemas.badge_fact_sheet import Audience, Context

    badge = BadgeFactSheet(
        badge_name="Unknown Badge",
        description="A badge that doesn't match any category",
        audience=[Audience.ALUMNI],  # Not covered by any rule
        context=None,  # Missing context
    )

    category = step1_category.classify_category(badge)
    assert category == "Uncategorized"

    # Test explanation for Uncategorized
    exp = step1_category.get_category_explanation(badge, category)
    assert "Uncategorized" in exp


def test_type_fallback_with_description():
    """Test type classification fallback using description keywords."""
    badge = BadgeFactSheet(
        badge_name="Skill Badge",
        description="A badge",
        has_assessment=True,
        assessment_type=None,  # No assessment type set
        assessment_description="Demonstrates skill in programming",  # Set assessment_description, not description
    )

    badge_type = step2_type.classify_type(badge)
    assert badge_type == "Skill"


def test_competency_fallback_via_description():
    """Test competency detection via description keywords."""
    badge = BadgeFactSheet(
        badge_name="Competency Badge",
        description="A badge",
        has_assessment=True,
        assessment_type=None,
        assessment_description="Evaluates KSA knowledge skills and abilities",
    )

    badge_type = step2_type.classify_type(badge)
    assert badge_type == "Competency"


def test_achievement_fallback_via_description():
    """Test achievement detection via description keywords."""
    badge = BadgeFactSheet(
        badge_name="Achievement Badge",
        description="A badge",
        has_assessment=True,
        assessment_type=None,
        assessment_description="Complete quiz and assignment",
    )

    badge_type = step2_type.classify_type(badge)
    assert badge_type == "Achievement"


def test_souvenir_explanation():
    """Test explanation for Souvenir type."""
    badge = BadgeFactSheet(
        badge_name="Souvenir Badge",
        description="Participation badge",
        has_assessment=False,
    )

    badge_type = step2_type.classify_type(badge)
    exp = step2_type.get_type_explanation(badge, badge_type)
    assert "Souvenir" in exp
    assert "no assessment" in exp.lower()


def test_skill_levels_via_bloom():
    """Test skill level classification using Bloom levels."""
    from data.schemas.badge_fact_sheet import BloomLevel, EvidenceType

    # Awareness level
    badge1 = BadgeFactSheet(
        badge_name="Awareness Badge",
        description="Basic knowledge",
        has_assessment=True,
        assessment_type=None,
        bloom_levels=[BloomLevel.REMEMBER],
    )
    level1 = step3_level.classify_level(badge1, "Skill")
    assert level1 == "Awareness"

    # Application level
    badge2 = BadgeFactSheet(
        badge_name="Application Badge",
        description="Apply knowledge",
        has_assessment=True,
        assessment_type=None,
        bloom_levels=[BloomLevel.APPLY],
    )
    level2 = step3_level.classify_level(badge2, "Skill")
    assert level2 == "Application"

    # Mastery level
    badge3 = BadgeFactSheet(
        badge_name="Mastery Badge",
        description="Master level",
        has_assessment=True,
        assessment_type=None,
        bloom_levels=[BloomLevel.CREATE],
    )
    level3 = step3_level.classify_level(badge3, "Skill")
    assert level3 == "Mastery"


def test_skill_fallback_via_evidence():
    """Test skill level fallback when no Bloom levels provided."""
    from data.schemas.badge_fact_sheet import EvidenceType

    # Awareness via attendance
    badge1 = BadgeFactSheet(
        badge_name="Awareness Badge",
        description="Basic",
        has_assessment=True,
        assessment_type=None,
        bloom_levels=[],
        evidence_required=[EvidenceType.ATTENDANCE],
    )
    level1 = step3_level.classify_level(badge1, "Skill")
    assert level1 == "Awareness"

    # Application via assignment
    badge2 = BadgeFactSheet(
        badge_name="Application Badge",
        description="Apply",
        has_assessment=True,
        assessment_type=None,
        bloom_levels=[],
        evidence_required=[EvidenceType.ASSIGNMENT],
    )
    level2 = step3_level.classify_level(badge2, "Skill")
    assert level2 == "Application"

    # Mastery via project
    badge3 = BadgeFactSheet(
        badge_name="Mastery Badge",
        description="Master",
        has_assessment=True,
        assessment_type=None,
        bloom_levels=[],
        evidence_required=[EvidenceType.PROJECT],
    )
    level3 = step3_level.classify_level(badge3, "Skill")
    assert level3 == "Mastery"


def test_competency_levels():
    """Test all competency level branches."""
    from data.schemas.badge_fact_sheet import EvidenceType

    # Exemplary via leadership evidence
    badge1 = BadgeFactSheet(
        badge_name="Leadership Badge",
        description="Leadership",
        has_assessment=True,
        assessment_type=None,
        evidence_required=[EvidenceType.LEADERSHIP_EVIDENCE],
    )
    level1 = step3_level.classify_level(badge1, "Competency")
    assert level1 == "Exemplary"

    # Exemplary via 360 feedback
    badge2 = BadgeFactSheet(
        badge_name="360 Badge",
        description="360 feedback",
        has_assessment=True,
        assessment_type=None,
        evidence_required=[EvidenceType._360_FEEDBACK],
    )
    level2 = step3_level.classify_level(badge2, "Competency")
    assert level2 == "Exemplary"

    # Integrated via KSA portfolio
    badge3 = BadgeFactSheet(
        badge_name="KSA Badge",
        description="KSA portfolio",
        has_assessment=True,
        assessment_type=None,
        evidence_required=[EvidenceType.KSA_TAGGED_PORTFOLIO],
    )
    level3 = step3_level.classify_level(badge3, "Competency")
    assert level3 == "Integrated"

    # Integrated via case study
    badge4 = BadgeFactSheet(
        badge_name="Case Study Badge",
        description="Case study",
        has_assessment=True,
        assessment_type=None,
        evidence_required=[EvidenceType.CASE_STUDY],
    )
    level4 = step3_level.classify_level(badge4, "Competency")
    assert level4 == "Integrated"

    # Demonstrated (default)
    badge5 = BadgeFactSheet(
        badge_name="Standard Badge",
        description="Standard",
        has_assessment=True,
        assessment_type=None,
        evidence_required=[EvidenceType.ATTENDANCE],
    )
    level5 = step3_level.classify_level(badge5, "Competency")
    assert level5 == "Demonstrated"


def test_achievement_levels():
    """Test achievement level branches."""
    # Terminal
    badge1 = BadgeFactSheet(
        badge_name="Terminal Badge",
        description="Final badge",
        has_assessment=True,
        assessment_type=None,
        is_terminal=True,
        prerequisites=["Previous Badge"],
    )
    level1 = step3_level.classify_level(badge1, "Achievement")
    assert level1 == "Terminal"

    # Milestone
    badge2 = BadgeFactSheet(
        badge_name="Milestone Badge",
        description="Mid badge",
        has_assessment=True,
        assessment_type=None,
        is_terminal=False,
        prerequisites=["Previous Badge"],
    )
    level2 = step3_level.classify_level(badge2, "Achievement")
    assert level2 == "Milestone"

    # Foundational
    badge3 = BadgeFactSheet(
        badge_name="Foundational Badge",
        description="First badge",
        has_assessment=True,
        assessment_type=None,
        is_terminal=False,
        prerequisites=[],
    )
    level3 = step3_level.classify_level(badge3, "Achievement")
    assert level3 == "Foundational"


def test_level_explanations():
    """Test all level explanation branches."""
    # Achievement explanations
    badge1 = BadgeFactSheet(
        badge_name="Test", description="Test", prerequisites=["Prev"], is_terminal=True
    )

    exp_terminal = step3_level.get_level_explanation(badge1, "Achievement", "Terminal")
    assert "Terminal" in exp_terminal

    badge2 = BadgeFactSheet(
        badge_name="Test", description="Test", prerequisites=["Prev"], is_terminal=False
    )
    exp_milestone = step3_level.get_level_explanation(
        badge2, "Achievement", "Milestone"
    )
    assert "Milestone" in exp_milestone
    assert "Prev" in exp_milestone

    badge3 = BadgeFactSheet(
        badge_name="Test", description="Test", prerequisites=[], is_terminal=False
    )
    exp_foundational = step3_level.get_level_explanation(
        badge3, "Achievement", "Foundational"
    )
    assert "Foundational" in exp_foundational

    # Skill explanations
    exp_awareness = step3_level.get_level_explanation(badge3, "Skill", "Awareness")
    assert "Awareness" in exp_awareness

    exp_application = step3_level.get_level_explanation(badge3, "Skill", "Application")
    assert "Application" in exp_application

    exp_mastery = step3_level.get_level_explanation(badge3, "Skill", "Mastery")
    assert "Mastery" in exp_mastery

    # Competency explanations
    exp_demon = step3_level.get_level_explanation(badge3, "Competency", "Demonstrated")
    assert "Demonstrated" in exp_demon

    exp_int = step3_level.get_level_explanation(badge3, "Competency", "Integrated")
    assert "Integrated" in exp_int

    exp_exemp = step3_level.get_level_explanation(badge3, "Competency", "Exemplary")
    assert "Exemplary" in exp_exemp


def test_unknown_level():
    """Test unknown level fallback for invalid badge type."""
    badge = BadgeFactSheet(badge_name="Test", description="Test")
    level = step3_level.classify_level(badge, "InvalidType")
    assert level == "Unknown"


def test_badge_fact_sheet_to_dict():
    """Test to_dict method serialization."""
    from data.schemas.badge_fact_sheet import (
        Audience,
        Context,
        AssessmentType,
        EvidenceType,
        BloomLevel,
    )

    badge = BadgeFactSheet(
        badge_name="Test Badge",
        description="Test description",
        issuing_department="CS",
        audience=[Audience.STUDENT],
        context=Context.ACADEMIC,
        has_assessment=True,
        assessment_type=AssessmentType.AUTO,
        assessment_description="Quiz",
        completion_criteria="Pass quiz",
        evidence_required=[EvidenceType.QUIZ],
        evidence_description="Quiz result",
        bloom_levels=[BloomLevel.APPLY],
        prerequisites=["Intro"],
        is_terminal=False,
        hours_to_complete=10.0,
        source_format="proposal_form",
    )

    d = badge.to_dict()

    assert d["badge_name"] == "Test Badge"
    assert d["description"] == "Test description"
    assert d["issuing_department"] == "CS"
    assert d["audience"] == ["student"]
    assert d["context"] == "academic"
    assert d["has_assessment"] is True
    assert d["assessment_type"] == "auto_graded"
    assert d["evidence_required"] == ["quiz_result"]
    assert d["bloom_levels"] == ["apply"]
    assert d["prerequisites"] == ["Intro"]
    assert d["is_terminal"] is False
    assert d["hours_to_complete"] == 10.0


def test_badge_fact_sheet_from_proposal_form():
    """Test from_proposal_form class method."""
    from data.schemas.badge_fact_sheet import Audience, Context

    form_data = {
        "badge_name": "Test Badge",
        "description": "Test description",
        "issuing_dept": "Computer Science",
        "badge_category": "Academic (Credit-bearing courses)",
        "earning_criteria": "Complete all assignments",
    }

    badge = BadgeFactSheet.from_proposal_form(form_data)

    assert badge.badge_name == "Test Badge"
    assert badge.description == "Test description"
    assert badge.issuing_department == "Computer Science"
    assert badge.audience == [Audience.STUDENT]
    assert badge.context == Context.ACADEMIC
    assert badge.completion_criteria == "Complete all assignments"


def test_badge_fact_sheet_from_proposal_form_all_categories():
    """Test from_proposal_form for all four categories."""
    from data.schemas.badge_fact_sheet import Audience, Context

    # Academic
    form1 = {
        "badge_name": "Academic",
        "description": "Desc",
        "badge_category": "Academic",
    }
    badge1 = BadgeFactSheet.from_proposal_form(form1)
    assert badge1.context == Context.ACADEMIC

    # Co-Curricular
    form2 = {
        "badge_name": "Co",
        "description": "Desc",
        "badge_category": "Co-Curricular",
    }
    badge2 = BadgeFactSheet.from_proposal_form(form2)
    assert badge2.context == Context.CO_CURRICULAR

    # Extra-Curricular
    form3 = {
        "badge_name": "Extra",
        "description": "Desc",
        "badge_category": "Extra-Curricular",
    }
    badge3 = BadgeFactSheet.from_proposal_form(form3)
    assert badge3.context == Context.CO_CURRICULAR

    # Continuing Education
    form4 = {
        "badge_name": "CE",
        "description": "Desc",
        "badge_category": "Continuing and Professional Education",
    }
    badge4 = BadgeFactSheet.from_proposal_form(form4)
    assert badge4.context == Context.PROFESSIONAL_ED
    assert Audience.EXTERNAL in badge4.audience
    assert Audience.PROFESSIONAL in badge4.audience

    # Faculty/Staff
    form5 = {
        "badge_name": "Fac",
        "description": "Desc",
        "badge_category": "Faculty and Staff Development",
    }
    badge5 = BadgeFactSheet.from_proposal_form(form5)
    assert badge5.context == Context.EMPLOYEE_DEV
    assert Audience.FACULTY in badge5.audience
    assert Audience.STAFF in badge5.audience


def test_badge_fact_sheet_validate():
    """Test validate method."""
    from data.schemas.badge_fact_sheet import Audience, Context

    # Valid badge
    badge1 = BadgeFactSheet(
        badge_name="Valid",
        description="Valid desc",
        audience=[Audience.STUDENT],
        context=Context.ACADEMIC,
    )
    errors1 = badge1.validate()
    assert len(errors1) == 0

    # Missing name
    badge2 = BadgeFactSheet(
        badge_name="",
        description="Desc",
        audience=[Audience.STUDENT],
        context=Context.ACADEMIC,
    )
    errors2 = badge2.validate()
    assert "Badge name is required." in errors2

    # Missing audience
    badge3 = BadgeFactSheet(
        badge_name="Test", description="Desc", audience=[], context=Context.ACADEMIC
    )
    errors3 = badge3.validate()
    assert "At least one audience must be specified." in errors3

    # Missing context
    badge4 = BadgeFactSheet(
        badge_name="Test", description="Desc", audience=[Audience.STUDENT], context=None
    )
    errors4 = badge4.validate()
    assert "Context must be specified." in errors4

    # Missing assessment type when has_assessment is True
    badge5 = BadgeFactSheet(
        badge_name="Test",
        description="Desc",
        audience=[Audience.STUDENT],
        context=Context.ACADEMIC,
        has_assessment=True,
        assessment_type=None,
    )
    errors5 = badge5.validate()
    assert "Assessment type must be specified when has_assessment is True." in errors5


def test_presentation_evidence_mapping():
    """Test that presentation evidence type is properly mapped."""
    from data.schemas.badge_fact_sheet import EvidenceType

    # Verify PRESENTATION exists in enum
    assert hasattr(EvidenceType, "PRESENTATION")
    assert EvidenceType.PRESENTATION.value == "presentation"

    # Test mapping in create_fact_sheet_from_dict
    d = {
        "badge_name": "Test",
        "description": "Test",
        "evidence_required": ["presentation"],
    }

    badge = create_fact_sheet_from_dict(d)
    assert EvidenceType.PRESENTATION in badge.evidence_required


if __name__ == "__main__":
    test_classification_pipeline()
