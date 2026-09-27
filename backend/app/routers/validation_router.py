from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime

from ..database import (
    validation_results_col, comparison_results_col, onboarding_plans_col,
    audit_log_col, adversarial_flags_col,
)
from ..auth import require_roles
from ..models.schemas import ReviewerDecision

router = APIRouter(prefix="/validation", tags=["validation"])


@router.get("/results/{employee_id}")
async def get_validation(employee_id: str, user=Depends(require_roles(
        "admin", "training_manager", "reviewer", "manager"))):
    result = await validation_results_col.find_one(
        {"employee_id": employee_id}, {"_id": 0}, sort=[("validated_at", -1)]
    )
    if not result:
        raise HTTPException(status_code=404, detail="No validation results found")
    return result


@router.get("/comparison/{employee_id}")
async def get_comparison(employee_id: str, user=Depends(require_roles(
        "admin", "training_manager", "reviewer", "manager"))):
    result = await comparison_results_col.find_one(
        {"employee_id": employee_id}, {"_id": 0}, sort=[("created_at", -1)]
    )
    if not result:
        raise HTTPException(status_code=404, detail="No comparison results found")
    return result


@router.get("/manual-review-queue")
async def manual_review_queue(user=Depends(require_roles("admin", "training_manager", "reviewer"))):
    """Returns all plans whose Pipeline-2 validation did not come back fully 'Verified'."""
    flagged_statuses = [
        "Partially Verified", "Source Support Missing", "Requirement Missing",
        "Unsupported Requirement", "Outdated Source", "Contradiction Detected",
        "Manual Review Required", "Verified with Warning",
    ]
    results = await validation_results_col.find(
        {"final_status": {"$in": flagged_statuses}}, {"_id": 0}
    ).to_list(length=1000)
    return results


@router.post("/reviewer-decision")
async def reviewer_decision(payload: ReviewerDecision,
                             user=Depends(require_roles("admin", "training_manager", "reviewer"))):
    """Step 48/49 - Human review workflow with reviewer override + audit trail."""
    record = {
        "item_id": payload.item_id,
        "decision": payload.decision,
        "comment": payload.comment,
        "edited_content": payload.edited_content,
        "reviewer": payload.reviewer,
        "decided_by_user": user["username"],
        "decided_at": datetime.utcnow().isoformat(),
    }
    await audit_log_col.insert_one({
        "action": "reviewer_decision", **record,
    })
    return {"message": "Reviewer decision recorded", "record": record}


@router.get("/audit-trail")
async def audit_trail(employee_id: str = None,
                       user=Depends(require_roles("admin", "training_manager", "reviewer"))):
    query = {"employee_id": employee_id} if employee_id else {}
    logs = await audit_log_col.find(query, {"_id": 0}).sort("timestamp", -1).to_list(length=2000)
    return logs


@router.get("/adversarial-flags")
async def adversarial_flags(user=Depends(require_roles("admin", "training_manager", "reviewer"))):
    flags = await adversarial_flags_col.find({}, {"_id": 0}).to_list(length=1000)
    return flags
