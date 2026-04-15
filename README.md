# NJIT AI-Assisted Digital Badge Classification Tool

> A deterministic, explainable, and auditable classification system for NJIT's official digital badge taxonomy.

**Capstone Project — Spring 2026**
New Jersey Institute of Technology
Faculty Advisor: Prabhat Vaish | Supervisor: Kerry Eberhardt

---

## Table of Contents

1. [Overview](#overview)
2. [Key Features](#key-features)
3. [System Architecture](#system-architecture)
4. [Taxonomy](#taxonomy)
5. [Tech Stack](#tech-stack)
6. [Project Structure](#project-structure)
7. [Getting Started](#getting-started)
8. [API Reference](#api-reference)
9. [NLP Pipeline](#nlp-pipeline)
10. [Classification Rule Engine](#classification-rule-engine)
11. [Testing](#testing)
12. [Environment Variables](#environment-variables)
13. [Reviewer Dashboard](#reviewer-dashboard)

---

## Overview

NJIT issues digital badges to students, faculty, staff, and external professionals across dozens of programs. Each badge must be formally classified against a three-stage institutional taxonomy — Category, Type, and Level — before it is published.

This system operationalizes that taxonomy into a reproducible, auditable classification pipeline. It accepts badge metadata in any format (OBv3 JSON, OBv2 JSON, structured form, or free text), normalizes it into a standard internal representation called the **Badge Fact Sheet**, runs it through a deterministic rule engine, and produces a fully explained classification recommendation that a human reviewer must accept or override.

**This is a decision-support tool, not an autonomous authority.** Every classification is a recommendation. The final decision always belongs to a human reviewer.

---

## Key Features

### Input Flexibility
- **OBv3 JSON** — Open Badges v3 format with full alignment and achievementType parsing
- **OBv2 JSON** — Legacy format with issuer URL resolution and alignment field differences
- **Structured Form** — Guided submission form with all relevant fields
- **Free Text** — Plain-language badge description parsed via NLP

### Classification Engine
- **Deterministic, three-stage rule engine** — Category → Type → Level
- **Four parallel NLP layers** extract classification signals from badge text
- **Word-boundary-aware phrase matching** prevents false positives from substrings
- **Negation-aware** phrase and Bloom verb detection
- **Conflict detection** — flags when multiple level signals disagree
- **Implied series detection** — advisory note when a badge title suggests a pathway

### Explainability and Governance
- Every classification includes a full plain-English explanation
- All triggered rule IDs recorded (e.g. `S1R04`, `S2R05`, `S3S01`)
- Complete audit trail stored in a SQLite governance log
- Signal sources tracked: `keyword_rule` / `regex_pattern` / `spacy_verb` / `structured_field`

### Two-User Review Workflow
- **Submitter** submits a badge and receives a confirmation with status
- **Reviewer** receives a review link, views the classification, and accepts or overrides
- Override validation: minimum 20-character reason, valid taxonomy combination enforcement
- Identical-to-recommendation overrides silently resolve as acceptances
- Password-protected reviewer dashboard with pending queue and review history

### Input Validation
- Whitespace-only fields detected and flagged as missing
- Criteria identical to description detected and flagged
- Short-content advisory warnings (non-blocking)

---

## System Architecture

```
Raw Input (OBv3 / OBv2 / Form / Free Text)
         │
         ▼
┌─────────────────────┐
│   POST /ingest      │  Normalizer · Issuer Resolver · Canvas Code Parser
│   BadgeFactSheet    │  · Input Validation (EC01–EC03, EC24)
└────────┬────────────┘
         │  BadgeFactSheet (BFS)
         ▼
┌─────────────────────┐
│   POST /classify    │  NLP Pipeline (Layers 1–4) · Rule Engine (Stages 1–3)
│ ClassificationResult│  · Governance Log creation
└────────┬────────────┘
         │  log_id + recommendation
         ▼
┌─────────────────────┐
│   POST /review      │  Human Reviewer accepts or overrides
│   GovernanceLog     │  · Final decision locked
└─────────────────────┘
```

### NLP Pipeline (4 Layers)

| Layer | Technology | Purpose |
|---|---|---|
| 1 | Exact phrase matching | Level, assessment, audience, and purpose signals |
| 2 | Regex patterns | Paraphrased level and assessment signals |
| 3 | spaCy `en_core_web_sm` | Bloom's Taxonomy verb extraction |
| 4 | LLM stub ( API) | Gap-filling — disabled by default (`USE_LLM=false`) |

---

## Taxonomy

NJIT's official badge taxonomy has three classification stages.

### Stage 1 — Category (Audience and Institutional Context)

| Category | Governing Office |
|---|---|
| Academic | Office of Digital Learning / Registrar |
| Co-Curricular and Extra-Curricular | OSIL |
| Continuing & Professional Education | LDI |
| Faculty & Staff Development | HR / CEIE |

### Stage 2 — Type (Earning Criteria and Assessment)

| Type | Assessment Required |
|---|---|
| Souvenir | Attendance / participation only — no assessment |
| Achievement | Auto-assessed completion — no expert evaluation |
| Skill | Expert-scored skill demonstration |
| Competency | Expert evaluation across Knowledge, Skills, and Abilities |

### Stage 3 — Level (Evidence, Bloom Level, Pathway Position)

Level options are **type-dependent** and not interchangeable across types.

| Type | Valid Levels |
|---|---|
| Souvenir | Souvenir |
| Achievement | Foundational · Milestone · Terminal |
| Skill | Awareness · Application · Mastery |
| Competency | Demonstrated · Integrated · Exemplary |

---

## Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Backend Framework | Python + FastAPI | Python 3.11+, FastAPI 0.115 |
| Database | SQLite + SQLAlchemy | 2.0 |
| Data Validation | Pydantic | 2.x |
| NLP | spaCy | 3.8 (`en_core_web_sm`) |
| LLM (stub) | Anthropic SDK | 0.34 |
| Frontend | React + Vite | React 19, Vite 8 |
| Styling | Tailwind CSS | 4.x |
| HTTP Client | Axios | 1.x |
| Testing | pytest + httpx | 8.x |

---

## Project Structure

```
ai-badge-classification-tool/
├── .md                          # Architecture and taxonomy rules (source of truth)
├── README.md                          # This file
├── .env.example                       # Environment variable template
│
├── backend/
│   ├── requirements.txt
│   ├── database.py                    # SQLAlchemy engine, session, migrations
│   └── app/
│       ├── main.py                    # FastAPI app, CORS, router registration
│       ├── routes/
│       │   ├── ingestion.py           # POST /ingest
│       │   ├── classification.py      # POST /classify
│       │   ├── review.py              # POST /review
│       │   ├── logs.py                # GET /logs, GET /logs/{id}
│       │   └── reviewer.py            # POST /reviewer/auth, GET /reviewer/queue
│       ├── models/
│       │   ├── badge_fact_sheet.py    # Core Pydantic BFS model (60+ fields)
│       │   ├── classification_result.py
│       │   └── governance_log.py      # SQLAlchemy ORM model
│       ├── services/
│       │   ├── ingestion/
│       │   │   ├── parser.py          # OBv2 + OBv3 JSON parser
│       │   │   └── form_mapper.py     # Form fields → BadgeFactSheet
│       │   ├── normalization/
│       │   │   ├── normalizer.py      # Orchestrates full ingestion pipeline
│       │   │   └── issuer_resolver.py # URL → issuer name (IR01–IR07)
│       │   ├── nlp/
│       │   │   ├── phrase_dictionary.py  # Layer 1: phrase matching (EC17, EC18, EC19)
│       │   │   ├── pattern_rules.py      # Layer 2: regex patterns
│       │   │   ├── bloom_extractor.py    # Layer 3: spaCy Bloom verb extraction (EC20)
│       │   │   ├── llm_extractor.py      # Layer 4: LLM stub
│       │   │   └── signal_extractor.py   # Orchestrates all 4 layers
│       │   ├── classification/
│       │   │   ├── stage1.py          # Category rules (S1R01–S1R08)
│       │   │   ├── stage2.py          # Type rules (S2R01–S2R11)
│       │   │   ├── stage3.py          # Level rules, 4 branches
│       │   │   └── engine.py          # Orchestrates Stages 1–3
│       │   ├── explainability/
│       │   │   └── explainer.py       # Human-readable explanation generator
│       │   └── logging/
│       │       └── governance_logger.py
│       └── utils/
│           ├── canvas_code_parser.py  # MCAI.002.03 → pathway + sequence
│           └── obv_version_detector.py
│   └── tests/                         # 290 tests across 10 test files
│
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── SubmitBadge.jsx            # Three-tab input (form / JSON / free text)
│       │   ├── ReviewResult.jsx           # Classification result display
│       │   ├── GovernanceLogs.jsx         # Audit trail table
│       │   ├── SubmissionConfirmation.jsx
│       │   └── reviewer/
│       │       ├── ReviewerLogin.jsx
│       │       ├── ReviewerDashboard.jsx
│       │       └── ReviewerReview.jsx
│       ├── components/
│       │   └── ProtectedRoute.jsx
│       ├── context/
│       │   └── ReviewerContext.jsx
│       └── services/
│           └── api.js
│
├── sample_data/
│   ├── real_badges/                   # Real NJIT badge JSON fixtures
│   ├── synthetic_badges/
│   │   ├── happy_path/                # One badge per valid taxonomy combination
│   │   └── edge_cases/                # Conflict, missing, ambiguous inputs
│   └── test_manifest.json
│
├── docs/                              # Architecture, taxonomy, testing docs
└── scripts/
    ├── load_sample_data.py
    └── reset_database.py
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Git

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ai-badge-classification-tool
```

### 2. Backend Setup

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Download the spaCy language model
python -m spacy download en_core_web_sm

# Configure environment variables
cp ../.env.example .env
# Edit .env — set REVIEWER_PASSWORD and any other values you want to change
```

### 3. Start the Backend

```bash
# From the backend/ directory
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API is available at `http://localhost:8000`.
Interactive API docs: `http://localhost:8000/docs`

> The SQLite database (`badges.db`) and all tables are created automatically on first startup.

### 4. Frontend Setup

```bash
# From the repo root
cd frontend
npm install
npm run dev
```

The application is available at `http://localhost:5173`.

### 5. Load Sample Data (Optional)

```bash
# From the backend/ directory, with the server running
python ../scripts/load_sample_data.py
```

### 6. Reset the Database (Optional)

```bash
# Clears badges.db for a fresh start
python ../scripts/reset_database.py
```

---

## API Reference

All endpoints are documented interactively at `http://localhost:8000/docs`.

### Core Workflow Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/ingest` | Normalize raw input into a BadgeFactSheet |
| `POST` | `/classify` | Run the rule engine on a BadgeFactSheet |
| `POST` | `/review` | Submit a reviewer decision (accept or override) |
| `GET` | `/logs` | List all governance log entries |
| `GET` | `/logs/{log_id}` | Full detail for a single log entry |
| `GET` | `/health` | Health check |

### Reviewer Workflow Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/reviewer/auth` | Authenticate and receive an access token |
| `GET` | `/reviewer/queue` | Pending queue and recent reviews |
| `GET` | `/reviewer/review/{token}` | Load a badge for review via email link |

### POST /ingest — Request Body

```json
{
  "input_type": "form",
  "payload": {
    "badge_title": "Leadership Workshop",
    "badge_description": "Recognizes NJIT students who completed the annual workshop.",
    "issuer": "OSIL",
    "earning_criteria_text": "Attend the full-day workshop and submit the reflection.",
    "submitter_email": "student@njit.edu",
    "reviewer_email": "reviewer@njit.edu"
  }
}
```

`input_type` values: `form` | `obv3_json` | `obv2_json` | `free_text`

### POST /classify — Response

```json
{
  "badge_id": "uuid",
  "badge_title": "Leadership Workshop",
  "issuer": "OSIL",
  "classification": {
    "category": "Co-Curricular and Extra-Curricular",
    "type": "Souvenir",
    "level": "Souvenir",
    "confidence": "High",
    "level_branch_used": "souvenir"
  },
  "rules_triggered": ["S1R04", "S2R05", "S3S01"],
  "signals_used": {
    "issuer": { "value": "OSIL", "source": "structured_field" },
    "assessment_type": { "value": "attendance", "source": "keyword_rule" }
  },
  "explanation": "CATEGORY: Classified as Co-Curricular and Extra-Curricular...",
  "follow_up_needed": false,
  "missing_signals": [],
  "governance": {
    "log_id": "uuid",
    "classified_at": "2026-04-14T10:00:00Z",
    "reviewer_status": "pending_review"
  }
}
```

### POST /review — Override Example

```json
{
  "log_id": "uuid",
  "reviewer_id": "kerry.eberhardt",
  "reviewer_status": "overridden",
  "override_reason": "Badge includes a reflection component requiring evaluation.",
  "override_category": "Co-Curricular and Extra-Curricular",
  "override_type": "Achievement",
  "override_level": "Foundational"
}
```

**Validation rules enforced by the endpoint:**
- `override_reason` must be at least 20 characters (EC29)
- `override_type` + `override_level` must be a valid taxonomy pairing (EC30)
- If all override values match the recommendation, status silently resolves to `accepted` (EC26)

---

## NLP Pipeline

Signal extraction runs during `POST /classify` via four sequential layers.

### Layer 1 — Phrase Dictionary (`phrase_dictionary.py`)

Case-insensitive exact matching against curated dictionaries for level, assessment type, audience, and badge purpose. Key behaviors:

- **Word-boundary matching (EC17)** — `\b` anchors prevent substring false positives. `precapstone` does not trigger the `capstone` Terminal phrase.
- **Negation detection (EC18)** — phrases preceded by negation words (`not`, `never`, `without`, etc.) within a 10-word window are skipped.
- **Conflict detection (EC19)** — when multiple non-negated phrases point to different levels, a `CONFLICT:` note is appended to `confidence_notes` and the highest-priority (longest) phrase wins.

### Layer 2 — Regex Patterns (`pattern_rules.py`)

Catches paraphrased level and assessment signals. Examples:

- `"second course in the series"` → Milestone
- `"after completing all three modules"` → Terminal
- `"expert-evaluated by faculty"` → expert_scored

### Layer 3 — Bloom's Taxonomy (`bloom_extractor.py`)

Uses spaCy's dependency parser to extract verbs and map them to Bloom's Taxonomy levels (remembering → creating). The highest detected level sets `bloom_level`, which drives Skill level classification.

- **Negation detection (EC20)** — verbs with a `neg` dependency child (e.g. `"do not demonstrate"`) are excluded from Bloom scoring.

### Layer 4 — LLM Extractor (`llm_extractor.py`)

Stub implementation connected to the Anthropic SDK. When `USE_LLM=true`, this layer queries the  API to fill any remaining `missing_signals` using structured prompting. Disabled by default to keep classification fully deterministic.

---

## Classification Rule Engine

The engine runs three sequential stages. All rules are explicit `if/elif` chains — no ML inference ever makes a classification decision.

### Stage 1 — Category (8 rules: S1R01–S1R08)

Determined by issuer identity and audience type.

| Rule | Condition | Result |
|---|---|---|
| S1R01 | LDI + faculty/staff audience | Faculty & Staff Development |
| S1R02 | LDI + external/professional audience | Continuing & Professional Education |
| S1R04 | OSIL | Co-Curricular and Extra-Curricular |
| S1R05 | Makerspace | Academic |
| S1R06 | NCE | Academic |
| S1R08 | Unknown issuer | `confidence = Low`, follow-up required |

### Stage 2 — Type (11 rules: S2R01–S2R11)

Determined by earning criteria and assessment method. Rules run in strict priority order; first match wins.

| Rule | Condition | Result |
|---|---|---|
| S2R01 | `achievementType = Micro Credential` | Achievement (Terminal in Stage 3) |
| S2R02 | `achievementType = Competency` | Competency |
| S2R05 | Attendance only / no assessment | Souvenir |
| S2R06 | Expert-scored + skill domain detected | Skill |
| S2R09 | Canvas course code or module completion | Achievement |

### Stage 3 — Level (4 independent branches)

Branches based on the Stage 2 type result.

| Branch | Type | Level Determination |
|---|---|---|
| A — Souvenir | Souvenir | Always `Souvenir` |
| B — Achievement | Achievement | Canvas sequence → prerequisite badges → self-declared phrase |
| C — Skill | Skill | Bloom level → assessment type → self-declared phrase |
| D — Competency | Competency | Leadership evidence → multi-context evidence → real-world context |

---

## Testing

```bash
# From the backend/ directory
pytest tests/ -v
```

### Test Suite — 290 Tests, All Passing

| File | What It Tests |
|---|---|
| `test_real_badges.py` | All real NJIT badge fixtures classified correctly |
| `test_synthetic_badges.py` | All 26 happy-path combinations + edge cases |
| `test_classification.py` | Rule engine unit tests per stage |
| `test_nlp.py` | NLP layer signal extraction |
| `test_api_integration.py` | Full round-trip API endpoint tests |
| `test_verification_checklist.py` | 8 key scenario regression tests (T01–T08) |
| `test_edge_cases.py` | 19 edge case tests (EC01–EC03, EC17–EC20, EC24, EC26, EC29, EC30) |
| `test_explainability.py` | Explanation content and completeness |
| `test_logging.py` | Governance log creation, update, and review |
| `test_ingestion.py` | Parser and normalizer tests |

### Edge Cases Verified

| Code | Description |
|---|---|
| EC01 | Whitespace-only field detection |
| EC02 | Criteria identical to description |
| EC03 | Minimum content warning (non-blocking) |
| EC17 | Word-boundary matching prevents substring false positives |
| EC18 | Negated level phrase detection |
| EC19 | Conflicting level phrase detection with CONFLICT note |
| EC20 | Negated Bloom verb excluded from scoring |
| EC24 | Implied series detection from badge title |
| EC26 | Identical override silently becomes acceptance |
| EC29 | Minimum override reason length (≥ 20 characters) |
| EC30 | Invalid taxonomy type+level combination rejected |

---

## Environment Variables

Copy `.env.example` to `backend/.env` before starting the server.

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./badges.db` | SQLAlchemy database URL |
| `USE_LLM` | `false` | Set to `true` to enable  API gap-filling |
| `SPACY_MODEL` | `en_core_web_sm` | spaCy model name |
| `ANTHROPIC_API_KEY` | *(empty)* | Required only when `USE_LLM=true` |
| `API_HOST` | `0.0.0.0` | Uvicorn bind address |
| `API_PORT` | `8000` | Uvicorn port |
| `ALLOWED_ORIGINS` | `http://localhost:5173` | CORS allowed origins |
| `APP_VERSION` | `1.0.0` | Reported in `/health` and API docs |
| `DEBUG` | `true` | FastAPI debug mode |
| `REVIEWER_PASSWORD` | `njit-reviewer-2026` | Reviewer dashboard password |

---

## Reviewer Dashboard

### Authentication

```
POST /reviewer/auth
{ "password": "<REVIEWER_PASSWORD>" }
→ { "access_token": "uuid" }
```

The access token is held in server memory and clears on restart. Pass it as `Authorization: Bearer <token>` on subsequent reviewer requests.

### Review Queue (`GET /reviewer/queue`)

Returns:
- **Stats** — total classified, pending review, accepted, overridden
- **Pending** — badges awaiting a reviewer decision, sorted by submission date
- **Recently reviewed** — the last 20 decisions with final outcomes

### Review via Link (`GET /reviewer/review/{token}`)

When a badge is submitted with a `reviewer_email`, a UUID review token is generated and stored in the governance log (expires after 30 days). The reviewer receives a link in the format `/reviewer/review/{token}`.

Possible responses:
- `200` — badge data returned, ready for review
- `404` — token not found
- `409` — badge already reviewed
- `410` — token expired

### Override Validation

`POST /review` enforces four rules in order:

1. **At least one override field** — `override_category`, `override_type`, or `override_level` must be provided
2. **Reason length** — `override_reason` must be ≥ 20 characters (EC29)
3. **Valid taxonomy combination** — `override_type` + `override_level` must be a valid pairing (EC30)
4. **Identical override** — if all provided values match the recommendation, `reviewer_status` silently resolves to `"accepted"` (EC26)

---

## Git History

```
67da94d  Upgrade 3 Cat 1+4: NLP accuracy and pathway edge cases (EC17–EC20, EC24)
39fbde9  Upgrade 3 Cat 3: Review workflow validation (EC26, EC29, EC30)
a310aa2  Upgrade 3: Input validation edge cases (EC01–EC03)
be6e6e2  Upgrade 1: Two-user system and reviewer dashboard
40edd2a  Upgrade 2: redesigned submission form, classification fixes, and E2E tests
6a235df  v1.0.0 — NJIT Badge Classification Tool production ready
```

---

## License

Developed as a capstone prototype for New Jersey Institute of Technology, Spring 2026.
All classification rules are derived from NJIT's official badge taxonomy documentation.
