import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
from utils.api_client import api_get, api_post, require_role
from utils import theme

_authed = "token" in st.session_state
st.set_page_config(page_title="Roles & Requirement Matrix", page_icon="◆", layout="wide", initial_sidebar_state="expanded" if _authed else "collapsed")
theme.inject(authenticated=_authed)
require_role("admin", "training_manager")
theme.topnav("Roles_and_Requirements", True, st.session_state.get("username", ""), st.session_state.get("role", "").replace("_", " ").title())

theme.hero("Roles & Requirement Matrix", "The ground-truth reference every generated onboarding item is checked against.", eyebrow="Role Intelligence")

tab1, tab2 = st.tabs(["Roles", "Requirement Matrix"])

with tab1:
    with st.container(border=True):
        with st.form("role_form", clear_on_submit=True):
            role_name = st.text_input("Role name (e.g. Customer Support Executive)")
            department = st.text_input("Department")
            description = st.text_area("Description", height=80)
            if st.form_submit_button("Create Role", use_container_width=True):
                resp = api_post("/roles/", json={"role_name": role_name, "department": department, "description": description})
                if resp.status_code == 200:
                    st.success(f"Role '{role_name}' created.")
                    st.rerun()
                else:
                    st.error(resp.json().get("detail"))

    roles_resp = api_get("/roles/")
    if roles_resp.status_code == 200 and roles_resp.json():
        rdf = pd.DataFrame(roles_resp.json())
        theme.metric_card("🧩", "Total Roles", str(len(rdf)), "job roles defined", theme.GOLD)
        st.markdown("")
        with st.container(border=True):
            search = st.text_input("🔍 Search roles", "")
            if search:
                rdf = rdf[rdf["role_name"].str.contains(search, case=False, na=False)]
            st.dataframe(rdf, use_container_width=True, hide_index=True)

with tab2:
    docs_resp = api_get("/documents/")
    doc_options = [d["document_id"] for d in docs_resp.json()] if docs_resp.status_code == 200 else []
    roles_resp = api_get("/roles/")
    role_options = [r["role_name"] for r in roles_resp.json()] if roles_resp.status_code == 200 and roles_resp.json() else []

    st.info("Every mandatory requirement MUST cite a source_document_id + source_section_id "
            "so generated content can be traced back to an approved document.")

    with st.expander("➕ Add a requirement", expanded=False):
        with st.form("req_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                r_role = st.selectbox("Role", role_options) if role_options else st.text_input("Role (create a role first)")
                policy_requirement = st.text_input("Policy / process requirement")
                competency = st.text_input("Required competency")
                requirement_type = st.selectbox("Requirement type", [
                    "Must Know", "Must Complete", "Must Demonstrate", "Must Acknowledge",
                    "Recommended", "Optional", "Not Applicable"])
            with col2:
                mandatory = st.checkbox("Mandatory", value=True)
                priority = st.selectbox("Priority", ["High", "Medium", "Low"])
                due_stage = st.selectbox("Due stage", ["Day 1", "Week 1", "Week 2", "First 30 Days", "First 60 Days", "First 90 Days"])
                source_doc = st.selectbox("Source document_id", doc_options) if doc_options else st.text_input("Source document_id")
                source_section = st.text_input("Source section_id (e.g. 4.2 or a heading-part like 'Escalation-1')")
            assessment_req = st.text_input("Assessment requirement (optional)")

            if st.form_submit_button("Add Requirement", use_container_width=True):
                payload = {
                    "role_name": r_role, "policy_requirement": policy_requirement, "competency": competency,
                    "mandatory": mandatory, "priority": priority, "due_stage": due_stage,
                    "source_document_id": source_doc, "source_section_id": source_section,
                    "assessment_requirement": assessment_req, "requirement_type": requirement_type,
                }
                resp = api_post("/roles/matrix", json=payload)
                if resp.status_code == 200:
                    st.success(f"Requirement {resp.json()['requirement_id']} added.")
                    st.rerun()
                else:
                    st.error(resp.json().get("detail"))

    theme.divider()
    with st.container(border=True):
        fcol1, fcol2, fcol3 = st.columns(3)
        with fcol1:
            filter_role = st.selectbox("Filter by role", ["All"] + role_options)
        with fcol2:
            mandatory_filter = st.selectbox("Filter by mandatory status", ["All", "Mandatory only", "Optional only"])
        with fcol3:
            search_req = st.text_input("🔍 Search requirement text", "")

        params = {} if filter_role == "All" else {"role_name": filter_role}
        matrix_resp = api_get("/roles/matrix", params=params)
        if matrix_resp.status_code == 200 and matrix_resp.json():
            mdf = pd.DataFrame(matrix_resp.json())
            if mandatory_filter == "Mandatory only":
                mdf = mdf[mdf["mandatory"] == True]
            elif mandatory_filter == "Optional only":
                mdf = mdf[mdf["mandatory"] == False]
            if search_req:
                mdf = mdf[mdf["policy_requirement"].str.contains(search_req, case=False, na=False)]

            m1, m2, m3 = st.columns(3)
            m1.metric("Total Requirements", len(mdf))
            m2.metric("Mandatory", int(mdf["mandatory"].sum()) if "mandatory" in mdf else 0)
            m3.metric("Roles Covered", mdf["role_name"].nunique() if "role_name" in mdf else 0)

            st.dataframe(mdf, use_container_width=True, hide_index=True)
        else:
            st.caption("No requirements added yet for this filter. Try 'All' roles, or run "
                       "`python scripts/seed_full_dataset.py` from the project root if you "
                       "haven't loaded the sample dataset yet.")
