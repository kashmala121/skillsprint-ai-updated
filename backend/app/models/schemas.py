from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
import uuid


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


# ---------------- Auth / Users ----------------
class UserCreate(BaseModel):
    username: str
    password: str
    role: Literal["admin", "training_manager", "reviewer", "manager", "employee"] = "employee"
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None


# ---------------- Roles ----------------
class RoleCreate(BaseModel):
    role_name: str
    department: str
    description: Optional[str] = ""


# ---------------- Employees ----------------
class EmployeeCreate(BaseModel):
    employee_id: Optional[str] = None
    name: str
    role_name: str
    department: str
    experience_level: Literal["Beginner", "Intermediate", "Advanced"] = "Beginner"
    location: Optional[str] = None
    joining_date: Optional[str] = None
    reporting_manager: Optional[str] = None
    required_competencies: Optional[List[str]] = []
    previous_experience: Optional[str] = None


# ---------------- Documents ----------------
class DocumentMeta(BaseModel):
    document_id: Optional[str] = None
    title: str
    doc_type: Literal[
        "Policy", "SOP", "RoleDescription", "ProcessManual", "FAQ",
        "ComplianceDoc", "EmployeeHandbook", "Other"
    ] = "Other"
    department: Optional[str] = "General"
    version: str = "1.0"
    effective_date: Optional[str] = None
    expiry_date: Optional[str] = None
    precedence_category: Literal[
        "Latest Approved Policy", "Department SOP", "FAQ", "Informal Guidance"
    ] = "Latest Approved Policy"
    supersedes_document_id: Optional[str] = None


class RequirementMatrixEntry(BaseModel):
    requirement_id: Optional[str] = None
    role_name: str
    policy_requirement: str
    process_requirement: Optional[str] = ""
    competency: Optional[str] = ""
    mandatory: bool = True
    priority: Literal["High", "Medium", "Low"] = "Medium"
    due_stage: Literal["Day 1", "Week 1", "Week 2", "First 30 Days", "First 60 Days", "First 90 Days"] = "Week 1"
    source_document_id: str
    source_section_id: str
    assessment_requirement: Optional[str] = ""
    requirement_type: Literal[
        "Must Know", "Must Complete", "Must Demonstrate",
        "Must Acknowledge", "Recommended", "Optional", "Not Applicable"
    ] = "Must Know"


class OnboardingGenerateRequest(BaseModel):
    employee_id: str


class ReviewerDecision(BaseModel):
    item_id: str
    decision: Literal["approve", "reject", "edit", "regenerate"]
    comment: Optional[str] = None
    edited_content: Optional[dict] = None
    reviewer: str
