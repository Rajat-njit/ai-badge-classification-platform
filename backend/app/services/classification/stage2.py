"""
Stage 2 — Badge Type classification.

Determined by: Earning Criteria and Assessment.
Rules S2R01–S2R11 from .md Section 8.
CRITICAL: Run in listed order. First match wins.

Returns:
    {
        "type":            str | None,
        "confidence":      "High" | "Medium" | "Low",
        "rules_triggered": list[str],
    }
"""

from app.models.badge_fact_sheet import BadgeFactSheet

# assessment_type values that indicate a structured module/course completion
_MODULE_ASSESSMENT_TYPES = {"module_completion", "final_assessment", "knowledge_checks"}


def classify_stage2(bfs: BadgeFactSheet) -> dict:
    """
    Classify badge type using S2R01–S2R11.

    Mutates nothing on the BFS — pure function.
    """
    criteria_lower = (bfs.earning_criteria_text or "").lower()

    # ------------------------------------------------------------------
    # S2R01 — Micro Credential → Achievement (Terminal in Stage 3)
    # ------------------------------------------------------------------
    if bfs.achievement_type == "Micro Credential":
        return {
            "type": "Achievement",
            "confidence": "High",
            "rules_triggered": ["S2R01"],
        }

    # ------------------------------------------------------------------
    # S2R02 — Competency achievement type → Competency
    # ------------------------------------------------------------------
    if bfs.achievement_type == "Competency":
        return {
            "type": "Competency",
            "confidence": "High",
            "rules_triggered": ["S2R02"],
        }

    # ------------------------------------------------------------------
    # S2R03 — Certificate of Completion → Achievement (entry level)
    # ------------------------------------------------------------------
    if bfs.achievement_type == "Certificate Of Completion":
        return {
            "type": "Achievement",
            "confidence": "High",
            "rules_triggered": ["S2R03"],
        }

    # ------------------------------------------------------------------
    # S2R04 — Compliance badge → Achievement
    # ------------------------------------------------------------------
    if (
        bfs.badge_purpose == "compliance"
        or "mandatory to apply" in criteria_lower
        or "required to apply" in criteria_lower
    ):
        return {
            "type": "Achievement",
            "confidence": "High",
            "rules_triggered": ["S2R04"],
        }

    # ------------------------------------------------------------------
    # S2R05 — No assessment → Souvenir
    # ------------------------------------------------------------------
    if (
        bfs.assessment_required == "no"
        or bfs.assessment_type == "attendance"
        or (bfs.criteria_id_url and "badgr.com/claim" in bfs.criteria_id_url)
    ):
        return {
            "type": "Souvenir",
            "confidence": "High",
            "rules_triggered": ["S2R05"],
        }

    # ------------------------------------------------------------------
    # S2R06 — Expert evaluation present → Skill
    # Simplified per Phase 5 spec: expert_evaluation_required OR expert_scored
    # ------------------------------------------------------------------
    if bfs.expert_evaluation_required or bfs.assessment_evaluator == "expert_scored":
        return {
            "type": "Skill",
            "confidence": "High",
            "rules_triggered": ["S2R06"],
        }

    # ------------------------------------------------------------------
    # S2R08 — KSA dimensions present OR real-world OR criteria logic suggests
    # ------------------------------------------------------------------
    if bfs.ksa_dimensions:
        return {
            "type": "Competency",
            "confidence": "Medium",
            "rules_triggered": ["S2R08"],
        }
    if (
        bfs.real_world_context
        and bfs.criteria_logic in ("OR", "mixed")
        and bfs.achievement_type is None
    ):
        return {
            "type": "Competency",
            "confidence": "Medium",
            "rules_triggered": ["S2R08"],
        }

    # ------------------------------------------------------------------
    # S2R09 — Canvas course code OR module-style assessment → Achievement
    # Moved before S2R07: canvas code / structured assessment type gives
    # enough signal to commit to Achievement at High confidence.
    # ------------------------------------------------------------------
    if bfs.canvas_course_code or bfs.assessment_type in _MODULE_ASSESSMENT_TYPES:
        return {
            "type": "Achievement",
            "confidence": "High",
            "rules_triggered": ["S2R09"],
        }

    # ------------------------------------------------------------------
    # S2R10 — OSIL + pre/post assessment → Achievement
    # Moved before S2R07 for same reason: specific enough to be High.
    # ------------------------------------------------------------------
    if bfs.issuer == "OSIL" and bfs.assessment_type == "pre_post_assessment":
        return {
            "type": "Achievement",
            "confidence": "High",
            "rules_triggered": ["S2R10"],
        }

    # ------------------------------------------------------------------
    # S2R07 — Assessment required but evaluator unknown → Achievement/Medium
    # "Skill possible — confirm assessment_evaluator"
    # Only reaches here when no canvas code / structured type matched above.
    # ------------------------------------------------------------------
    if bfs.assessment_required == "yes" and bfs.assessment_evaluator is None:
        return {
            "type": "Achievement",
            "confidence": "Medium",
            "rules_triggered": ["S2R07"],
            "flag": "Skill possible — confirm assessment_evaluator",
        }

    # ------------------------------------------------------------------
    # S2R11 — No rule matched
    # ------------------------------------------------------------------
    return {
        "type": None,
        "confidence": "Low",
        "rules_triggered": ["S2R11"],
    }
