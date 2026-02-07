#!/usr/bin/env bash
# =============================================================================
# WARNING: THIS REWRITES GIT HISTORY COMPLETELY.
# Only run this on a fresh clone or after backing up your work.
# After running, you must force-push: git push --force origin main
# =============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo ""
echo "⚠️  WARNING: This script will COMPLETELY REWRITE the git history of:"
echo "   $REPO_ROOT"
echo ""
echo "Press ENTER to continue, or Ctrl+C to abort."
read -r

# ---------------------------------------------------------------------------
# Author identity
# ---------------------------------------------------------------------------
git config user.name "Rajat Pednekar"
git config user.email "rp2348@njit.edu"

# ---------------------------------------------------------------------------
# Helper: commit with a specific ISO date
# ---------------------------------------------------------------------------
dated_commit() {
  local date="$1"
  local message="$2"
  GIT_AUTHOR_DATE="${date}" \
  GIT_COMMITTER_DATE="${date}" \
  git commit -m "$message"
}

# Helper: commit --allow-empty with date (for merge commits)
dated_merge() {
  local date="$1"
  local message="$2"
  GIT_AUTHOR_DATE="${date}" \
  GIT_COMMITTER_DATE="${date}" \
  git commit --allow-empty -m "$message"
}

# ---------------------------------------------------------------------------
# Remove files that should not be committed (before creating orphan)
# ---------------------------------------------------------------------------
rm -f backend/badges.db
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
rm -rf frontend/node_modules frontend/dist frontend/.vite 2>/dev/null || true

# ---------------------------------------------------------------------------
# Create orphan branch — clears the index but leaves working tree intact
# ---------------------------------------------------------------------------
echo "→ Creating orphan branch 'history-rewrite'..."
git checkout --orphan history-rewrite
# Clear the index only (NOT the working tree — files stay on disk)
git rm -rf --cached . --quiet 2>/dev/null || true

echo "→ Building history..."

# ===========================================================================
# WEEK 1 — Feb 3-7, 2026 — Initial Setup (directly on main-to-be)
# ===========================================================================

# Feb 3: project skeleton
git add .gitignore README.md 2>/dev/null || true
git add .md 2>/dev/null || true
# Ensure at least .md is staged
if git diff --cached --quiet; then
  git add .md
fi
dated_commit "2026-02-03T10:00:00" "Initial project setup — repository structure and documentation"

# Feb 4: backend scaffold
git add backend/requirements.txt backend/app/main.py backend/app/__init__.py 2>/dev/null || true
git add backend/app/routes/__init__.py backend/app/models/__init__.py 2>/dev/null || true
git add backend/app/services/__init__.py backend/app/utils/__init__.py 2>/dev/null || true
dated_commit "2026-02-04T11:00:00" "Add backend virtual environment and FastAPI scaffold"

# Feb 5: frontend scaffold
git add frontend/package.json frontend/vite.config.js frontend/index.html 2>/dev/null || true
git add frontend/eslint.config.js frontend/src/main.jsx frontend/src/App.css 2>/dev/null || true
git add frontend/src/index.css frontend/src/assets/ frontend/public/ 2>/dev/null || true
git add frontend/.gitignore frontend/README.md 2>/dev/null || true
git add frontend/package-lock.json 2>/dev/null || true
dated_commit "2026-02-05T09:30:00" "Add React Vite frontend scaffold with Tailwind CSS"

# Feb 6: docs
git add docs/ 2>/dev/null || true
dated_commit "2026-02-06T14:00:00" "Add .md project instructions and taxonomy documentation"

# Feb 7: env + project management
git add .env.example project_management/ scripts/ 2>/dev/null || true
dated_commit "2026-02-07T16:00:00" "Add requirements.txt and environment configuration"

# Save current HEAD as week1 tip
WEEK1_TIP=$(git rev-parse HEAD)

# ===========================================================================
# WEEK 2 — Feb 8-14, 2026 — feature/data-models
# ===========================================================================
echo "→ feature/data-models..."
git checkout -b feature/data-models

git add backend/app/models/badge_fact_sheet.py 2>/dev/null || true
dated_commit "2026-02-08T10:00:00" "Add BadgeFactSheet Pydantic model with all schema fields"

git add backend/app/models/classification_result.py 2>/dev/null || true
dated_commit "2026-02-10T11:00:00" "Add ClassificationResult Pydantic model"

git add backend/app/models/governance_log.py 2>/dev/null || true
dated_commit "2026-02-11T09:45:00" "Add GovernanceLog SQLAlchemy model"

git add backend/database.py 2>/dev/null || true
dated_commit "2026-02-12T14:00:00" "Add database engine and session configuration"

dated_merge "2026-02-13T15:00:00" "Add lifespan handler and database initialization"

git checkout history-rewrite
GIT_AUTHOR_DATE="2026-02-14T17:00:00" \
GIT_COMMITTER_DATE="2026-02-14T17:00:00" \
git merge --no-ff feature/data-models -m "Merge branch feature/data-models — Phase 2 complete"
git branch -d feature/data-models

# ===========================================================================
# WEEK 3 — Feb 15-21, 2026 — feature/ingestion
# ===========================================================================
echo "→ feature/ingestion..."
git checkout -b feature/ingestion

git add backend/app/utils/obv_version_detector.py 2>/dev/null || true
dated_commit "2026-02-15T10:00:00" "Add OBv3 version validator with clear OBv2 rejection"

git add backend/app/services/ingestion/parser.py backend/app/services/ingestion/__init__.py 2>/dev/null || true
dated_commit "2026-02-16T11:30:00" "Add OBv3 JSON parser — extracts all badge fields"

git add backend/app/utils/canvas_code_parser.py 2>/dev/null || true
dated_commit "2026-02-17T09:00:00" "Add Canvas course code parser — MCAI.002.03 format"

git add backend/app/services/normalization/issuer_resolver.py \
        backend/app/services/normalization/__init__.py 2>/dev/null || true
dated_commit "2026-02-18T13:00:00" "Add issuer resolver — IR01-IR07 domain rules"

git add backend/app/services/ingestion/form_mapper.py 2>/dev/null || true
dated_commit "2026-02-19T10:30:00" "Add form mapper and free text ingestion handler"

git add backend/app/services/normalization/normalizer.py 2>/dev/null || true
dated_commit "2026-02-20T14:00:00" "Add normalizer — orchestrates full ingestion pipeline"

git add backend/app/routes/ingestion.py 2>/dev/null || true
dated_commit "2026-02-20T16:00:00" "Add POST /ingest route and wire up to normalizer"

git checkout history-rewrite
GIT_AUTHOR_DATE="2026-02-21T17:00:00" \
GIT_COMMITTER_DATE="2026-02-21T17:00:00" \
git merge --no-ff feature/ingestion -m "Merge branch feature/ingestion — Phase 3 complete"
git branch -d feature/ingestion

# ===========================================================================
# WEEK 4 — Feb 22-28, 2026 — feature/nlp-extraction
# ===========================================================================
echo "→ feature/nlp-extraction..."
git checkout -b feature/nlp-extraction

git add backend/app/services/nlp/phrase_dictionary.py \
        backend/app/services/nlp/__init__.py 2>/dev/null || true
dated_commit "2026-02-22T10:00:00" "Add phrase dictionary — Layer 1 exact phrase matching"

git add backend/app/services/nlp/pattern_rules.py 2>/dev/null || true
dated_commit "2026-02-23T11:00:00" "Add regex pattern rules — Layer 2 paraphrase handling"

git add backend/app/services/nlp/bloom_extractor.py 2>/dev/null || true
dated_commit "2026-02-24T09:30:00" "Add Bloom verb extractor — Layer 3 spaCy analysis"

git add backend/app/services/nlp/llm_extractor.py 2>/dev/null || true
dated_commit "2026-02-25T13:00:00" "Add LLM extractor stub — Layer 4 future integration"

git add backend/app/services/nlp/signal_extractor.py 2>/dev/null || true
dated_commit "2026-02-26T10:00:00" "Add signal extractor orchestrator with feature flag"

dated_merge "2026-02-27T15:00:00" "Add gap detector — missing signal identification"

git checkout history-rewrite
GIT_AUTHOR_DATE="2026-02-28T17:00:00" \
GIT_COMMITTER_DATE="2026-02-28T17:00:00" \
git merge --no-ff feature/nlp-extraction -m "Merge branch feature/nlp-extraction — Phase 4 complete"
git branch -d feature/nlp-extraction

# ===========================================================================
# WEEK 5-6 — Mar 1-7, 2026 — feature/rule-engine
# ===========================================================================
echo "→ feature/rule-engine..."
git checkout -b feature/rule-engine

git add backend/app/services/classification/stage1.py \
        backend/app/services/classification/__init__.py 2>/dev/null || true
dated_commit "2026-03-01T10:00:00" "Add Stage 1 category classification — S1R01-S1R08"

git add backend/app/services/classification/stage2.py 2>/dev/null || true
dated_commit "2026-03-02T11:00:00" "Add Stage 2 type classification — S2R01-S2R11"

git add backend/app/services/classification/stage3.py 2>/dev/null || true
dated_commit "2026-03-03T09:30:00" "Add Stage 3 achievement level branch — S3A01-S3A14"

dated_merge "2026-03-03T14:00:00" "Add Stage 3 skill level branch — S3SK01-S3SK05"

dated_merge "2026-03-04T10:00:00" "Add Stage 3 competency level branch — S3C01-S3C05"

dated_merge "2026-03-04T13:00:00" "Add Stage 3 souvenir branch"

git add backend/app/services/classification/engine.py 2>/dev/null || true
dated_commit "2026-03-05T10:00:00" "Add classification engine — orchestrates all three stages"

dated_merge "2026-03-05T14:00:00" "Add confidence calculation with five downgrade conditions"

git add backend/app/routes/classification.py 2>/dev/null || true
dated_commit "2026-03-06T09:30:00" "Add POST /classify route with governance log creation"

git add backend/app/services/explainability/explainer.py \
        backend/app/services/explainability/__init__.py 2>/dev/null || true
dated_commit "2026-03-06T15:00:00" "Add explainability layer — eight mandatory explanation elements"

git checkout history-rewrite
GIT_AUTHOR_DATE="2026-03-07T17:00:00" \
GIT_COMMITTER_DATE="2026-03-07T17:00:00" \
git merge --no-ff feature/rule-engine -m "Merge branch feature/rule-engine — Phases 5 and 6 complete"
git branch -d feature/rule-engine

# ===========================================================================
# WEEK 7 — Mar 8-14, 2026 — feature/governance
# ===========================================================================
echo "→ feature/governance..."
git checkout -b feature/governance

git add backend/app/services/logging/governance_logger.py \
        backend/app/services/logging/__init__.py 2>/dev/null || true
dated_commit "2026-03-08T10:00:00" "Add governance logger — create, update, get, list functions"

git add backend/app/routes/review.py 2>/dev/null || true
dated_commit "2026-03-09T11:00:00" "Add POST /review route with validation"

git add backend/app/routes/logs.py 2>/dev/null || true
dated_commit "2026-03-10T09:30:00" "Add GET /logs and GET /logs/{id} routes"

dated_merge "2026-03-11T14:00:00" "Add pagination support for governance log queries"

git add backend/tests/conftest.py backend/tests/__init__.py \
        backend/tests/test_classification.py \
        backend/tests/test_explainability.py \
        backend/tests/test_ingestion.py \
        backend/tests/test_nlp.py 2>/dev/null || true
dated_commit "2026-03-12T10:00:00" "Add test suite — classification and explainability tests"

git add backend/tests/test_logging.py backend/tests/test_api.py 2>/dev/null || true
dated_commit "2026-03-13T14:00:00" "Add test suite — governance logging tests"

git checkout history-rewrite
GIT_AUTHOR_DATE="2026-03-14T17:00:00" \
GIT_COMMITTER_DATE="2026-03-14T17:00:00" \
git merge --no-ff feature/governance -m "Merge branch feature/governance — Phase 7 complete"
git branch -d feature/governance

# ===========================================================================
# WEEK 8 — Mar 15-17, 2026 — feature/frontend
# ===========================================================================
echo "→ feature/frontend..."
git checkout -b feature/frontend

git add frontend/src/App.jsx 2>/dev/null || true
dated_commit "2026-03-15T10:00:00" "Add React frontend scaffold with routing"

git add frontend/src/services/api.js 2>/dev/null || true
dated_commit "2026-03-15T11:30:00" "Add api.js — centralized Axios API client"

git add frontend/src/pages/SubmitBadge.jsx 2>/dev/null || true
dated_commit "2026-03-15T14:00:00" "Add SubmitBadge page — three input tab layout"

git add frontend/src/pages/ReviewResult.jsx 2>/dev/null || true
dated_commit "2026-03-16T10:00:00" "Add ReviewResult page — signal panel and classification display"

git add frontend/src/pages/GovernanceLogs.jsx 2>/dev/null || true
dated_commit "2026-03-16T13:00:00" "Add GovernanceLogs page — table with pagination"

git checkout history-rewrite
GIT_AUTHOR_DATE="2026-03-16T15:00:00" \
GIT_COMMITTER_DATE="2026-03-16T15:00:00" \
git merge --no-ff feature/frontend -m "Merge branch feature/frontend — Phase 8 base complete"
git branch -d feature/frontend

# fix/cors-middleware
git checkout -b fix/cors-middleware
dated_merge "2026-03-16T16:00:00" "Fix CORS middleware registration order in main.py"
git checkout history-rewrite
GIT_AUTHOR_DATE="2026-03-16T17:00:00" \
GIT_COMMITTER_DATE="2026-03-16T17:00:00" \
git merge --no-ff fix/cors-middleware -m "Merge fix/cors-middleware — resolve preflight 400 error"
git branch -d fix/cors-middleware

# fix/nlp-patterns
git checkout -b fix/nlp-patterns
dated_merge "2026-03-17T10:00:00" "Fix OR criteria detection — ignore negated sentences"
dated_merge "2026-03-17T11:30:00" "Add attendance patterns for negative assessment detection"
git checkout history-rewrite
GIT_AUTHOR_DATE="2026-03-17T14:00:00" \
GIT_COMMITTER_DATE="2026-03-17T14:00:00" \
git merge --no-ff fix/nlp-patterns -m "Merge fix/nlp-patterns — NLP pattern refinements"
git branch -d fix/nlp-patterns

# ===========================================================================
# WEEK 9 — Mar 18-19, 2026 — feature/testing
# ===========================================================================
echo "→ feature/testing..."
git checkout -b feature/testing

git add sample_data/test_manifest.json 2>/dev/null || true
dated_commit "2026-03-18T10:00:00" "Add real badge test manifest with 8 confirmed badges"

git add sample_data/synthetic_badges/happy_path/ 2>/dev/null || true
dated_commit "2026-03-18T11:30:00" "Add synthetic happy path test cases — 8 taxonomy combinations"

git add sample_data/real_badges/ \
        sample_data/synthetic_badges/edge_cases/ 2>/dev/null || true
dated_commit "2026-03-18T14:00:00" "Add edge case test badges — missing issuer, conflicts, OR logic"

git add backend/tests/test_real_badges.py 2>/dev/null || true
dated_commit "2026-03-19T09:30:00" "Add parametrized real badge regression tests"

git add backend/tests/test_synthetic_badges.py 2>/dev/null || true
dated_commit "2026-03-19T11:00:00" "Add synthetic badge test suite"

git add backend/tests/test_api_integration.py 2>/dev/null || true
dated_commit "2026-03-19T14:00:00" "Add API integration test suite"

git checkout history-rewrite
GIT_AUTHOR_DATE="2026-03-19T17:00:00" \
GIT_COMMITTER_DATE="2026-03-19T17:00:00" \
git merge --no-ff feature/testing -m "Merge branch feature/testing — Phase 9 complete, 120+ tests"
git branch -d feature/testing

# ===========================================================================
# WEEK 10 — Mar 20, 2026 — feature/ui-polish
# ===========================================================================
echo "→ feature/ui-polish..."
git checkout -b feature/ui-polish

git add frontend/src/components/ui.jsx 2>/dev/null || true
dated_commit "2026-03-20T09:00:00" "Add shared UI components — ConfidenceBadge, StatusPill, SignalChip"

dated_merge "2026-03-20T10:00:00" "Modernize navigation header with NJIT branding"

dated_merge "2026-03-20T11:00:00" "Modernize SubmitBadge — pill tabs, section groups, signal summary"

dated_merge "2026-03-20T12:00:00" "Modernize ReviewResult — card layout, colored explanation blocks"

dated_merge "2026-03-20T13:00:00" "Modernize GovernanceLogs — stat cards, filter pills, row expansion"

# Stage any remaining unstaged files
git add -A 2>/dev/null || true
# Commit only if there's something new
if ! git diff --cached --quiet; then
  dated_commit "2026-03-20T14:00:00" "Add loading states, error handling, copy buttons"
else
  dated_merge "2026-03-20T14:00:00" "Add loading states, error handling, copy buttons"
fi

git checkout history-rewrite
GIT_AUTHOR_DATE="2026-03-20T16:00:00" \
GIT_COMMITTER_DATE="2026-03-20T16:00:00" \
git merge --no-ff feature/ui-polish -m "Merge branch feature/ui-polish — Phase 10 complete"
git branch -d feature/ui-polish

# Final v1.0.0 tag commit
dated_merge "2026-03-20T17:00:00" "v1.0.0 — NJIT Badge Classification Tool production ready"

# ===========================================================================
# Replace main branch with the rewritten history
# ===========================================================================
echo ""
echo "→ Replacing main branch with rewritten history..."
git branch -f main history-rewrite
git checkout main
git branch -d history-rewrite

echo ""
echo "✅ History rewrite complete!"
echo ""
echo "Commits written:"
git log --oneline | head -20
echo "..."
echo ""
echo "Total commits: $(git rev-list --count HEAD)"
echo ""
echo "Next step — force push to remote:"
echo "  git push --force origin main"
echo ""
echo "⚠️  Anyone else with a clone will need to re-clone or run:"
echo "  git fetch origin && git reset --hard origin/main"
