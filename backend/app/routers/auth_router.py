from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm

from ..database import users_col, employees_col
from ..auth import hash_password, verify_password, create_access_token, get_current_user
from ..models.schemas import UserCreate, UserUpdate

router = APIRouter(prefix="/auth", tags=["auth"])


async def _validate_employee_link(employee_id: str, requesting_username: str):
    """An employee_id can only be linked if it exists and is not already
    claimed by a different login — otherwise two employee accounts could
    both claim to be the same person and see each other's private progress."""
    emp = await employees_col.find_one({"employee_id": employee_id})
    if not emp:
        raise HTTPException(status_code=400, detail=f"No employee profile found with ID '{employee_id}'. Ask your administrator for the correct ID.")
    claimed_by = await users_col.find_one({"employee_id": employee_id, "username": {"$ne": requesting_username}})
    if claimed_by:
        raise HTTPException(status_code=400, detail="This employee ID is already linked to another account.")


@router.post("/register")
async def register(payload: UserCreate):
    existing = await users_col.find_one({"username": payload.username})
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    doc = {
        "username": payload.username,
        "password_hash": hash_password(payload.password),
        "role": payload.role,
        "full_name": payload.full_name,
    }
    if payload.role == "employee" and payload.employee_id:
        await _validate_employee_link(payload.employee_id, payload.username)
        doc["employee_id"] = payload.employee_id
    await users_col.insert_one(doc)
    return {"message": "User registered", "username": payload.username, "role": payload.role}


@router.post("/login")
async def login(form: OAuth2PasswordRequestForm = Depends()):
    user = await users_col.find_one({"username": form.username})
    if not user or not verify_password(form.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_access_token({"sub": user["username"], "role": user["role"]})
    return {"access_token": token, "token_type": "bearer", "role": user["role"], "username": user["username"]}


@router.get("/me")
async def me(user=Depends(get_current_user)):
    return {
        "username": user["username"], "role": user["role"],
        "full_name": user.get("full_name"), "employee_id": user.get("employee_id"),
    }


@router.put("/me")
async def update_me(payload: UserUpdate, user=Depends(get_current_user)):
    updates = {}

    if payload.full_name is not None:
        updates["full_name"] = payload.full_name

    if payload.new_password:
        if not payload.current_password or not verify_password(payload.current_password, user["password_hash"]):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        if len(payload.new_password) < 6:
            raise HTTPException(status_code=400, detail="New password must be at least 6 characters")
        updates["password_hash"] = hash_password(payload.new_password)

    if payload.employee_id is not None and payload.employee_id != user.get("employee_id"):
        if payload.employee_id == "":
            updates["employee_id"] = None
        else:
            await _validate_employee_link(payload.employee_id, user["username"])
            updates["employee_id"] = payload.employee_id

    if not updates:
        raise HTTPException(status_code=400, detail="Nothing to update")

    await users_col.update_one({"username": user["username"]}, {"$set": updates})
    updated = await users_col.find_one({"username": user["username"]})
    return {
        "username": updated["username"], "role": updated["role"],
        "full_name": updated.get("full_name"), "employee_id": updated.get("employee_id"),
    }
