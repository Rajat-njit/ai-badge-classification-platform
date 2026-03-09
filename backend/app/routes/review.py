"""
POST /review — apply a human reviewer decision to a classification.

Input:  ReviewRequest (log_id + reviewer decision fields)
Output: Updated GovernanceLog record

Validation rules:
  - reviewer_status must be "accepted" or "overridden"
  - If "overridden": override_reason is required
  - If "overridden": at least one of override_category/type/level must be set
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.governance_log import GovernanceLog
from app.services.logging.governance_logger import update_log_review
from database import get_db

router = APIRouter()

_VALID_STATUSES = {"accepted", "overridden"}


class ReviewRequest(BaseModel):
    log_id: str
    reviewer_status: str
    reviewer_id: str
    override_reason: Optional[str] = None
    override_category: Optional[str] = None
    override_type: Optional[str] = None
    override_level: Optional[str] = None


@router.post("/review", response_model=None)
def review_classification(
    req: ReviewRequest,
    db: Session = Depends(get_db),
) -> dict:
    """
    Apply a reviewer decision (accept or override) to an existing governance log.

    Returns the updated GovernanceLog serialized as a dict.
    """
    # --- Validation ---
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

    # --- Apply review (get_log inside will raise 404 if not found) ---
    log = update_log_review(
        log_id=req.log_id,
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
    }
