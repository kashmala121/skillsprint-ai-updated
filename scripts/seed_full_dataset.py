"""
One-shot dataset loader. Run this AFTER the backend is running and you have
seeded the admin user (python -m app.seed_admin).

    cd skillsprint-ai
    python scripts/seed_full_dataset.py

What it does:
  1. Logs in as admin.
  2. Uploads all 24 DOCX documents in documents_manifest.json, in dependency
     order (base policy versions before the versions that supersede them),
     capturing each document's real document_id.
  3. Creates the 10 roles from roles.json.
  4. Resolves requirement_matrix_seed.json (which references documents by
     filename + heading) into real requirement_id/source_document_id/
     source_section_id rows and bulk-imports them (161 rows).
  5. Creates one demo employee per role so you can immediately generate an
     onboarding plan for any of the 10 roles.

Safe to re-run: duplicate documents are skipped (detected by content hash),
duplicate roles/requirements are skipped with a warning.
"""
import json
import os
import sys
import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
DATASET_DIR = os.path.join(os.path.dirname(__file__), "..", "sample_documents", "dataset")
ADMIN_USERNAME = os.getenv("SEED_ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("SEED_ADMIN_PASSWORD", "Admin@123")


def login():
    resp = requests.post(f"{BACKEND_URL}/auth/login",
                          data={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})
    resp.raise_for_status()
    return resp.json()["access_token"]


def upload_documents(token):
    with open(os.path.join(DATASET_DIR, "documents_manifest.json")) as f:
        manifest = json.load(f)

    headers = {"Authorization": f"Bearer {token}"}
    filename_to_doc_id = {}

    for entry in manifest:
        filepath = os.path.join(DATASET_DIR, entry["filename"])
        supersedes_id = filename_to_doc_id.get(entry["supersedes"]) if entry["supersedes"] else ""

        with open(filepath, "rb") as fh:
            files = {"file": (entry["filename"], fh.read())}

        data = {
            "title": entry["title"], "doc_type": entry["doc_type"], "department": entry["department"],
            "version": entry["version"], "effective_date": entry["effective_date"],
            "precedence_category": entry["precedence_category"], "supersedes_document_id": supersedes_id or "",
        }
        resp = requests.post(f"{BACKEND_URL}/documents/upload", headers=headers, data=data, files=files)
        if resp.status_code == 409:
            print(f"  [skip] {entry['filename']} already uploaded (duplicate hash)")
            # Try to find its document_id from the existing list
            existing = requests.get(f"{BACKEND_URL}/documents/", headers=headers).json()
            match = next((d for d in existing if d["title"] == entry["title"] and d["version"] == entry["version"]), None)
            if match:
                filename_to_doc_id[entry["filename"]] = match["document_id"]
            continue
        if resp.status_code != 200:
            print(f"  [ERROR] {entry['filename']}: {resp.status_code} {resp.text}")
            continue

        result = resp.json()
        doc_id = result["document"]["document_id"]
        filename_to_doc_id[entry["filename"]] = doc_id
        flag_note = f" ⚠️ {result['adversarial_flags_found']} adversarial flag(s)" if result["adversarial_flags_found"] else ""
        print(f"  [ok] {entry['filename']} -> {doc_id} ({result['chunk_count']} chunks){flag_note}")

    return filename_to_doc_id


def create_roles(token):
    with open(os.path.join(DATASET_DIR, "roles.json")) as f:
        roles = json.load(f)
    headers = {"Authorization": f"Bearer {token}"}
    for role in roles:
        resp = requests.post(f"{BACKEND_URL}/roles/", headers=headers, json=role)
        if resp.status_code == 200:
            print(f"  [ok] role created: {role['role_name']}")
        elif resp.status_code == 400:
            print(f"  [skip] role already exists: {role['role_name']}")
        else:
            print(f"  [ERROR] {role['role_name']}: {resp.text}")
    return [r["role_name"] for r in roles]


def import_requirement_matrix(token, filename_to_doc_id):
    with open(os.path.join(DATASET_DIR, "requirement_matrix_seed.json")) as f:
        seed_rows = json.load(f)

    resolved = []
    for row in seed_rows:
        doc_id = filename_to_doc_id.get(row["source_document_file"])
        if not doc_id:
            print(f"  [WARN] no document_id found for {row['source_document_file']}, skipping {row['requirement_id']}")
            continue
        section_id = f"{row['source_heading'][:30]}-1"
        resolved.append({
            "requirement_id": row["requirement_id"], "role_name": row["role_name"],
            "policy_requirement": row["policy_requirement"], "process_requirement": row["process_requirement"],
            "competency": row["competency"], "mandatory": row["mandatory"], "priority": row["priority"],
            "due_stage": row["due_stage"], "source_document_id": doc_id, "source_section_id": section_id,
            "assessment_requirement": row["assessment_requirement"], "requirement_type": row["requirement_type"],
        })

    headers = {"Authorization": f"Bearer {token}"}
    batch_size = 40
    inserted_total = 0
    for i in range(0, len(resolved), batch_size):
        batch = resolved[i:i + batch_size]
        resp = requests.post(f"{BACKEND_URL}/roles/matrix/bulk", headers=headers, json=batch)
        if resp.status_code == 200:
            inserted_total += resp.json()["inserted"]
            print(f"  [ok] imported batch {i // batch_size + 1}: {resp.json()['inserted']} requirements")
        else:
            print(f"  [ERROR] batch {i // batch_size + 1}: {resp.status_code} {resp.text[:300]}")
    print(f"Total requirements imported: {inserted_total} / {len(resolved)}")


def create_demo_employees(token, role_names):
    headers = {"Authorization": f"Bearer {token}"}
    for role in role_names:
        payload = {
            "name": f"Demo {role}", "role_name": role, "department": role,
            "experience_level": "Beginner", "location": "Karachi",
            "joining_date": "2026-09-24", "reporting_manager": "System Seed",
            "required_competencies": [],
        }
        resp = requests.post(f"{BACKEND_URL}/employees/", headers=headers, json=payload)
        if resp.status_code == 200:
            print(f"  [ok] demo employee created for {role}: {resp.json()['employee_id']}")
        elif resp.status_code == 400:
            print(f"  [skip] demo employee already exists for {role}")
        else:
            print(f"  [ERROR] {role}: {resp.text}")


def main():
    print(f"Connecting to backend at {BACKEND_URL} ...")
    try:
        token = login()
    except Exception as e:
        print(f"Login failed: {e}\nMake sure the backend is running and `python -m app.seed_admin` was run.")
        sys.exit(1)
    print("Logged in as admin.\n")

    print("Step 1/4: Uploading 24 documents (this scans each for prompt-injection patterns too)...")
    filename_to_doc_id = upload_documents(token)
    print()

    print("Step 2/4: Creating 10 roles...")
    role_names = create_roles(token)
    print()

    print("Step 3/4: Importing Role Requirement Matrix (161 rows)...")
    import_requirement_matrix(token, filename_to_doc_id)
    print()

    print("Step 4/4: Creating 1 demo employee per role...")
    create_demo_employees(token, role_names)
    print()

    print("Done! Open the Streamlit frontend, go to 'Generate Onboarding', pick any "
          "'Demo <Role>' employee, and click Generate Onboarding Plan.")


if __name__ == "__main__":
    main()
