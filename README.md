
# NJIT AI-Assisted Digital Badge Classification Tool

New Jersey Institute of Technology
Capstone Project - Spring 2026

---

## About This Project

This tool automatically classifies digital badges issued at NJIT using a multi-layer
NLP pipeline combined with a rule engine. It accepts badge input in three formats -
a proposal form, an OBv3 JSON file, or plain free text - and returns a classification
with category, type, level, confidence score, and a human-readable explanation.

The backend is built with FastAPI and Python. The frontend is built with React.

---

## Branch: nlp-improvements

This branch adds student-friendly natural language support to the NLP extraction layer.
The goal was to make the system understand how students and instructors actually describe
badges in plain English, not just formal academic language.

All changes on this branch are additive. Nothing from the original codebase was removed
or modified in a breaking way.

---

## What Was Done

### 1. Expanded the Phrase Dictionary

File: backend/app/services/nlp/phrase_dictionary.py

Added student-friendly phrases for badge level detection. These are words and expressions
that students commonly use when describing a badge or course.

Examples of phrases added:

For Foundational level:
- "complete beginners"
- "no experience necessary"
- "learn from scratch"
- "just starting out"
- "first-time learners"
- "zero experience"
- "beginners welcome"

For Milestone level:
- "builds on"
- "level up"
- "prior experience required"
- "next step after"
- "already familiar with"
- "prerequisite course"
- "some background needed"

For Terminal level:
- "capstone project"
- "culminating experience"
- "putting it all together"
- "final stage of the program"
- "integrating all skills"

Additional phrases were also added for audience types (graduate students,
undergraduate students) and badge purpose (prerequisite gate, compliance).


### 2. Expanded the Regex Pattern Rules

File: backend/app/services/nlp/pattern_rules.py

Added regex patterns that match the same student language in a more flexible way,
so the system can catch variations even when the exact phrase is not present.

Examples of patterns added:
- Matches phrases like "just starting" or "brand new to this"
- Matches "no experience needed" or "no prior experience required"
- Matches "next step after completing" or "take the next step"
- Matches "builds on the previous" or "expands on prior work"
- Matches "capstone", "culminating project", or "final project in the series"
- Matches "just show up", "physical presence required" for attendance detection
- Matches "client project", "community service", "case study" for real-world context


### 3. New Test File - NLP Unit Tests

File: backend/tests/test_nlp_student_language.py

This file contains 44 unit tests organized into 7 test classes. It tests:
- That all new student phrases are present in the dictionary
- That the extractor correctly picks up the level from student language descriptions
- That regex patterns match the expected text inputs
- That Rajat's original phrases still work correctly (regression tests)

Test classes in this file:
- TestStudentLevelPhrases
- TestStudentAssessmentPhrases
- TestStudentAudiencePhrases
- TestStudentPurposePhrases
- TestStudentLevelPatterns
- TestStudentAssessmentPatterns
- TestStudentRealWorldPatterns
- TestFreeTextStudentDescriptions
- TestOriginalPhraseRegression


### 4. New Test File - End-to-End Validation Tests

File: backend/tests/test_nlp_end_to_end_validation.py

This file contains 17 tests that cover 10 real test cases. Each test runs the
full pipeline from start to finish: input is normalized, NLP signals are extracted,
and the badge is classified. The tests cover all three input types.

Test cases included:
- 4 proposal form inputs using real badge files from sample_data/real_badges/
- 3 OBv3 JSON inputs using synthetic badge descriptions
- 3 free text inputs using plain natural language descriptions

Test classes in this file:
- Test01_FormFoundational
- Test02_FormTerminal
- Test03_FormSouvenirAttendance
- Test04_FormSkillExpertScored
- Test05_OBv3Foundational
- Test06_OBv3Milestone
- Test07_OBv3Terminal
- Test08_FreeTextFoundational
- Test09_FreeTextMilestone
- Test10_FreeTextCompliance
- Test00_ValidationReport (meta checks)


### 5. Validation Report

File: VALIDATION_REPORT.md (at repo root)

A plain text report documenting all 10 test cases, what NLP signals were detected
in each case, what the classification output was, and the overall test results.

---

## New Files Added

```
VALIDATION_REPORT.md
backend/tests/test_nlp_student_language.py
backend/tests/test_nlp_end_to_end_validation.py
```

## Files Modified

```
backend/app/services/nlp/phrase_dictionary.py
backend/app/services/nlp/pattern_rules.py
```

---

## Project Structure

```
ai-badge-classification-platform/
|
|-- VALIDATION_REPORT.md
|-- README.md
|
|-- backend/
|   |-- app/
|   |   |-- models/
|   |   |   |-- badge_fact_sheet.py
|   |   |   |-- classification_result.py
|   |   |   |-- governance_log.py
|   |   |
|   |   |-- routes/
|   |   |   |-- ingestion.py
|   |   |   |-- classification.py
|   |   |   |-- review.py
|   |   |   |-- reviewer.py
|   |   |   |-- logs.py
|   |   |
|   |   |-- services/
|   |   |   |-- nlp/
|   |   |   |   |-- phrase_dictionary.py   (modified)
|   |   |   |   |-- pattern_rules.py       (modified)
|   |   |   |   |-- signal_extractor.py
|   |   |   |   |-- bloom_extractor.py
|   |   |   |   |-- llm_extractor.py
|   |   |   |
|   |   |   |-- classification/
|   |   |   |   |-- engine.py
|   |   |   |   |-- stage1.py
|   |   |   |   |-- stage2.py
|   |   |   |   |-- stage3.py
|   |   |   |
|   |   |   |-- ingestion/
|   |   |   |   |-- parser.py
|   |   |   |   |-- form_mapper.py
|   |   |   |
|   |   |   |-- normalization/
|   |   |   |   |-- normalizer.py
|   |   |   |   |-- issuer_resolver.py
|   |   |   |
|   |   |   |-- explainability/
|   |   |   |   |-- explainer.py
|   |   |   |
|   |   |   |-- logging/
|   |   |       |-- governance_logger.py
|   |   |
|   |   |-- utils/
|   |       |-- canvas_code_parser.py
|   |       |-- obv_version_detector.py
|   |
|   |-- tests/
|       |-- conftest.py
|       |-- test_nlp_student_language.py   (new)
|       |-- test_nlp_end_to_end_validation.py  (new)
|       |-- test_api.py
|       |-- test_api_integration.py
|       |-- test_classification.py
|       |-- test_edge_cases.py
|       |-- test_explainability.py
|       |-- test_ingestion.py
|       |-- test_logging.py
|       |-- test_nlp.py
|       |-- test_real_badges.py
|       |-- test_synthetic_badges.py
|       |-- test_verification_checklist.py
|
|-- frontend/
|   |-- src/
|       |-- components/
|       |-- pages/
|       |-- services/
|
|-- sample_data/
    |-- real_badges/
    |-- synthetic_badges/
    |-- test_manifest.json
```

---

## How to Run the Tests

```bash
cd backend
python -m pytest tests/ -q
```

---

## Authors

Original system design and backend: Rajat (NJIT)
NLP improvements on this branch: Prabhath Vinay (NJIT)
