"""
Unit tests for Pipeline 2 (pure Python, deterministic - no GenAI, no DB).
Run with: pytest tests/test_python_validation.py
"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.pipeline.python_validation import (
    calculate_coverage, calculate_traceability, detect_hallucinations,
    detect_duplicates, schema_validate, overall_verification_status,
)

REQUIREMENTS = [
    {"requirement_id": "R001", "role_name": "Customer Support Executive", "mandatory": True,
     "source_document_id": "SOP-07", "source_section_id": "4.2", "priority": "High", "due_stage": "Week 1"},
    {"requirement_id": "R002", "role_name": "Customer Support Executive", "mandatory": True,
     "source_document_id": "HR-01", "source_section_id": "2.1", "priority": "Medium", "due_stage": "Day 1"},
]

CHUNKS = [
    {"document_id": "SOP-07", "section_id": "4.2-1", "text": "Escalation process details"},
    {"document_id": "HR-01", "section_id": "2.1-1", "text": "Leave policy details"},
]

GOOD_PLAN = {
    "role": "Customer Support Executive",
    "employee_id": "EMP-test001",
    "modules": [
        {"module_id": "M01", "module_title": "Escalation Process", "mandatory": True,
         "source_document_id": "SOP-07", "source_section_id": "4.2", "requirement_id": "R001",
         "due_stage": "Week 1"},
        {"module_id": "M02", "module_title": "Leave Policy", "mandatory": True,
         "source_document_id": "HR-01", "source_section_id": "2.1", "requirement_id": "R002",
         "due_stage": "Day 1"},
    ],
    "checklist": [], "tasks": [], "quizzes": [], "assessments": [],
    "insufficient_information": [],
}

BAD_PLAN = {
    "role": "Customer Support Executive",
    "employee_id": "EMP-test001",
    "modules": [
        {"module_id": "M01", "module_title": "Escalation Process", "mandatory": True,
         "source_document_id": "SOP-07", "source_section_id": "4.2", "requirement_id": "R001",
         "due_stage": "Week 1"},
        {"module_id": "M02", "module_title": "Made Up Policy", "mandatory": True,
         "source_document_id": "FAKE-99", "source_section_id": "9.9", "requirement_id": "R999",
         "due_stage": "Day 1"},
    ],
    "checklist": [], "tasks": [], "quizzes": [], "assessments": [],
    "insufficient_information": [],
}


def test_coverage_full():
    result = calculate_coverage(GOOD_PLAN, REQUIREMENTS)
    assert result["coverage_score"] == 100.0
    assert result["missing_requirements"] == []


def test_coverage_missing():
    result = calculate_coverage(BAD_PLAN, REQUIREMENTS)
    assert result["coverage_score"] == 50.0
    assert len(result["missing_requirements"]) == 1


def test_traceability_full():
    result = calculate_traceability(GOOD_PLAN, CHUNKS)
    assert result["traceability_score"] == 100.0


def test_traceability_partial():
    result = calculate_traceability(BAD_PLAN, CHUNKS)
    assert result["traceability_score"] == 50.0
    assert len(result["unsupported_items"]) == 1


def test_hallucination_detection():
    flags = detect_hallucinations(BAD_PLAN, CHUNKS, REQUIREMENTS)
    assert len(flags) >= 1
    assert any("FAKE" in str(f) or "R999" in str(f) for f in [f["reasons"] for f in flags])


def test_no_hallucination_on_good_plan():
    flags = detect_hallucinations(GOOD_PLAN, CHUNKS, REQUIREMENTS)
    assert flags == []


def test_schema_validation_passes():
    errors = schema_validate(GOOD_PLAN)
    assert errors == []


def test_schema_validation_missing_field():
    broken_plan = {k: v for k, v in GOOD_PLAN.items() if k != "checklist"}
    errors = schema_validate(broken_plan)
    assert any("checklist" in e for e in errors)


def test_final_status_verified():
    coverage = calculate_coverage(GOOD_PLAN, REQUIREMENTS)
    traceability = calculate_traceability(GOOD_PLAN, CHUNKS)
    hallucinations = detect_hallucinations(GOOD_PLAN, CHUNKS, REQUIREMENTS)
    status = overall_verification_status(coverage, traceability, hallucinations, [], [])
    assert status == "Verified"


def test_final_status_requirement_missing():
    coverage = calculate_coverage(BAD_PLAN, REQUIREMENTS)
    traceability = calculate_traceability(BAD_PLAN, CHUNKS)
    hallucinations = detect_hallucinations(BAD_PLAN, CHUNKS, REQUIREMENTS)
    status = overall_verification_status(coverage, traceability, hallucinations, [], [])
    assert status in ("Requirement Missing", "Partially Verified")
