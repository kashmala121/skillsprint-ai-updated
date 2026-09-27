from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime

from ..database import (
    employees_col, requirement_matrix_col, chunks_col, documents_col,
    onboarding_plans_col, validation_results_col, comparison_results_col,
    audit_log_col, progress_col,
)
from ..auth import require_roles
from ..models.schemas import OnboardingGenerateRequest, new_id
from ..pipeline.genai_pipeline import generate_onboarding_plan, generate_twice_for_consistency
from ..pipeline.python_validation import run_full_validation, consistency_score
from ..pipeline.comparison_engine import compare_plan_to_matrix, summarize_comparison

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


async def _gather_context(employee: dict):
    role_reqs = await requirement_matrix_col.find(
        {"role_name": employee["role_name"]}, {"_id": 0}
    ).to_list(length=1000)
    if not role_reqs:
        raise HTTPException(
            status_code=400,
            detail=f"No Role Requirement Matrix entries found for role '{employee['role_name']}'. "
                   f"Add requirements first via /roles/matrix.",
        )
    doc_ids = {r["source_document_id"] for r in role_reqs}
    chunks = await chunks_col.find({"document_id": {"$in": list(doc_ids)}}, {"_id": 0}).to_list(length=5000)
    documents = await documents_col.find({"document_id": {"$in": list(doc_ids)}}, {"_id": 0}).to_list(length=1000)
    return role_reqs, chunks, documents


@router.post("/generate")
async def generate_plan(payload: OnboardingGenerateRequest,
                         user=Depends(require_roles("admin", "training_manager"))):
    employee = await employees_col.find_one({"employee_id": payload.employee_id}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    role_reqs, chunks, documents = await _gather_context(employee)
    if not chunks:
        raise HTTPException(status_code=400, detail="No source document chunks available for this role's documents.")

    # ---- Pipeline 1: GenAI generation ----
    gen_result = generate_onboarding_plan(employee, role_reqs, chunks)
    if gen_result["status"] != "success":
        await audit_log_col.insert_one({
            "action": "onboarding_generation_failed", "employee_id": employee["employee_id"],
            "error": gen_result.get("error"), "timestamp": datetime.utcnow().isoformat(),
        })
        raise HTTPException(status_code=502, detail=f"GenAI generation failed after retries: {gen_result.get('error')}")

    plan = gen_result["plan"]
    plan_id = new_id("PLAN")

    # ---- Pipeline 2: independent Python ground-truth validation ----
    validation = run_full_validation(plan, role_reqs, chunks, documents, employee["role_name"])

    # ---- Result comparison ----
    comparison_rows = compare_plan_to_matrix(plan, role_reqs)
    comparison_summary = summarize_comparison(comparison_rows)

    plan_record = {
        "plan_id": plan_id,
        "employee_id": employee["employee_id"],
        "role_name": employee["role_name"],
        "plan": plan,
        "prompt_version": gen_result["prompt_version"],
        "model": gen_result["model"],
        "generated_at": gen_result["generated_at"],
        "generation_attempts": gen_result["attempts"],
        "final_status": validation["final_status"],
    }
    await onboarding_plans_col.insert_one(dict(plan_record))

    validation_record = dict(validation)
    validation_record["plan_id"] = plan_id
    validation_record["employee_id"] = employee["employee_id"]
    await validation_results_col.insert_one(validation_record)

    comparison_record = {
        "plan_id": plan_id,
        "employee_id": employee["employee_id"],
        "rows": comparison_rows,
        "summary": comparison_summary,
        "created_at": datetime.utcnow().isoformat(),
    }
    await comparison_results_col.insert_one(dict(comparison_record))

    await progress_col.update_one(
        {"employee_id": employee["employee_id"]},
        {"$set": {
            "employee_id": employee["employee_id"], "plan_id": plan_id,
            "overall_status": "On Track" if validation["final_status"] == "Verified" else "Assessment Required",
            "module_completion": {}, "checklist_completion": {}, "task_completion": {},
            "quiz_scores": {}, "assessment_scores": {}, "updated_at": datetime.utcnow().isoformat(),
        }},
        upsert=True,
    )

    await employees_col.update_one(
        {"employee_id": employee["employee_id"]}, {"$set": {"training_status": "Assigned"}}
    )

    await audit_log_col.insert_one({
        "action": "onboarding_generated", "employee_id": employee["employee_id"], "plan_id": plan_id,
        "final_status": validation["final_status"], "user": user["username"],
        "timestamp": datetime.utcnow().isoformat(),
    })

    plan_record.pop("_id", None)
    return {
        "plan": plan_record,
        "validation": validation,
        "comparison": {"summary": comparison_summary, "rows": comparison_rows},
    }


@router.post("/consistency-check")
async def consistency_check(payload: OnboardingGenerateRequest,
                             user=Depends(require_roles("admin", "training_manager"))):
    """Step 44/45 - runs GenAI generation twice and reports the consistency score."""
    employee = await employees_col.find_one({"employee_id": payload.employee_id}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    role_reqs, chunks, _ = await _gather_context(employee)
    runs = generate_twice_for_consistency(employee, role_reqs, chunks)
    if runs["run_a"]["status"] != "success" or runs["run_b"]["status"] != "success":
        raise HTTPException(status_code=502, detail="One or both consistency-check generations failed.")
    score = consistency_score(runs["run_a"]["plan"], runs["run_b"]["plan"])
    return {"consistency": score, "run_a_meta": {k: v for k, v in runs["run_a"].items() if k != "plan"},
            "run_b_meta": {k: v for k, v in runs["run_b"].items() if k != "plan"}}


@router.get("/plan/{employee_id}")
async def get_plan(employee_id: str, user=Depends(require_roles(
        "admin", "training_manager", "reviewer", "manager", "employee"))):
    plan = await onboarding_plans_col.find_one(
        {"employee_id": employee_id}, {"_id": 0}, sort=[("generated_at", -1)]
    )
    if not plan:
        raise HTTPException(status_code=404, detail="No onboarding plan generated yet for this employee")
    return plan


@router.get("/plans")
async def list_plans(user=Depends(require_roles("admin", "training_manager", "reviewer"))):
    plans = await onboarding_plans_col.find({}, {"_id": 0}).to_list(length=2000)
    return plans
