"""
Stage 1 — Badge Category classification.

Determined by: Audience and Institutional Context.
Rules S1R01–S1R08 from .md Section 8.

Returns:
    {
        "category":        str | None,
        "confidence":      "High" | "Medium" | "Low",
        "rules_triggered": list[str],
    }

.md Rule R1: Taxonomy rules are locked.
.md Rule R2: Rule engine decides — not any LLM.
"""

from app.models.badge_fact_sheet import BadgeFactSheet

# Known NJIT issuers — anything outside this set falls to S1R08
_KNOWN_ISSUERS = {"LDI", "OSIL", "Makerspace", "NCE", "OGI"}

# Audience signals that indicate faculty / staff
_FACULTY_STAFF_SIGNALS = {"educator", "faculty", "instructor", "staff"}

# Audience signals that indicate external / professional
_EXTERNAL_PROF_SIGNALS = {"professional", "workforce", "workplace", "industry"}


def classify_stage1(bfs: BadgeFactSheet) -> dict:
    """
    Classify the badge category using S1R01–S1R08.

    Mutates nothing on the BFS — pure function.
    """
    issuer = bfs.issuer
    rules: list[str] = []

    # ------------------------------------------------------------------
    # S1R01 — LDI → Faculty & Staff Development
    # Condition: audience is faculty/staff employee
    # ------------------------------------------------------------------
    if issuer == "LDI":
        if _is_faculty_staff(bfs):
            return {
                "category": "Faculty & Staff Development",
                "confidence": "High",
                "rules_triggered": ["S1R01"],
            }

    # ------------------------------------------------------------------
    # S1R02 — LDI → Continuing & Professional Education
    # Condition: audience is external professional OR PDH credits present
    # ------------------------------------------------------------------
    if issuer == "LDI":
        if _is_external_professional(bfs):
            return {
                "category": "Continuing & Professional Education",
                "confidence": "High",
                "rules_triggered": ["S1R02"],
            }

    # ------------------------------------------------------------------
    # S1R03 — LDI + Micro Credential
    # Audience not clear from S1R01/S1R02 — route by any audience hint
    # ------------------------------------------------------------------
    if issuer == "LDI" and bfs.achievement_type == "Micro Credential":
        # Check audience_signal for any faculty/staff keyword
        sig = (bfs.audience_signal or "").lower()
        if any(kw in sig for kw in _FACULTY_STAFF_SIGNALS):
            return {
                "category": "Faculty & Staff Development",
                "confidence": "High",
                "rules_triggered": ["S1R03"],
            }
        # Default Micro Credential → Continuing & Professional Education
        return {
            "category": "Continuing & Professional Education",
            "confidence": "High",
            "rules_triggered": ["S1R03"],
        }

    # ------------------------------------------------------------------
    # S1R04 — OSIL → Co-Curricular and Extra-Curricular
    # ------------------------------------------------------------------
    if issuer == "OSIL":
        return {
            "category": "Co-Curricular and Extra-Curricular",
            "confidence": "High",
            "rules_triggered": ["S1R04"],
        }

    # ------------------------------------------------------------------
    # S1R05 — Makerspace → Academic
    # NOTE: Open question Q002 — confirm with supervisor
    # ------------------------------------------------------------------
    if issuer == "Makerspace":
        return {
            "category": "Academic",
            "confidence": "High",
            "rules_triggered": ["S1R05"],
        }

    # ------------------------------------------------------------------
    # S1R06 — NCE → Academic
    # ------------------------------------------------------------------
    if issuer == "NCE":
        return {
            "category": "Academic",
            "confidence": "High",
            "rules_triggered": ["S1R06"],
        }

    # ------------------------------------------------------------------
    # S1R07 — OGI → Open question (no official taxonomy category)
    # ------------------------------------------------------------------
    if issuer == "OGI":
        return {
            "category": None,
            "confidence": "Low",
            "rules_triggered": ["S1R07"],
            "note": (
                "Open question Q001: OGI compliance badges have no official "
                "taxonomy category. Supervisor confirmation required."
            ),
        }

    # ------------------------------------------------------------------
    # Residual LDI — issuer is LDI but no audience signal matched S1R01/S1R02
    # Default to Continuing & Professional Education (broadest LDI mandate)
    # ------------------------------------------------------------------
    if issuer == "LDI":
        return {
            "category": "Continuing & Professional Education",
            "confidence": "Medium",
            "rules_triggered": ["S1R02"],
            "note": (
                "Audience type unclear — defaulting to Continuing & Professional "
                "Education. Confirm audience to raise confidence."
            ),
        }

    # ------------------------------------------------------------------
    # S1R08 — Issuer missing or unrecognised
    # ------------------------------------------------------------------
    return {
        "category": None,
        "confidence": "Low",
        "rules_triggered": ["S1R08"],
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _is_faculty_staff(bfs: BadgeFactSheet) -> bool:
    """True if any audience signal points to faculty or NJIT employee."""
    if bfs.audience_type in ("njit_employee", "faculty"):
        return True
    sig = (bfs.audience_signal or "").lower()
    return any(kw in sig for kw in _FACULTY_STAFF_SIGNALS)


def _is_external_professional(bfs: BadgeFactSheet) -> bool:
    """True if any audience signal points to external / professional."""
    if bfs.audience_type == "external_professional":
        return True
    if bfs.pdh_credits is not None:
        return True
    sig = (bfs.audience_signal or "").lower()
    return any(kw in sig for kw in _EXTERNAL_PROF_SIGNALS)
