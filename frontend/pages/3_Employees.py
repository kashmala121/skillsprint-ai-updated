import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
from utils.api_client import api_get, api_post, require_role
from utils import theme

_authed = "token" in st.session_state
st.set_page_config(page_title="Employees", page_icon="◆", layout="wide", initial_sidebar_state="expanded" if _authed else "collapsed")
theme.inject(authenticated=_authed)
require_role("admin", "training_manager")
theme.topnav("Employees", True, st.session_state.get("username", ""), st.session_state.get("role", "").replace("_", " ").title())

theme.hero("Employee Profiles", "Maintain the people going through onboarding — no sensitive personal data required.", eyebrow="People")

roles_resp = api_get("/roles/")
role_options = [r["role_name"] for r in roles_resp.json()] if roles_resp.status_code == 200 and roles_resp.json() else []

with st.container(border=True):
    with st.expander("➕ Add employee", expanded=False):
        with st.form("emp_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full name")
                role_name = st.selectbox("Job role", role_options) if role_options else st.text_input("Role (create a role first)")
                department = st.text_input("Department")
                experience_level = st.selectbox("Experience level", ["Beginner", "Intermediate", "Advanced"])
            with col2:
                location = st.text_input("Location")
                joining_date = st.date_input("Joining date")
                reporting_manager = st.text_input("Reporting manager")
                competencies = st.text_input("Required competencies (comma-separated)")

            if st.form_submit_button("Create Employee", use_container_width=True):
                payload = {
                    "name": name, "role_name": role_name, "department": department,
                    "experience_level": experience_level, "location": location,
                    "joining_date": str(joining_date), "reporting_manager": reporting_manager,
                    "required_competencies": [c.strip() for c in competencies.split(",") if c.strip()],
                }
                resp = api_post("/employees/", json=payload)
                if resp.status_code == 200:
                    st.session_state["_last_created_employee_id"] = resp.json()["employee_id"]
                    st.rerun()
                else:
                    st.error(resp.json().get("detail"))

_last_id = st.session_state.pop("_last_created_employee_id", None)
if _last_id:
    st.success(
        f"Employee created — ID: **{_last_id}**. Share this ID with them: they'll enter it under "
        "*Update Profile → Linked Employee ID* (or at sign-up) so their Employee Dashboard shows their own progress."
    )

theme.divider()
st.markdown("### Employee Directory")
emp_resp = api_get("/employees/")
if emp_resp.status_code == 200 and emp_resp.json():
    edf = pd.DataFrame(emp_resp.json())

    m1, m2, m3 = st.columns(3)
    with m1:
        theme.metric_card("👥", "Total Employees", str(len(edf)), "in directory", theme.GOLD)
    with m2:
        theme.metric_card("🧩", "Roles Covered", str(edf["role_name"].nunique()), "distinct roles", theme.INFO)
    with m3:
        assigned = int((edf["training_status"] == "Assigned").sum()) if "training_status" in edf.columns else 0
        theme.metric_card("📋", "Plans Assigned", str(assigned), "onboarding generated", theme.SUCCESS)

    st.markdown("")
    with st.container(border=True):
        fcol1, fcol2, fcol3 = st.columns(3)
        with fcol1:
            search = st.text_input("🔍 Search by name", "")
        with fcol2:
            role_filter = st.selectbox("Filter by role", ["All"] + sorted(edf["role_name"].dropna().unique().tolist()))
        with fcol3:
            status_filter = st.selectbox("Filter by training status", ["All"] + sorted(edf["training_status"].dropna().unique().tolist())) \
                if "training_status" in edf.columns else "All"

        filtered = edf.copy()
        if search:
            filtered = filtered[filtered["name"].str.contains(search, case=False, na=False)]
        if role_filter != "All":
            filtered = filtered[filtered["role_name"] == role_filter]
        if isinstance(status_filter, str) and status_filter != "All":
            filtered = filtered[filtered["training_status"] == status_filter]

        st.caption(f"Showing {len(filtered)} of {len(edf)} employees")
        st.dataframe(filtered, use_container_width=True, hide_index=True)
else:
    st.info("No employees yet.")
