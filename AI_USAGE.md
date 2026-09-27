# AI_USAGE.md

This project used Claude (Anthropic) as an AI coding assistant during
development, as permitted by SRS section 1.8 (#15 AI Code Usage).

| AI tool | Purpose | Prompt / assistance type | File(s)/module affected | Modification performed | Test performed | Verified by |
|---|---|---|---|---|---|---|
| Claude | Scaffold the initial full-stack project (FastAPI backend, Streamlit frontend, dual GenAI/Python validation pipeline) from the SRS | "Build the SkillSprint AI application per this SRS: Streamlit frontend, FastAPI backend, Google OpenAI, MongoDB Atlas" | All files under `backend/app/` and `frontend/` | Generated initial implementation; team must review, adapt to their own company document set, test against their own Role Requirement Matrix, and extend contradiction/hallucination heuristics as needed | Manual smoke test pending (upload sample docs → generate plan → verify scores) | _fill in team member name_ |

> Per SRS rules, every team member must be able to explain any code they
> submit. Add a new row to this table for every additional AI-assisted change
> you make (new validation rule, new dashboard filter, bug fix, etc.), and
> keep this file up to date across all five competition days.
