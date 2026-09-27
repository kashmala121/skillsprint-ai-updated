from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import ensure_indexes
from .routers import (
    auth_router, documents_router, roles_router, employees_router,
    onboarding_router, validation_router, progress_reports_router,
)

app = FastAPI(
    title="SkillSprint AI",
    description="Generative AI-powered onboarding intelligence platform "
                "(dual GenAI + Python ground-truth validation pipeline).",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(documents_router.router)
app.include_router(roles_router.router)
app.include_router(employees_router.router)
app.include_router(onboarding_router.router)
app.include_router(validation_router.router)
app.include_router(progress_reports_router.router)


@app.on_event("startup")
async def on_startup():
    await ensure_indexes()


@app.get("/")
async def root():
    return {"app": "SkillSprint AI", "status": "running", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok"}
