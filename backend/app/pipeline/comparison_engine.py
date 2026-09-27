"""
Result Comparison and Verification (SRS Table 1 style comparison).
Compares structured attributes/source references field-by-field between the
GenAI (Pipeline 1) output and the Python Requirement Matrix ground truth
(Pipeline 2), rather than comparing exact sentence wording.
"""
from typing import Dict, List


def _generated_by_requirement(plan: dict) -> Dict[str, dict]:
    result = {}
    for key in ("modules", "checklist", "tasks", "quizzes", "assessments"):
        for item in plan.get(key, []) or []:
            rid = item.get("requirement_id")
            if rid:
                result[rid] = item
    return result


def compare_plan_to_matrix(plan: dict, requirements: List[dict]) -> List[Dict]:
    """Builds the requirement-level comparison table (mirrors SRS Table 1)."""
    generated_by_req = _generated_by_requirement(plan)
    rows = []
    for req in requirements:
        rid = req["requirement_id"]
        gen_item = generated_by_req.get(rid)

        def field_row(field_label, expected, actual):
            match = "Match" if str(expected) == str(actual) else "Mismatch"
            return {"field": field_label, "genai_output": actual, "python_ground_truth": expected, "result": match}

        if gen_item is None:
            rows.append({
                "requirement_id": rid,
                "role": req["role_name"],
                "validation_status": "Requirement Missing",
                "fields": [
                    {"field": "Requirement ID", "genai_output": None, "python_ground_truth": rid, "result": "Mismatch"},
                ],
            })
            continue

        fields = [
            field_row("Requirement ID", rid, gen_item.get("requirement_id")),
            field_row("Role", req["role_name"], plan.get("role")),
            field_row("Source Document", req["source_document_id"], gen_item.get("source_document_id")),
            field_row("Source Section", req["source_section_id"], gen_item.get("source_section_id")),
            field_row("Mandatory", req["mandatory"], gen_item.get("mandatory", True)),
            field_row("Priority", req["priority"], gen_item.get("priority", req["priority"])),
            field_row("Due Stage", req["due_stage"], gen_item.get("due_stage")),
        ]
        mismatches = [f for f in fields if f["result"] == "Mismatch"]
        status = "Verified" if not mismatches else "Verified with Warning"
        rows.append({
            "requirement_id": rid,
            "role": req["role_name"],
            "validation_status": status,
            "fields": fields,
        })
    return rows


def summarize_comparison(rows: List[Dict]) -> Dict:
    total = len(rows)
    verified = sum(1 for r in rows if r["validation_status"] == "Verified")
    warning = sum(1 for r in rows if r["validation_status"] == "Verified with Warning")
    missing = sum(1 for r in rows if r["validation_status"] == "Requirement Missing")
    return {
        "total_requirements": total,
        "verified": verified,
        "verified_with_warning": warning,
        "requirement_missing": missing,
        "match_rate_percent": round((verified / total) * 100, 2) if total else 100.0,
    }
