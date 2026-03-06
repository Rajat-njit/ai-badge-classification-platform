"""
POST /classify — runs the classification engine on a BadgeFactSheet.

Input:  BadgeFactSheet (from POST /ingest or manually constructed)
Output: ClassificationResult (with governance.log_id populated)

The route owns governance log creation so the engine stays DB-free.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.badge_fact_sheet import BadgeFactSheet
from app.models.classification_result import ClassificationResult
from app.services.classification.engine import run_classification
from app.services.logging.governance_logger import create_log
from app.services.nlp.signal_extractor import SignalExtractor
from app.utils.canvas_code_parser import parse_canvas_code
from database import get_db

router = APIRouter()

_signal_extractor = SignalExtractor()


@router.post("/classify", response_model=ClassificationResult)
def classify_badge(
    bfs: BadgeFactSheet,
    db: Session = Depends(get_db),
) -> ClassificationResult:
    """
    Classify a BadgeFactSheet through all three rule-engine stages.

    Steps:
      1. Run NLP signal extraction (idempotent — skips already-filled fields)
      2. Run classification engine (Stage 1 → 2 → 3)
      3. Create governance log record
      4. Return ClassificationResult with log_id
    """
    try:
        # Step 1a — Parse canvas code if present but not yet parsed
        # (normalizer does this; this is a safety step for direct BFS submissions)
        if bfs.canvas_course_code and bfs.canvas_sequence_number is None:
            parsed = parse_canvas_code(bfs.canvas_course_code)
            if parsed:
                bfs.canvas_pathway_code = parsed.get("canvas_pathway_code")
                bfs.canvas_sequence_number = parsed.get("canvas_sequence_number")
                bfs.is_capstone = bfs.is_capstone or parsed.get("is_capstone", False)

        # Step 1b — NLP extraction (fills any signals not already set)
        bfs = _signal_extractor.extract_all(bfs)

        # Step 2 — Classification engine
        result = run_classification(bfs)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification error: {e}")

    # Step 3 — Governance log (delegated to governance_logger)
    log = create_log(bfs, result, db)

    # Step 4 — Fill governance.log_id now that we have it
    result.governance.log_id = log.id

    return result
