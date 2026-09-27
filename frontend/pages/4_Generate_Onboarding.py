import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
from utils.api_client import api_get, api_post, require_role
from utils import theme

_authed = "token" in st.session_state
st.set_page_config(page_title="Generate Onboarding Plan", page_icon="◆", layout="wide", initial_sidebar_state="expanded" if _authed else "collapsed")
theme.inject(authenticated=_authed)
require_role("admin", "training_manager")
theme.topnav("Generate_Onboarding", True, st.session_state.get("username", ""), st.session_state.get("role", "").replace("_", " ").title())

theme.hero("Generate Onboarding Plan", "Pipeline 1 (OpenAI) drafts the plan — Pipeline 2 (pure Python) independently verifies it.", eyebrow="Dual-Pipeline Generation")

emp_resp = api_get("/employees/")
employees = emp_resp.json() if emp_resp.status_code == 200 else []
emp_options = {f"{e['name']} ({e['employee_id']}) — {e['role_name']}": e["employee_id"] for e in employees}

if not emp_options:
    st.warning("No employees found. Add one on the Employees page first.")
    st.stop()

with st.container(border=True):
    selected_label = st.selectbox("Select employee", list(emp_options.keys()))
    employee_id = emp_options[selected_label]
    col1, col2 = st.columns(2)
    generate_clicked = col1.button("✨  Generate Onboarding Plan", type="primary", use_container_width=True)
    consistency_clicked = col2.button("🔁  Run Consistency Check", use_container_width=True)

if generate_clicked:
    with st.spinner("Calling OpenAI (Pipeline 1) and running Python validation (Pipeline 2)..."):
        resp = api_post("/onboarding/generate", json={"employee_id": employee_id})
    if resp.status_code != 200:
        st.error(f"Generation failed: {resp.json().get('detail')}")
    else:
        st.session_state["last_generation"] = resp.json()
        st.success("Onboarding plan generated and validated.")

if consistency_clicked:
    with st.spinner("Running two controlled generations..."):
        resp = api_post("/onboarding/consistency-check", json={"employee_id": employee_id})
    if resp.status_code != 200:
        st.error(f"Consistency check failed: {resp.json().get('detail')}")
    else:
        data = resp.json()["consistency"]
        theme.metric_card("🔁", "Generation Consistency Score", f"{data['consistency_score']}%", "across 2 controlled runs", theme.INFO)
        with st.expander("Details"):
            st.json(data)

result = st.session_state.get("last_generation")
if result:
    plan_record = result["plan"]
    validation = result["validation"]
    comparison = result["comparison"]
    plan = plan_record["plan"]

    status = validation["final_status"]
    kind = theme.status_badge_kind(status)
    status_color = {"success": theme.SUCCESS, "warning": theme.WARNING, "danger": theme.DANGER, "gold": theme.GOLD}[kind]

    st.markdown("")
    left, right = st.columns([1.3, 1], gap="large")

    with left:
        m1, m2 = st.columns(2)
        with m1:
            theme.metric_card("📊", "Coverage Score", f"{validation['coverage']['coverage_score']}%",
                               f"{validation['coverage']['covered_count']}/{validation['coverage']['total_mandatory']} mandatory items", theme.GOLD)
        with m2:
            theme.metric_card("🔗", "Traceability Score", f"{validation['traceability']['traceability_score']}%",
                               f"{validation['traceability']['traced_count']}/{validation['traceability']['total_mandatory_items']} items sourced", theme.INFO)
        m3, m4 = st.columns(2)
        with m3:
            theme.metric_card("⚠", "Missing Requirements", str(validation["consistency_count"]["missing_requirement_count"]), "vs. requirement matrix", theme.WARNING)
        with m4:
            theme.metric_card("⚖", "Contradictions", str(validation["consistency_count"]["contradiction_count"]), "policy conflicts found", theme.DANGER)

    with right:
        with st.container(border=True):
            theme.panel_header("🛡", "PYTHON VALIDATION ENGINE", status, kind)
            theme.progress_row("Coverage", validation['coverage']['coverage_score'], color=theme.GOLD)
            theme.progress_row("Traceability", validation['traceability']['traceability_score'], color=theme.INFO)
            hallucination_free = 100 if not validation["hallucinations"] else max(0, 100 - len(validation["hallucinations"]) * 10)
            theme.progress_row("Hallucination-Free", hallucination_free, color=theme.SUCCESS)
            st.caption("Independently computed — zero AI involvement in this check.")

    st.markdown("")
    tabs = st.tabs([
        "Modules", "Checklist", "Tasks", "Quizzes", "Assessments",
        "OpenAI vs Python Comparison", "Hallucinations & Issues",
    ])

    with tabs[0]:
        if plan.get("modules"):
            st.dataframe(pd.DataFrame(plan["modules"]), use_container_width=True, hide_index=True)
        else:
            st.caption("No modules generated.")

    with tabs[1]:
        if plan.get("checklist"):
            st.dataframe(pd.DataFrame(plan["checklist"]), use_container_width=True, hide_index=True)
        else:
            st.caption("No checklist items generated.")

    with tabs[2]:
        if plan.get("tasks"):
            st.dataframe(pd.DataFrame(plan["tasks"]), use_container_width=True, hide_index=True)
        else:
            st.caption("No tasks generated.")

    with tabs[3]:
        if plan.get("quizzes"):
            st.dataframe(pd.DataFrame(plan["quizzes"]), use_container_width=True, hide_index=True)
        else:
            st.caption("No quizzes generated.")

    with tabs[4]:
        if plan.get("assessments"):
            for a in plan["assessments"]:
                with st.container(border=True):
                    st.markdown(f"**{a.get('topic')}** ({a.get('assessment_id')})")
                    if a.get("rubric"):
                        st.dataframe(pd.DataFrame(a["rubric"]), use_container_width=True, hide_index=True)
        else:
            st.caption("No assessments generated.")

    with tabs[5]:
        st.write("Summary:", comparison["summary"])
        rows_flat = []
        for row in comparison["rows"]:
            for f in row["fields"]:
                rows_flat.append({"requirement_id": row["requirement_id"], "role": row["role"],
                                   "validation_status": row["validation_status"], **f})
        if rows_flat:
            st.dataframe(pd.DataFrame(rows_flat), use_container_width=True, hide_index=True)

    with tabs[6]:
        st.markdown("**Hallucinations / Unsupported Content**")
        st.json(validation["hallucinations"] or "None detected")
        st.markdown("**Duplicate Content**")
        st.json(validation["duplicates"] or "None detected")
        st.markdown("**Contradictions**")
        st.json(validation["contradictions"] or "None detected")
        st.markdown("**Sequence / Prerequisite Issues**")
        st.json(validation["sequence_issues"] or "None detected")
        st.markdown("**Role Relevance Issues**")
        st.json(validation["role_relevance_issues"] or "None detected")
        st.markdown("**Schema Errors**")
        st.json(validation["schema_errors"] or "None")
