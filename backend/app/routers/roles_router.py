from fastapi import APIRouter, Depends, HTTPException
from typing import List

from ..database import roles_col, requirement_matrix_col
from ..auth import require_roles
from ..models.schemas import RoleCreate, RequirementMatrixEntry, new_id

router = APIRouter(prefix="/roles", tags=["roles"])


@router.post("/")
async def create_role(payload: RoleCreate, user=Depends(require_roles("admin", "training_manager"))):
    existing = await roles_col.find_one({"role_name": payload.role_name})
    if existing:
        raise HTTPException(status_code=400, detail="Role already exists")
    doc = payload.model_dump()
    doc["role_id"] = new_id("ROLE")
    await roles_col.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.get("/")
async def list_roles(user=Depends(require_roles("admin", "training_manager", "reviewer", "manager", "employee"))):
    roles = await roles_col.find({}, {"_id": 0}).to_list(length=500)
    return roles


@router.post("/matrix")
async def add_requirement(payload: RequirementMatrixEntry, user=Depends(require_roles("admin", "training_manager"))):
    doc = payload.model_dump()
    doc["requirement_id"] = doc.get("requirement_id") or new_id("R")
    existing = await requirement_matrix_col.find_one({"requirement_id": doc["requirement_id"]})
    if existing:
        raise HTTPException(status_code=400, detail="requirement_id already exists")
    await requirement_matrix_col.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.post("/matrix/bulk")
async def bulk_add_requirements(payload: List[RequirementMatrixEntry], user=Depends(require_roles("admin", "training_manager"))):
    docs = []
    for p in payload:
        d = p.model_dump()
        d["requirement_id"] = d.get("requirement_id") or new_id("R")
        docs.append(d)
    if docs:
        await requirement_matrix_col.insert_many(docs)
    for d in docs:
        d.pop("_id", None)
    return {"inserted": len(docs), "requirements": docs}


@router.get("/matrix")
async def list_matrix(role_name: str = None,
                       user=Depends(require_roles("admin", "training_manager", "reviewer", "manager"))):
    query = {"role_name": role_name} if role_name else {}
    reqs = await requirement_matrix_col.find(query, {"_id": 0}).to_list(length=5000)
    return reqs


@router.delete("/matrix/{requirement_id}")
async def delete_requirement(requirement_id: str, user=Depends(require_roles("admin"))):
    await requirement_matrix_col.delete_one({"requirement_id": requirement_id})
    return {"message": f"Requirement {requirement_id} deleted"}
