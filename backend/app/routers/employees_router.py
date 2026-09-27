from fastapi import APIRouter, Depends, HTTPException

from ..database import employees_col
from ..auth import require_roles
from ..models.schemas import EmployeeCreate, new_id

router = APIRouter(prefix="/employees", tags=["employees"])


@router.post("/")
async def create_employee(payload: EmployeeCreate, user=Depends(require_roles("admin", "training_manager"))):
    doc = payload.model_dump()
    doc["employee_id"] = doc.get("employee_id") or new_id("EMP")
    existing = await employees_col.find_one({"employee_id": doc["employee_id"]})
    if existing:
        raise HTTPException(status_code=400, detail="employee_id already exists")
    doc["training_status"] = "Not Started"
    await employees_col.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.get("/")
async def list_employees(user=Depends(require_roles("admin", "training_manager", "reviewer", "manager"))):
    employees = await employees_col.find({}, {"_id": 0}).to_list(length=2000)
    return employees


@router.get("/{employee_id}")
async def get_employee(employee_id: str, user=Depends(require_roles(
        "admin", "training_manager", "reviewer", "manager", "employee"))):
    emp = await employees_col.find_one({"employee_id": employee_id}, {"_id": 0})
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp
