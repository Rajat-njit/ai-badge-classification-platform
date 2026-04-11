"""
test_edge_cases.py

Edge case tests — Upgrade 3 Categories 2 and 3.

Category 2: Input validation (EC01–EC03) — exercised via POST /ingest.
Category 3: Review workflow validation (EC26, EC29, EC30) — exercised via POST /review.

EC01  Whitespace-only field detection
EC02  Criteria identical to description
EC03  Minimum content warning (warning-only, does not block)
EC26  Identical override silently becomes acceptance
EC29  Minimum override reason length (≥ 20 characters)
EC30  Invalid taxonomy type+level combination rejected
"""

import os
import sys
import tempfile

_db_fd, _db_path = tempfile.mkstemp(suffix=".db")
os.close(_db_fd)
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_db_path}")

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c
    try:
        os.unlink(_db_path)
    except OSError:
        pass


def _ingest(client: TestClient, payload: dict) -> dict:
    """POST /ingest with form input_type. Returns the BFS dict."""
    resp = client.post("/ingest", json={"input_type": "form", "payload": payload})
    assert resp.status_code == 200, f"/ingest returned {resp.status_code}: {resp.text}"
    return resp.json()


# ---------------------------------------------------------------------------
# EC01 — Whitespace-only field detection
# ---------------------------------------------------------------------------

class TestEC01_WhitespaceFields:

    def test_ec01_whitespace_title_treated_as_null(self, client):
        """badge_title = '   ' must be set to None and flagged as missing."""
        bfs = _ingest(client, {
            "badge_title": "   ",
            "badge_description": "A badge that recognizes completion of a comprehensive workshop on leadership skills.",
            "issuer": "OSIL",
            "earning_criteria_text": "Attend the full-day workshop and complete the reflection activity.",
        })
        assert bfs["badge_title"] is None
        assert "badge_title" in bfs["missing_signals"]
        assert bfs["needs_followup_questions"] is True

    def test_ec01_whitespace_description_treated_as_null(self, client):
        """badge_description = '\\n\\n' must be set to None and flagged as missing."""
        bfs = _ingest(client, {
            "badge_title": "Leadership Workshop",
            "badge_description": "\n\n",
            "issuer": "OSIL",
            "earning_criteria_text": "Attend the full-day workshop and complete the reflection activity.",
        })
        assert bfs["badge_description"] is None
        assert "badge_description" in bfs["missing_signals"]

    def test_ec01_whitespace_criteria_treated_as_null(self, client):
        """earning_criteria_text = '  \\t  ' must be set to None and flagged as missing."""
        bfs = _ingest(client, {
            "badge_title": "Leadership Workshop",
            "badge_description": "A badge that recognizes completion of a comprehensive workshop on leadership skills.",
            "issuer": "OSIL",
            "earning_criteria_text": "  \t  ",
        })
        assert bfs["earning_criteria_text"] is None
        assert "earning_criteria_text" in bfs["missing_signals"]


# ---------------------------------------------------------------------------
# EC02 — Criteria identical to description
# ---------------------------------------------------------------------------

class TestEC02_CriteriaIdenticalToDescription:

    _SHARED_TEXT = (
        "This badge is awarded to NJIT students who attended the annual "
        "leadership workshop and completed all required activities."
    )

    def test_ec02_criteria_identical_to_description(self, client):
        """When earning_criteria_text == badge_description the system must flag it."""
        bfs = _ingest(client, {
            "badge_title": "Leadership Workshop",
            "badge_description": self._SHARED_TEXT,
            "issuer": "OSIL",
            "earning_criteria_text": self._SHARED_TEXT,
        })
        assert "earning_criteria_meaningful_content" in bfs["missing_signals"]
        assert bfs["needs_followup_questions"] is True
        assert "criteria_identical_to_description" in (bfs["confidence_notes"] or "")


# ---------------------------------------------------------------------------
# EC03 — Minimum content warning (warning-only)
# ---------------------------------------------------------------------------

class TestEC03_MinimumContentWarnings:

    def test_ec03_short_description_adds_warning_not_missing_signal(self, client):
        """A short description adds a confidence_notes warning but NOT a missing_signal."""
        bfs = _ingest(client, {
            "badge_title": "Quick Badge",
            "badge_description": "Short desc",          # < 50 chars
            "issuer": "OSIL",
            "earning_criteria_text": "Attend the full-day workshop and submit the reflection form.",
        })
        assert "description_too_short" in (bfs["confidence_notes"] or "")
        assert "badge_description" not in bfs["missing_signals"]

    def test_ec03_short_criteria_adds_warning_not_missing_signal(self, client):
        """A short criteria adds a confidence_notes warning but NOT a missing_signal."""
        bfs = _ingest(client, {
            "badge_title": "Quick Badge",
            "badge_description": "A badge that recognizes completion of a comprehensive workshop on leadership.",
            "issuer": "OSIL",
            "earning_criteria_text": "Do task",         # < 30 chars
        })
        assert "criteria_too_short" in (bfs["confidence_notes"] or "")
        assert "earning_criteria_text" not in bfs["missing_signals"]


# ---------------------------------------------------------------------------
# Helpers shared by EC26 / EC29 / EC30 tests
# ---------------------------------------------------------------------------

# A minimal OSIL attendance badge — classifies as Co-Curricular / Souvenir / Souvenir.
_SOUVENIR_FORM = {
    "badge_title": "Leadership Workshop",
    "badge_description": (
        "A badge recognizing NJIT students who completed the annual "
        "OSIL leadership workshop."
    ),
    "issuer": "OSIL",
    "earning_criteria_text": "Attend the full-day workshop and submit the reflection activity.",
}


def _classify_badge(client) -> dict:
    """
    Classify a simple badge and return the full ClassificationResult dict.
    Ingest + classify in one call.
    """
    ingest_resp = client.post(
        "/ingest", json={"input_type": "form", "payload": _SOUVENIR_FORM}
    )
    assert ingest_resp.status_code == 200, ingest_resp.text
    bfs = ingest_resp.json()

    classify_resp = client.post("/classify", json=bfs)
    assert classify_resp.status_code == 200, classify_resp.text
    return classify_resp.json()


def _review(client, log_id: str, **kwargs) -> object:
    """POST /review and return the raw Response object."""
    return client.post("/review", json={"log_id": log_id, **kwargs})


# ---------------------------------------------------------------------------
# EC29 — Minimum override reason length
# ---------------------------------------------------------------------------

class TestEC29_MinimumOverrideReason:

    def test_ec29_override_reason_too_short(self, client):
        """override_reason shorter than 20 chars must return 400."""
        result = _classify_badge(client)
        log_id = result["governance"]["log_id"]

        resp = _review(
            client,
            log_id,
            reviewer_status="overridden",
            reviewer_id="tester",
            override_reason="Wrong",          # 5 chars — too short
            override_category="Academic",
        )
        assert resp.status_code == 400
        assert "20 characters" in resp.json()["detail"]

    def test_ec29_override_reason_exactly_20_chars(self, client):
        """override_reason of exactly 20 chars must be accepted (boundary value)."""
        result = _classify_badge(client)
        log_id = result["governance"]["log_id"]

        resp = _review(
            client,
            log_id,
            reviewer_status="overridden",
            reviewer_id="tester",
            override_reason="A" * 20,         # exactly 20 chars — must pass
            override_category="Academic",     # different from recommended Co-Curricular
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# EC30 — Invalid taxonomy combination validation
# ---------------------------------------------------------------------------

class TestEC30_InvalidTaxonomyCombination:

    def test_ec30_invalid_taxonomy_combination(self, client):
        """Skill type + Foundational level is an invalid combination — must return 400."""
        result = _classify_badge(client)
        log_id = result["governance"]["log_id"]

        resp = _review(
            client,
            log_id,
            reviewer_status="overridden",
            reviewer_id="tester",
            override_reason="Testing invalid combination here",   # ≥ 20 chars
            override_type="Skill",
            override_level="Foundational",   # invalid for Skill
        )
        assert resp.status_code == 400
        assert "Invalid taxonomy combination" in resp.json()["detail"]

    def test_ec30_valid_taxonomy_combination(self, client):
        """Skill type + Application level is valid — must return 200."""
        result = _classify_badge(client)
        log_id = result["governance"]["log_id"]

        resp = _review(
            client,
            log_id,
            reviewer_status="overridden",
            reviewer_id="tester",
            override_reason="Confirmed skill badge application level",  # ≥ 20 chars
            override_type="Skill",
            override_level="Application",    # valid for Skill
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# EC26 — Identical override detection
# ---------------------------------------------------------------------------

class TestEC26_IdenticalOverride:

    def test_ec26_identical_override_treated_as_acceptance(self, client):
        """
        Submitting override values that match the system recommendation
        must silently resolve to reviewer_status == 'accepted'.
        """
        result = _classify_badge(client)
        log_id = result["governance"]["log_id"]
        rec = result["classification"]

        resp = _review(
            client,
            log_id,
            reviewer_status="overridden",
            reviewer_id="tester",
            override_reason="Confirmed correct classification",   # ≥ 20 chars
            override_category=rec["category"],   # matches recommended
            override_type=rec["type"],           # matches recommended
            override_level=rec["level"],         # matches recommended
        )
        assert resp.status_code == 200
        assert resp.json()["reviewer_status"] == "accepted"
