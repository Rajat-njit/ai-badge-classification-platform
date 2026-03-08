"""
Governance Logger — four functions for creating and updating governance logs.

Owns all DB interactions for the governance_logs table.
Routes call these functions; the classification engine remains DB-free.
"""

import json
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.badge_fact_sheet import BadgeFactSheet
from app.models.classification_result import ClassificationResult
from app.models.governance_log import GovernanceLog

# Section 9 NLP signal fields stored in extracted_signals column
_NLP_SIGNAL_KEYS = {
    "audience_signal", "context_signal", "rigor_signal", "evidence_signal",
    "self_declared_level", "level_phrase_matched", "level_signal_source",
    "audience_signal_source", "needs_followup_questions", "missing_signals",
    "confidence_notes", "bloom_level", "bloom_confidence", "bloom_verbs_detected",
}


def create_log(
    bfs: BadgeFactSheet,
    result: ClassificationResult,
    db: Session,
) -> GovernanceLog:
    """
    Insert a new governance log record for a completed classification.

    - normalized_facts: full BFS serialized as JSON string
    - extracted_signals: Section 9 NLP fields only, as JSON string
    - triggered_rules: JSON array of rule IDs
    - final_category/type/level: seeded from recommended values;
      updated if a reviewer later overrides
    - reviewer_status: "pending"
    """
    bfs_dict = bfs.model_dump()
    extracted = {k: bfs_dict[k] for k in _NLP_SIGNAL_KEYS if k in bfs_dict}

    log = GovernanceLog(
        badge_id=bfs.badge_id,
        badge_title=bfs.badge_title,
        issuer=bfs.issuer,
        raw_input=bfs.raw_input_text,
        input_type=bfs.structured_source_type,
        normalized_facts=json.dumps(bfs_dict, default=str),
        extracted_signals=json.dumps(extracted, default=str),
        recommended_category=result.classification.category,
        recommended_type=result.classification.type,
        recommended_level=result.classification.level,
        confidence=result.classification.confidence,
        triggered_rules=json.dumps(result.rules_triggered),
        explanation_text=result.explanation or "",
        reviewer_status="pending",
        # Seed final decision with recommendation — updated on review
        final_category=result.classification.category,
        final_type=result.classification.type,
        final_level=result.classification.level,
    )

    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def update_log_review(
    log_id: str,
    reviewer_status: str,
    reviewer_id: str,
    override_reason: str | None,
    override_category: str | None,
    override_type: str | None,
    override_level: str | None,
    db: Session,
) -> GovernanceLog:
    """
    Apply a reviewer decision to an existing governance log record.

    accepted  → final_* = recommended_* values (no changes to classification)
    overridden → final_* = provided override_* values where given,
                 otherwise keep the recommended_* value for that stage
    Sets final_locked_decision and reviewed_at in both cases.
    """
    log = get_log(log_id, db)

    log.reviewer_status = reviewer_status
    log.reviewer_id = reviewer_id
    log.override_reason = override_reason
    log.reviewed_at = datetime.now(timezone.utc).isoformat()

    if reviewer_status == "accepted":
        log.final_category = log.recommended_category
        log.final_type = log.recommended_type
        log.final_level = log.recommended_level
        # Clear any stale override fields
        log.override_category = None
        log.override_type = None
        log.override_level = None

    elif reviewer_status == "overridden":
        log.override_category = override_category
        log.override_type = override_type
        log.override_level = override_level
        # Use override where provided, fall back to recommended for unchanged stages
        log.final_category = override_category if override_category is not None else log.recommended_category
        log.final_type = override_type if override_type is not None else log.recommended_type
        log.final_level = override_level if override_level is not None else log.recommended_level

    # Build human-readable locked decision summary
    category_str = log.final_category or "Unknown"
    type_str = log.final_type or "Unknown"
    level_str = log.final_level or "Unknown"
    log.final_locked_decision = f"{category_str} | {type_str} | {level_str}"

    db.commit()
    db.refresh(log)
    return log


def get_log(log_id: str, db: Session) -> GovernanceLog:
    """Return a single GovernanceLog by ID, or raise HTTP 404."""
    log = db.get(GovernanceLog, log_id)
    if log is None:
        raise HTTPException(status_code=404, detail=f"Log not found: {log_id}")
    return log


def get_all_logs(limit: int, offset: int, db: Session) -> dict:
    """
    Return a paginated list of GovernanceLogs ordered by created_at descending.

    Returns a dict with keys: total, offset, limit, records.
    """
    total = db.query(func.count(GovernanceLog.id)).scalar()
    records = (
        db.query(GovernanceLog)
        .order_by(GovernanceLog.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "records": records,
    }
