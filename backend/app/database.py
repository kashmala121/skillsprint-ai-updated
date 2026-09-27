"""
MongoDB Atlas connection layer using Motor (async driver).
All collections used by the application are defined here so the rest
of the codebase imports a single `db` object.
"""
from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings

client = AsyncIOMotorClient(settings.MONGO_URI)
db = client[settings.MONGO_DB_NAME]

# Collections
users_col = db["users"]
documents_col = db["documents"]
chunks_col = db["document_chunks"]
roles_col = db["roles"]
requirement_matrix_col = db["role_requirement_matrix"]
employees_col = db["employees"]
onboarding_plans_col = db["onboarding_plans"]
validation_results_col = db["validation_results"]
comparison_results_col = db["comparison_results"]
audit_log_col = db["audit_log"]
prompt_templates_col = db["prompt_templates"]
adversarial_flags_col = db["adversarial_flags"]
progress_col = db["employee_progress"]


async def ensure_indexes():
    await users_col.create_index("username", unique=True)
    await employees_col.create_index("employee_id", unique=True)
    await documents_col.create_index("document_id", unique=True)
    await chunks_col.create_index("chunk_id", unique=True)
    await requirement_matrix_col.create_index("requirement_id", unique=True)
    await onboarding_plans_col.create_index([("employee_id", 1)])
