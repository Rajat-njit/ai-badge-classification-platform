"""
test_edge_cases.py

Input-validation edge cases — Category 2 (Upgrade 3).

Tests EC01–EC03 exercised against the normalizer via POST /ingest.
All tests use form input to have full control over field values.

EC01  Whitespace-only field detection
EC02  Criteria identical to description
EC03  Minimum content warning (warning-only, does not block)
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
