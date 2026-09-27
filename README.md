# SkillSprint AI

Generative AI-powered onboarding intelligence platform, built per the SRS
(Theme: OnboardVerse, Category: Generative AI PowerPlay).

- **Frontend:** Streamlit
- **Backend:** Python + FastAPI
- **Generative AI:** OpenAI API (`openai`)
- **Database:** MongoDB Atlas (via Motor async driver)

## What's implemented

This is a working, end-to-end implementation of the SRS's mandatory
architecture:

1. **Document Upload & Processing** — PDF & DOCX (+ TXT/MD bonus) upload,
   validation (type/size/empty/duplicate via hash), parsing, and chunking with
   full source traceability (`document_id`, `chunk_id`, `section_id`,
   `heading`, page/paragraph location, version, effective date).
2. **Role Requirement Matrix** — structured ground-truth mapping of roles to
   mandatory/optional requirements, priorities, due stages and source
   references.
3. **Pipeline 1 — GenAI Generation** (`backend/app/pipeline/genai_pipeline.py`)
   — calls OpenAI with source-grounded, sanitized prompts and versioned
   prompt templates, enforces structured JSON output, retries on failure.
4. **Pipeline 2 — Python Ground-Truth Validation**
   (`backend/app/pipeline/python_validation.py`) — a fully independent,
   non-AI, deterministic engine that computes:
   - Mandatory Requirement Coverage Score
   - Source Traceability Score
   - Hallucination / unsupported-content detection
   - Duplicate content detection
   - Contradiction detection with configurable policy precedence
   - Prerequisite / learning-sequence validation
   - Role-relevance checking
   - JSON schema validation
   - A final verification status (`Verified`, `Verified with Warning`,
     `Partially Verified`, `Requirement Missing`, `Unsupported Requirement`,
     `Contradiction Detected`, `Manual Review Required`)
5. **Comparison Engine** — field-by-field GenAI-vs-Python comparison table
   (mirrors the SRS's Table 1 example), never comparing exact sentence wording.
6. **Prompt Injection / Adversarial Document Defense**
   (`backend/app/security/prompt_injection.py`) — scans every chunk for
   adversarial patterns before it ever reaches a prompt, and wraps all source
   content in explicit data delimiters so embedded instructions are never
   executed. See `sample_documents/Adversarial_FAQ_Sample.docx` for a live
   test case.
7. **Manual Review Workflow** — review queue, reviewer approve/reject/edit/
   regenerate decisions, and an audit trail that keeps both the original
   automated result and the reviewer's override.
8. **Policy Update Detection & Impact Analysis** — given an updated document,
   identifies affected requirements, roles, employees and plans, and returns
   the exact list of plans that need *selective* regeneration.
9. **Dashboards & Reports** — admin dashboard (coverage/traceability
   averages, status breakdown), employee dashboard (progress tracking), and a
   CSV coverage-report export.
10. **Auth & RBAC** — JWT login with roles: `admin`, `training_manager`,
    `reviewer`, `manager`, `employee`.

### Included dataset: "Nimbus Retail Co"

A complete fictional company document pack is included and meets the SRS
Hint minimums out of the box:

- **24 documents** (Policies, SOPs, FAQs, Employee Handbook, Compliance docs)
- **10 job roles** (Sales Executive, Customer Support Executive, HR Executive,
  Finance Associate, Operations Coordinator, Marketing Executive, Software
  Support Engineer, Branch Manager, Data Analyst, Team Leader)
- **161 Role Requirement Matrix rows** (131 mandatory, 61 role-specific)
- **3 policy-version-change pairs** (v1 → v2, with `supersedes_document_id`)
- **10 documented conflict/ambiguity cases**
- **10 adversarial / prompt-injection test cases** (verified to trigger the
  security scanner)

See `sample_documents/DATASET_REFERENCE.md` for the full catalog of
conflicts, version changes and adversarial cases. Files live in
`sample_documents/dataset/`; regenerate or extend them with
`scripts/generate_dataset.py` and `scripts/generate_requirement_matrix.py`.

This is a genuine starting point, not a stand-in for the competition
requirement that **each team build its own original scenario** — you should
still customize the company name, add more documents/roles/edge cases, and
produce the full documentation deliverables (DFD/UML diagrams, technical
blog, test reports, demo video, etc.) listed in SRS section 1.10 before
final submission, per the "Unique Company Pack" integrity rule.

## Project structure

```
skillsprint-ai/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app
│   │   ├── config.py
│   │   ├── database.py             # MongoDB Atlas (Motor) connection + collections
│   │   ├── auth.py                 # JWT auth + RBAC
│   │   ├── seed_admin.py           # creates the first admin login
│   │   ├── models/schemas.py       # Pydantic request/response models
│   │   ├── pipeline/
│   │   │   ├── document_processing.py   # Steps 4-8: validate/parse/chunk
│   │   │   ├── prompt_templates.py      # Step 40/41: versioned prompts
│   │   │   ├── genai_pipeline.py        # Pipeline 1 (OpenAI)
│   │   │   ├── python_validation.py     # Pipeline 2 (pure Python ground truth)
│   │   │   └── comparison_engine.py     # GenAI vs Python comparison
│   │   ├── security/prompt_injection.py # adversarial/injection defense
│   │   └── routers/                     # auth, documents, roles, employees,
│   │                                     # onboarding, validation, progress/reports
│   └── requirements.txt
├── frontend/
│   ├── app.py                      # Streamlit login/home
│   ├── pages/                      # Documents, Roles, Employees, Generate
│   │                                # Onboarding, Validation & Review,
│   │                                # Admin Dashboard, Employee Dashboard
│   ├── utils/api_client.py
│   └── requirements.txt
├── sample_documents/
│   ├── DATASET_REFERENCE.md         # catalog of conflicts/versions/adversarial cases
│   └── dataset/                     # 24 DOCX files + manifest + requirement matrix seed
├── scripts/
│   ├── generate_dataset.py          # (re)generates the 24 DOCX documents
│   ├── generate_requirement_matrix.py  # (re)generates the 161-row matrix seed
│   └── seed_full_dataset.py         # uploads everything to a running backend
├── tests/
├── .env.example
└── README.md
```

## Setup

### 1. MongoDB Atlas
Create a free cluster at https://www.mongodb.com/cloud/atlas, create a
database user, and whitelist your IP (or `0.0.0.0/0` for local testing).
Copy the connection string.

### 2. OpenAI API key
Get a key from https://platform.openai.com/api-keys.

### 3. Configure environment
```bash
cp .env.example .env
# edit .env: MONGO_URI, OPENAI_API_KEY, JWT_SECRET
```
Both the backend and frontend read this `.env` (place a copy in `backend/`
and `frontend/`, or export the variables in your shell before running each).

### 4. Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env .env
python -m app.seed_admin        # creates admin / Admin@123
uvicorn app.main:app --reload --port 8000
```
API docs available at http://localhost:8000/docs

### 5. Frontend
```bash
cd frontend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp ../.env .env
streamlit run app.py
```
Open http://localhost:8501, log in with `admin` / `Admin@123`.

## Quick end-to-end test (one command)

Once the backend is running and the admin user is seeded, load the entire
Nimbus Retail Co dataset (24 documents, 10 roles, 161 requirements, 10 demo
employees) in one shot:

```bash
cd skillsprint-ai
pip install requests --break-system-packages   # if not already installed
python scripts/seed_full_dataset.py
```

Then in the Streamlit app:
1. **Documents** page → confirm 24 documents and 10 adversarial flags appear.
2. **Roles & Requirements** page → confirm 161 requirements across 10 roles.
3. **Generate Onboarding** page → pick any `Demo <Role>` employee (e.g.
   "Demo Customer Support Executive") → click *Generate Onboarding Plan* and
   watch both pipelines run: OpenAI output, coverage/traceability scores, the
   GenAI-vs-Python comparison table, and any hallucination/contradiction
   flags.
4. **Admin Dashboard** page → view aggregate stats, run a policy-update
   impact analysis (try `Leave_Policy_v2.docx`'s document_id to see the
   affected roles/employees), export the CSV coverage report.

To test manually instead, upload individual files from
`sample_documents/dataset/` via the Documents page and build the matrix by
hand via the Roles & Requirements page.

## Security notes

- Passwords are hashed with bcrypt; access is via short-lived JWTs.
- `.env` / API keys must never be committed — see `.gitignore`.
- Uploaded document text is always treated as **data**, never as
  instructions (see `security/prompt_injection.py` and the system prompt in
  `pipeline/prompt_templates.py`).

## Known simplifications / next steps

- Contradiction detection uses a heuristic keyword/heading-overlap +
  precedence-category comparison (deterministic, non-AI) rather than full
  semantic clause matching — swap in an embeddings-based similarity check
  (`sentence-transformers` / OpenAI embeddings) for higher precision if
  needed.
- No live HRMS/payroll integration (explicitly out of scope per SRS §1.4).
- Rate limiting / API quota backoff for OpenAI is basic retry-count only;
  add exponential backoff for production use.
