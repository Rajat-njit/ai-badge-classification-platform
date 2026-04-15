"""
NJIT AI-Assisted Digital Badge Classification Tool
Author: Rajat Ravindra Pednekar (rp2348@njit.edu)
Institution: New Jersey Institute of Technology
Capstone Project — Spring 2026

Form mapper — maps proposal form fields directly into a BadgeFactSheet.

The form is the second input mode (Tab 1 in the frontend).
Unlike JSON parsing, the form fields map 1:1 to BFS fields
so no format detection or alignment parsing is needed.

All fields are optional at ingestion time — missing_signals
will be populated later by the normalizer's gap detector.
"""

import json
from typing import Any, Dict

from app.models.badge_fact_sheet import BadgeFactSheet


def map_form_to_bfs(form_data: Dict[str, Any]) -> BadgeFactSheet:
    """
    Map a proposal form payload dict into a BadgeFactSheet.

    The caller is responsible for passing validated field names.
    Unknown keys are ignored (BFS has extra="forbid" so we only
    pass known fields explicitly).

    Args:
        form_data: Dict of form field names and values from the API.

    Returns:
        A partially-filled BadgeFactSheet ready for issuer resolution
        and NLP extraction.
    """
    bfs = BadgeFactSheet()
    bfs.structured_source_type = "form"
    bfs.obv_version = None
    bfs.raw_input_text = json.dumps(form_data)
    bfs.obv_fields_present = []

    # ------------------------------------------------------------------
    # Section 2 — Core Identity
    # ------------------------------------------------------------------
    bfs.badge_title = _str(form_data, "badge_title")
    bfs.badge_description = _str(form_data, "badge_description")
    bfs.issuer = _str(form_data, "issuer") or None
    bfs.achievement_type = _str(form_data, "achievement_type") or None
    bfs.external_partner = _str(form_data, "external_partner") or None

    # ------------------------------------------------------------------
    # Section 3 — Audience and Context
    # ------------------------------------------------------------------
    bfs.intended_audience = _str(form_data, "intended_audience") or None
    bfs.audience_type = _str(form_data, "audience_type") or None
    bfs.institutional_context = _str(form_data, "institutional_context") or None
    bfs.audience_restriction = _str(form_data, "audience_restriction") or None
    bfs.is_credit_bearing = bool(form_data.get("is_credit_bearing", False))
    bfs.pdh_credits = _str(form_data, "pdh_credits") or None
    bfs.credit_type = _str(form_data, "credit_type") or None

    # ------------------------------------------------------------------
    # Section 4 — Earning Criteria
    # ------------------------------------------------------------------
    bfs.earning_criteria_text = _str(form_data, "earning_criteria_text")
    bfs.assessment_required = _str(form_data, "assessment_required") or "unknown"
    bfs.assessment_type = _str(form_data, "assessment_type") or None
    bfs.assessment_type_detail = _str(form_data, "assessment_type_detail") or None
    bfs.assessment_evaluator = _str(form_data, "assessment_evaluator") or None
    bfs.assessment_pass_threshold = _str(form_data, "assessment_pass_threshold") or None
    bfs.assessment_modality = _str(form_data, "assessment_modality") or None
    bfs.badge_purpose = _str(form_data, "badge_purpose") or "recognition"
    bfs.downstream_workflow = _str(form_data, "downstream_workflow") or None
    bfs.mandatory_for = _str(form_data, "mandatory_for") or None

    prereqs = form_data.get("prerequisite_badges", [])
    bfs.prerequisite_badges = prereqs if isinstance(prereqs, list) else []
    bfs.has_prerequisite_badges = len(bfs.prerequisite_badges) > 0

    # ------------------------------------------------------------------
    # Section 5 — Evidence
    # ------------------------------------------------------------------
    bfs.evidence_required = _str(form_data, "evidence_required") or "unknown"
    bfs.evidence_type = _str(form_data, "evidence_type") or None
    bfs.evidence_description = _str(form_data, "evidence_description") or None
    bfs.expert_evaluation_required = bool(
        form_data.get("expert_evaluation_required", False)
    )

    # ------------------------------------------------------------------
    # Section 6 — Pathway and Positioning
    # ------------------------------------------------------------------
    bfs.canvas_course_code = _str(form_data, "canvas_course_code") or None
    bfs.pathway_name = _str(form_data, "pathway_name") or None

    # canvas_pathway_length — needed for S3A07 (seq 3 in pathway of 3 or 4)
    cpl = form_data.get("canvas_pathway_length")
    if cpl is not None:
        try:
            bfs.canvas_pathway_length = int(cpl)
        except (TypeError, ValueError):
            pass

    # pathway_position — needed for S3A13 (standalone attendance badge)
    bfs.pathway_position = _str(form_data, "pathway_position") or None

    # canvas_sequence_number — direct position override without a full course code
    csn = form_data.get("canvas_sequence_number")
    if csn is not None:
        try:
            bfs.canvas_sequence_number = int(csn)
        except (TypeError, ValueError):
            pass

    # ------------------------------------------------------------------
    # Section 7 — Skill and Competency Signals
    # ------------------------------------------------------------------
    bfs.real_world_context = bool(form_data.get("real_world_context", False))
    bfs.multi_context_evidence = bool(form_data.get("multi_context_evidence", False))
    bfs.leadership_evidence = bool(form_data.get("leadership_evidence", False))

    ksa = form_data.get("ksa_dimensions", [])
    bfs.ksa_dimensions = ksa if isinstance(ksa, list) else []

    return bfs


def map_free_text_to_bfs(raw_text: str) -> BadgeFactSheet:
    """
    Wrap a plain-text description into a minimal BFS.

    All signals will come from NLP extraction. The full text is
    stored in both earning_criteria_text and raw_input_text so
    the NLP layer has maximum surface area to work with.

    A lightweight keyword pass resolves issuer when the submitter
    mentions a known NJIT office by name or abbreviation — avoids
    a mandatory follow-up question for straightforward free-text
    submissions.
    """
    bfs = BadgeFactSheet()
    bfs.structured_source_type = "free_text"
    bfs.obv_version = None
    bfs.raw_input_text = raw_text
    bfs.obv_fields_present = []

    # For free text, treat the whole blob as both description and criteria
    bfs.badge_description = raw_text.strip()
    bfs.earning_criteria_text = raw_text.strip()

    # Layer 0 — issuer keyword detection.
    # Checked before URL-based resolver so explicit mentions take precedence.
    # Order matters: longer / more specific strings first to avoid false matches.
    _lower = raw_text.lower()
    _ISSUER_KEYWORDS: list[tuple[str, list[str]]] = [
        ("OSIL",      ["student involvement and leadership",
                       "student involvement office",
                       "student involvement",
                       "osil"]),
        ("LDI",       ["learning and development institute",
                       "learning and development office",
                       "continuing education office",
                       " ldi "]),
        ("Makerspace", ["makerspace"]),
        ("NCE",       ["newark college of engineering"]),
        ("OGI",       ["office of global initiatives",
                       " ogi "]),
    ]
    for issuer_name, keywords in _ISSUER_KEYWORDS:
        if any(kw in _lower for kw in keywords):
            bfs.issuer = issuer_name
            break

    return bfs


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------

def _str(data: Dict[str, Any], key: str) -> str:
    """Return a stripped string value or empty string if missing/None."""
    val = data.get(key, "")
    return str(val).strip() if val is not None else ""
