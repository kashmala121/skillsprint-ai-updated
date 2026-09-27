"""
Generates requirement_matrix_seed.json - the Role Requirement Matrix for all
10 roles (SRS Step 10/11, and the '150+ identifiable requirements, 50+
mandatory, 30+ role-specific' minimums from the Hint section).

Each row references a document by FILENAME and a HEADING (not a database
document_id/section_id, which only exist after upload). scripts/seed_full_dataset.py
resolves filename -> real document_id, and computes section_id the same
deterministic way the backend's chunker does: f"{heading[:30]}-1".
"""
import json
import os

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "sample_documents", "dataset")

ROLES = [
    "Sales Executive", "Customer Support Executive", "HR Executive", "Finance Associate",
    "Operations Coordinator", "Marketing Executive", "Software Support Engineer",
    "Branch Manager", "Data Analyst", "Team Leader",
]

# ---- Common requirements applied to every role (10 items x 10 roles = 100 rows) ----
COMMON_ITEMS = [
    # (policy_requirement, competency, mandatory, priority, due_stage, doc_file, heading, req_type)
    ("Acknowledge Employee Handbook Code of Conduct", "Company Culture Awareness", True, "High", "Day 1",
     "Employee_Handbook_v2.docx", "Code of Conduct Overview", "Must Acknowledge"),
    ("Understand Company Culture Values", "Cultural Alignment", False, "Low", "Day 1",
     "Employee_Handbook_v2.docx", "Company Culture", "Recommended"),
    ("Acknowledge Leave Policy", "Leave Awareness", True, "Medium", "Week 1",
     "Leave_Policy_v2.docx", "Leave Entitlement", "Must Acknowledge"),
    ("Complete Code of Conduct Training", "Ethics & Compliance", True, "High", "Day 1",
     "HR_Policy_v2.docx", "Code of Conduct", "Must Complete"),
    ("Know Information Security Password Policy", "Information Security Awareness", True, "High", "Week 1",
     "Information_Security_Policy_v1.docx", "Password Policy", "Must Know"),
    ("Acknowledge Device Usage Policy", "Information Security Awareness", True, "Medium", "Week 1",
     "Information_Security_Policy_v1.docx", "Device Usage", "Must Acknowledge"),
    ("Acknowledge Anti-Harassment Policy", "Workplace Conduct", True, "High", "Week 1",
     "Workplace_Conduct_Policy_v1.docx", "Harassment and Discrimination", "Must Acknowledge"),
    ("Know Customer Data Handling Rules", "Data Privacy Awareness", True, "High", "Week 2",
     "Data_Privacy_Policy_v1.docx", "Customer Data Handling", "Must Know"),
    ("Know Mandatory Compliance Training Requirements", "Regulatory Compliance", True, "Medium", "First 30 Days",
     "Compliance_Requirements_v1.docx", "Mandatory Compliance Training", "Must Know"),
    ("Review General Escalation Matrix", "Cross-functional Awareness", False, "Low", "First 30 Days",
     "Escalation_Procedures_v1.docx", "General Escalation Matrix", "Recommended"),
]

# ---- Role-specific SOP filenames (matches ROLE_SOP_CONTENT in generate_dataset.py) ----
ROLE_SOP_FILE = {
    "Sales Executive": "Sales_Executive_SOP.docx",
    "Customer Support Executive": "Customer_Support_Executive_SOP.docx",
    "HR Executive": "HR_Executive_SOP.docx",
    "Finance Associate": "Finance_Associate_SOP.docx",
    "Operations Coordinator": "Operations_Coordinator_SOP.docx",
    "Marketing Executive": "Marketing_Executive_SOP.docx",
    "Software Support Engineer": "Software_Support_Engineer_SOP.docx",
    "Branch Manager": "Branch_Manager_SOP.docx",
    "Data Analyst": "Data_Analyst_SOP.docx",
    "Team Leader": "Team_Leader_SOP.docx",
}

# ---- Role-specific requirement template (6 items x 10 roles = 60 rows) ----
ROLE_SPECIFIC_TEMPLATE = [
    ("Know Core Role Responsibilities", "Role Fundamentals", True, "High", "Week 1", "Core Responsibilities", "Must Know"),
    ("Complete Standard Operating Procedure Training", "Process Compliance", True, "High", "Week 1",
     "Standard Operating Procedure", "Must Complete"),
    ("Demonstrate Escalation and Exception Handling", "Escalation Competency", True, "High", "Week 2",
     "Escalation and Exceptions", "Must Demonstrate"),
    ("Acknowledge Compliance and Approval Limits", "Approval Authority Awareness", True, "Medium", "Week 2",
     "Compliance and Approval Limits", "Must Acknowledge"),
    ("Know Required Tools and Systems", "Systems Proficiency", True, "Medium", "First 30 Days",
     "Tools and Systems", "Must Know"),
    ("Review Advanced Role Scenarios", "Advanced Competency", False, "Low", "First 60 Days",
     "Advanced Scenarios", "Recommended"),
]

rows = []
req_counter = 1


def next_id():
    global req_counter
    rid = f"R{req_counter:04d}"
    req_counter += 1
    return rid


for role in ROLES:
    for policy, competency, mandatory, priority, due_stage, doc_file, heading, req_type in COMMON_ITEMS:
        rows.append({
            "requirement_id": next_id(), "role_name": role, "policy_requirement": policy,
            "process_requirement": "", "competency": competency, "mandatory": mandatory,
            "priority": priority, "due_stage": due_stage, "source_document_file": doc_file,
            "source_heading": heading, "assessment_requirement": f"Quiz: {policy}",
            "requirement_type": req_type,
        })

for role in ROLES:
    doc_file = ROLE_SOP_FILE[role]
    for policy, competency, mandatory, priority, due_stage, heading, req_type in ROLE_SPECIFIC_TEMPLATE:
        rows.append({
            "requirement_id": next_id(), "role_name": role,
            "policy_requirement": f"{policy} ({role})", "process_requirement": policy,
            "competency": competency, "mandatory": mandatory, "priority": priority,
            "due_stage": due_stage, "source_document_file": doc_file, "source_heading": heading,
            "assessment_requirement": f"Practical assessment: {policy} for {role}",
            "requirement_type": req_type,
        })

# Extra role-specific requirement for Customer Support Executive citing the legacy SOP-07 doc
rows.append({
    "requirement_id": next_id(), "role_name": "Customer Support Executive",
    "policy_requirement": "Demonstrate SOP-07 Escalation Process", "process_requirement": "Escalation Process",
    "competency": "Escalation Competency", "mandatory": True, "priority": "High", "due_stage": "Week 1",
    "source_document_file": "Customer_Support_SOP.docx", "source_heading": "4.2 Escalation Process",
    "assessment_requirement": "Scenario quiz: SOP-07 escalation", "requirement_type": "Must Demonstrate",
})

mandatory_count = sum(1 for r in rows if r["mandatory"])
role_specific_count = sum(1 for r in rows if "(" in r["policy_requirement"] and ")" in r["policy_requirement"]) \
    + 1  # + the SOP-07 row above

with open(os.path.join(BASE_DIR, "requirement_matrix_seed.json"), "w") as f:
    json.dump(rows, f, indent=2)

print(f"Total requirements: {len(rows)}")
print(f"Mandatory requirements: {mandatory_count}")
print(f"Role-specific requirements: {role_specific_count}")
print(f"Roles covered: {len(ROLES)}")
