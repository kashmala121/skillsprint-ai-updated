"""
Pipeline 2 - Python Ground-Truth Validation Pipeline.
Independent of any GenAI API. Compares the structured GenAI output against
the Role Requirement Matrix, source chunks and business rules to compute:
coverage score, traceability score, missing/unsupported/duplicate requirements,
contradictions, role relevance, and a final verification status per item and
for the plan overall.

This module NEVER trusts the GenAI output blindly (SRS: "must not automatically
accept the GenAI output").
"""
from datetime import datetime
from difflib import SequenceMatcher
from typing import Dict, List, Set

from ..config import settings

DUPLICATE_SIMILARITY_THRESHOLD = 0.85
STAGE_ORDER = ["Day 1", "Week 1", "Week 2", "First 30 Days", "First 60 Days", "First 90 Days"]


def _text_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def _valid_source(item: dict, chunk_index: Dict[str, dict]) -> bool:
    doc_id = item.get("source_document_id")
    sec_id = item.get("source_section_id")
    if not doc_id or not sec_id:
        return False
    # A chunk key is "doc_id::section_id"; also allow doc-level match
    for key, chunk in chunk_index.items():
        if chunk["document_id"] == doc_id:
            return True
    return False


def build_chunk_index(chunks: List[dict]) -> Dict[str, dict]:
    return {f"{c['document_id']}::{c['section_id']}": c for c in chunks}


def _all_generated_items(plan: dict) -> List[dict]:
    items = []
    for key in ("modules", "checklist", "tasks", "quizzes", "assessments"):
        for item in plan.get(key, []) or []:
            item = dict(item)
            item["_category"] = key
            items.append(item)
    return items


def calculate_coverage(plan: dict, requirements: List[dict]) -> Dict:
    """Step 29 - Mandatory Requirement Coverage Score."""
    mandatory_reqs = [r for r in requirements if r.get("mandatory")]
    covered_ids: Set[str] = set()
    generated_req_ids = {
        item.get("requirement_id") for item in _all_generated_items(plan) if item.get("requirement_id")
    }
    for r in mandatory_reqs:
        if r["requirement_id"] in generated_req_ids:
            covered_ids.add(r["requirement_id"])

    missing = [r for r in mandatory_reqs if r["requirement_id"] not in covered_ids]
    total = len(mandatory_reqs)
    coverage_score = round((len(covered_ids) / total) * 100, 2) if total else 100.0
    return {
        "coverage_score": coverage_score,
        "total_mandatory": total,
        "covered_count": len(covered_ids),
        "missing_requirements": missing,
    }


def calculate_traceability(plan: dict, chunks: List[dict]) -> Dict:
    """Step 30 - Source Traceability Score."""
    chunk_index = build_chunk_index(chunks)
    items = _all_generated_items(plan)
    mandatory_items = [i for i in items if i.get("mandatory", True)]
    traced = [i for i in mandatory_items if _valid_source(i, chunk_index)]
    total = len(mandatory_items)
    score = round((len(traced) / total) * 100, 2) if total else 100.0
    unsupported = [i for i in mandatory_items if not _valid_source(i, chunk_index)]
    return {
        "traceability_score": score,
        "total_mandatory_items": total,
        "traced_count": len(traced),
        "unsupported_items": unsupported,
    }


def detect_hallucinations(plan: dict, chunks: List[dict], requirements: List[dict]) -> List[dict]:
    """Step 31/32 - Hallucination / Unsupported Content Detection.
    Flags any generated item that (a) has no valid source reference, OR
    (b) cites a requirement_id that does not exist in the Role Requirement Matrix."""
    chunk_index = build_chunk_index(chunks)
    valid_requirement_ids = {r["requirement_id"] for r in requirements}
    flags = []
    for item in _all_generated_items(plan):
        reasons = []
        if not _valid_source(item, chunk_index):
            reasons.append("No matching source document/section found in approved chunks")
        req_id = item.get("requirement_id")
        if req_id and req_id not in valid_requirement_ids:
            reasons.append(f"requirement_id '{req_id}' not present in Role Requirement Matrix")
        if reasons:
            flags.append({
                "category": item["_category"],
                "item_id": item.get("module_id") or item.get("item_id") or item.get("task_id")
                or item.get("question_id") or item.get("assessment_id"),
                "reasons": reasons,
            })
    for info in plan.get("insufficient_information", []) or []:
        flags.append({"category": "self_reported", "item_id": None,
                       "reasons": [f"GenAI reported insufficient source information: {info}"]})
    return flags


def detect_duplicates(plan: dict) -> List[dict]:
    """Step 35 - Duplicate Learning Detection using text similarity."""
    duplicates = []
    for category in ("modules", "checklist", "tasks", "quizzes"):
        entries = plan.get(category, []) or []
        text_field = {
            "modules": "module_title", "checklist": "activity",
            "tasks": "description", "quizzes": "question",
        }[category]
        for i in range(len(entries)):
            for j in range(i + 1, len(entries)):
                t1, t2 = entries[i].get(text_field, ""), entries[j].get(text_field, "")
                if t1 and t2 and _text_similarity(t1, t2) >= DUPLICATE_SIMILARITY_THRESHOLD:
                    duplicates.append({
                        "category": category,
                        "item_a": entries[i].get(text_field),
                        "item_b": entries[j].get(text_field),
                        "similarity": round(_text_similarity(t1, t2), 2),
                    })
    return duplicates


def detect_contradictions(chunks: List[dict], documents: List[dict]) -> List[dict]:
    """
    Step 33/34 - Contradiction Detection + Policy Precedence.
    Compares chunks that reference overlapping keywords but come from documents
    with different precedence categories or versions, and flags them for
    precedence resolution. This is a heuristic, deterministic (non-GenAI) check.
    """
    precedence_rank = {cat: i for i, cat in enumerate(settings.POLICY_PRECEDENCE)}
    doc_by_id = {d["document_id"]: d for d in documents}
    contradictions = []

    # Group chunks by heading keyword to find topically overlapping content
    from collections import defaultdict
    topic_groups = defaultdict(list)
    for c in chunks:
        key_terms = tuple(sorted(set(w.lower() for w in c["heading"].split() if len(w) > 4)))
        if key_terms:
            topic_groups[key_terms].append(c)

    for terms, group in topic_groups.items():
        doc_ids = {c["document_id"] for c in group}
        if len(doc_ids) < 2:
            continue
        docs_in_group = [doc_by_id.get(d) for d in doc_ids if doc_by_id.get(d)]
        if len(docs_in_group) < 2:
            continue
        precedences = {d["precedence_category"] for d in docs_in_group}
        versions = {(d["document_id"], d.get("version")) for d in docs_in_group}
        if len(precedences) > 1 or len(versions) > len(doc_ids):
            winning_doc = min(docs_in_group, key=lambda d: precedence_rank.get(d["precedence_category"], 99))
            contradictions.append({
                "topic": " ".join(terms),
                "conflicting_documents": [d["document_id"] for d in docs_in_group],
                "resolved_by_precedence": winning_doc["document_id"],
                "rule_applied": f"Precedence order: {settings.POLICY_PRECEDENCE}",
            })
    return contradictions


def validate_sequence(plan: dict, prerequisite_map: Dict[str, List[str]]) -> List[dict]:
    """Step 26/27 - Prerequisite / Learning Sequence Validation.
    prerequisite_map: {requirement_id: [required_requirement_ids...]} """
    issues = []
    items = _all_generated_items(plan)
    stage_of = {i.get("requirement_id"): i.get("due_stage") for i in items if i.get("requirement_id")}
    for req_id, prereqs in prerequisite_map.items():
        if req_id not in stage_of:
            continue
        for p in prereqs:
            if p not in stage_of:
                issues.append({"requirement_id": req_id, "issue": f"Missing prerequisite {p} in generated plan"})
                continue
            try:
                if STAGE_ORDER.index(stage_of[p]) > STAGE_ORDER.index(stage_of[req_id]):
                    issues.append({
                        "requirement_id": req_id,
                        "issue": f"Prerequisite {p} scheduled after dependent item (sequence violation)",
                    })
            except ValueError:
                continue
    return issues


def role_relevance_check(plan: dict, role_name: str, requirements: List[dict]) -> List[dict]:
    """Step 36 - Role Relevance Validation: flags items whose requirement_id
    belongs to a different role than the one being onboarded."""
    req_role = {r["requirement_id"]: r["role_name"] for r in requirements}
    flags = []
    for item in _all_generated_items(plan):
        rid = item.get("requirement_id")
        if rid and rid in req_role and req_role[rid] != role_name:
            flags.append({
                "item": item.get("module_id") or item.get("item_id") or item.get("task_id"),
                "issue": f"requirement_id {rid} belongs to role '{req_role[rid]}', not '{role_name}'",
            })
    return flags


def schema_validate(plan: dict) -> List[str]:
    """Step 38 - JSON Schema Validation. Returns list of schema errors."""
    errors = []
    required_top = ["role", "employee_id", "modules", "checklist", "tasks", "quizzes", "assessments"]
    for field in required_top:
        if field not in plan:
            errors.append(f"Missing top-level field: {field}")

    seen_ids = set()
    for item in _all_generated_items(plan):
        item_id = item.get("module_id") or item.get("item_id") or item.get("task_id") \
            or item.get("question_id") or item.get("assessment_id")
        if not item_id:
            errors.append(f"{item['_category']} item missing an ID field")
        elif item_id in seen_ids:
            errors.append(f"Duplicate ID detected: {item_id}")
        else:
            seen_ids.add(item_id)
        if "requirement_id" not in item:
            errors.append(f"{item['_category']} item {item_id} missing requirement_id")
    return errors


def overall_verification_status(coverage: dict, traceability: dict, hallucinations: list,
                                 contradictions: list, schema_errors: list) -> str:
    """Step 47 - Final Verification Status."""
    if schema_errors:
        return "Manual Review Required"
    if coverage["coverage_score"] < 100 and coverage["missing_requirements"]:
        return "Requirement Missing" if coverage["coverage_score"] < 50 else "Partially Verified"
    if hallucinations:
        return "Unsupported Requirement"
    if contradictions:
        return "Contradiction Detected"
    if traceability["traceability_score"] < 100:
        return "Verified with Warning"
    return "Verified"


def run_full_validation(plan: dict, requirements: List[dict], chunks: List[dict],
                         documents: List[dict], role_name: str,
                         prerequisite_map: Dict[str, List[str]] = None) -> Dict:
    """Runs the complete Pipeline 2 ground-truth validation and returns a
    consolidated report used by the comparison engine and dashboards."""
    prerequisite_map = prerequisite_map or {}
    coverage = calculate_coverage(plan, requirements)
    traceability = calculate_traceability(plan, chunks)
    hallucinations = detect_hallucinations(plan, chunks, requirements)
    duplicates = detect_duplicates(plan)
    contradictions = detect_contradictions(chunks, documents)
    sequence_issues = validate_sequence(plan, prerequisite_map)
    relevance_issues = role_relevance_check(plan, role_name, requirements)
    schema_errors = schema_validate(plan)

    status = overall_verification_status(coverage, traceability, hallucinations, contradictions, schema_errors)

    return {
        "validated_at": datetime.utcnow().isoformat(),
        "coverage": coverage,
        "traceability": traceability,
        "hallucinations": hallucinations,
        "duplicates": duplicates,
        "contradictions": contradictions,
        "sequence_issues": sequence_issues,
        "role_relevance_issues": relevance_issues,
        "schema_errors": schema_errors,
        "consistency_count": {
            "missing_requirement_count": len(coverage["missing_requirements"]),
            "unsupported_requirement_count": len(hallucinations),
            "contradiction_count": len(contradictions),
        },
        "final_status": status,
    }


def consistency_score(run_a_plan: dict, run_b_plan: dict) -> Dict:
    """Step 44/45 - Generation Consistency Score between two controlled runs,
    comparing structured business fields (requirement coverage), not exact wording."""
    ids_a = {i.get("requirement_id") for i in _all_generated_items(run_a_plan) if i.get("requirement_id")}
    ids_b = {i.get("requirement_id") for i in _all_generated_items(run_b_plan) if i.get("requirement_id")}
    if not ids_a and not ids_b:
        return {"consistency_score": 100.0, "matched": 0, "only_in_a": [], "only_in_b": []}
    intersection = ids_a & ids_b
    union = ids_a | ids_b
    score = round((len(intersection) / len(union)) * 100, 2) if union else 100.0
    return {
        "consistency_score": score,
        "matched": len(intersection),
        "only_in_a": list(ids_a - ids_b),
        "only_in_b": list(ids_b - ids_a),
    }
