"""
POST /review — apply a human reviewer decision to a classification.

Input:  ReviewRequest (log_id OR review_token + reviewer decision fields)
Output: Updated GovernanceLog record

Validation rules:
  - Either log_id or review_token must be provided
  - reviewer_status must be "accepted" or "overridden"
  - If "overridden": override_reason is required
  - If "overridden": at least one of override_category/type/level must be set
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.governance_log import GovernanceLog
from app.services.logging.governance_logger import get_log, update_log_review
from database import get_db

router = APIRouter()

_VALID_STATUSES = {"accepted", "overridden"}


class ReviewRequest(BaseModel):
    log_id: Optional[str] = None
    review_token: Optional[str] = None
    reviewer_status: str
    reviewer_id: str
    override_reason: Optional[str] = None
    override_category: Optional[str] = None
    override_type: Optional[str] = None
    override_level: Optional[str] = None


def _resolve_log(req: ReviewRequest, db: Session) -> GovernanceLog:
    """Resolve a GovernanceLog from either log_id or review_token."""
    if req.log_id:
        return get_log(req.log_id, db)

    if req.review_token:
        log = (
            db.query(GovernanceLog)
            .filter(GovernanceLog.review_token == req.review_token)
            .first()
        )
        if log is None:
            raise HTTPException(status_code=404, detail="Review token not found.")
        return log

    raise HTTPException(
        status_code=400,
        detail="Either log_id or review_token must be provided.",
    )


@router.post("/review", response_model=None)
def review_classification(
    req: ReviewRequest,
    db: Session = Depends(get_db),
) -> dict:
    """
    Apply a reviewer decision (accept or override) to an existing governance log.

    Returns the updated GovernanceLog serialized as a dict.
    """
    # --- Validate identifier ---
    if not req.log_id and not req.review_token:
        raise HTTPException(
            status_code=400,
            detail="Either log_id or review_token must be provided.",
        )

    # --- Validate status ---
    if req.reviewer_status not in _VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid reviewer_status '{req.reviewer_status}'. "
                f"Must be one of: {sorted(_VALID_STATUSES)}"
            ),
        )

    if req.reviewer_status == "overridden":
        if not req.override_reason or not req.override_reason.strip():
            raise HTTPException(
                status_code=400,
                detail="override_reason is required when reviewer_status is 'overridden'.",
            )
        if (
            req.override_category is None
            and req.override_type is None
            and req.override_level is None
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    "At least one of override_category, override_type, or override_level "
                    "must be provided when reviewer_status is 'overridden'."
                ),
            )

    # --- Resolve log from id or token ---
    log = _resolve_log(req, db)
    log_id = log.id

    # --- Apply review ---
    log = update_log_review(
        log_id=log_id,
        reviewer_status=req.reviewer_status,
        reviewer_id=req.reviewer_id,
        override_reason=req.override_reason,
        override_category=req.override_category,
        override_type=req.override_type,
        override_level=req.override_level,
        db=db,
    )

    return _log_to_dict(log)


def _log_to_dict(log: GovernanceLog) -> dict:
    """Serialize a GovernanceLog ORM object to a plain dict for the API response."""
    return {
        "id": log.id,
        "badge_id": log.badge_id,
        "badge_title": log.badge_title,
        "issuer": log.issuer,
        "input_type": log.input_type,
        "submitter_email": log.submitter_email,
        "reviewer_email": log.reviewer_email,
        "review_token": log.review_token,
        "review_token_expires_at": log.review_token_expires_at,
        "recommended_category": log.recommended_category,
        "recommended_type": log.recommended_type,
        "recommended_level": log.recommended_level,
        "confidence": log.confidence,
        "triggered_rules": log.triggered_rules,
        "explanation_text": log.explanation_text,
        "reviewer_status": log.reviewer_status,
        "reviewer_id": log.reviewer_id,
        "override_reason": log.override_reason,
        "override_category": log.override_category,
        "override_type": log.override_type,
        "override_level": log.override_level,
        "final_category": log.final_category,
        "final_type": log.final_type,
        "final_level": log.final_level,
        "final_locked_decision": log.final_locked_decision,
        "created_at": log.created_at,
        "reviewed_at": log.reviewed_at,
        "notification_sent_at": log.notification_sent_at,
        "decision_notification_sent_at": log.decision_notification_sent_at,
    }
