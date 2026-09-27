import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
from utils.api_client import api_get, api_post, require_login
from utils import theme

_authed = "token" in st.session_state
st.set_page_config(page_title="Employee Dashboard", page_icon="◆", layout="wide", initial_sidebar_state="expanded" if _authed else "collapsed")
theme.inject(authenticated=_authed)
require_login()
theme.topnav("Employee_Dashboard", True, st.session_state.get("username", ""), st.session_state.get("role", "").replace("_", " ").title())

theme.hero(
    "Employee Learning Dashboard",
    "Track modules, checklist items, tasks, quizzes and assessments assigned as part of onboarding.",
    eyebrow="Your Journey",
)

emp_resp = api_get("/employees/")
employees = emp_resp.json() if emp_resp.status_code == 200 else []
emp_options = {f"{e['name']} ({e['employee_id']})": e["employee_id"] for e in employees}

if not emp_options:
    st.info("No employees available yet.")
    st.stop()

selected = st.selectbox("View onboarding for", list(emp_options.keys()))
employee_id = emp_options[selected]

plan_resp = api_get(f"/onboarding/plan/{employee_id}")
if plan_resp.status_code != 200:
    st.warning("No onboarding plan generated yet for this employee. Ask an administrator to generate one.")
    st.stop()

plan_record = plan_resp.json()
plan = plan_record["plan"]

progress_resp = api_get(f"/progress/{employee_id}")
progress = progress_resp.json() if progress_resp.status_code == 200 else {}
progress = {
    "module_completion": progress.get("module_completion", {}),
    "checklist_completion": progress.get("checklist_completion", {}),
    "task_completion": progress.get("task_completion", {}),
    "quiz_scores": progress.get("quiz_scores", {}),
    "assessment_scores": progress.get("assessment_scores", {}),
}


def _mark_complete(item_type: str, item_id: str, key: str):
    if st.button("✓ Mark complete", key=key, use_container_width=True):
        api_post("/progress/update", json={
            "employee_id": employee_id, "item_type": item_type,
            "item_id": item_id, "status": "Completed",
        })
        st.rerun()


def _section_progress(ids, field):
    done = sum(1 for i in ids if progress[field].get(i) == "Completed")
    pct = round((done / len(ids)) * 100, 1) if ids else 0
    return done, pct

modules = plan.get("modules", []) or []
checklist = plan.get("checklist", []) or []
tasks = plan.get("tasks", []) or []
quizzes = plan.get("quizzes", []) or []
assessments = plan.get("assessments", []) or []

module_ids = [m["module_id"] for m in modules]
checklist_ids = [c["item_id"] for c in checklist]
task_ids = [t["task_id"] for t in tasks]
quiz_ids = [q["question_id"] for q in quizzes]
assessment_ids = [a["assessment_id"] for a in assessments]

mod_done, mod_pct = _section_progress(module_ids, "module_completion")
chk_done, chk_pct = _section_progress(checklist_ids, "checklist_completion")
task_done, task_pct = _section_progress(task_ids, "task_completion")
quiz_done, quiz_pct = _section_progress(quiz_ids, "quiz_scores")
assess_done, assess_pct = _section_progress(assessment_ids, "assessment_scores")

overall_total = len(module_ids) + len(checklist_ids) + len(task_ids) + len(quiz_ids) + len(assessment_ids)
overall_done = mod_done + chk_done + task_done + quiz_done + assess_done
overall_pct = round((overall_done / overall_total) * 100, 1) if overall_total else 0

kind = theme.status_badge_kind(plan_record["final_status"])
theme.card(f"""
    <div style="display:flex; align-items:flex-start; justify-content:space-between; gap:1.5rem; flex-wrap:wrap;">
        <div style="min-width:220px;">
            <div style="font-family:'Playfair Display',serif; font-size:1.4rem; font-weight:700; color:{theme.TEXT};">
                {plan_record['role_name']} &nbsp; {theme.badge(plan_record['final_status'], kind)}
            </div>
            <div class="ss-muted" style="margin-top:0.35rem;">Employee: {selected}</div>
        </div>
        <div style="text-align:right; min-width:140px;">
            <div class="ss-muted" style="font-size:0.75rem; text-transform:uppercase; letter-spacing:0.5px; white-space:nowrap;">Overall Progress</div>
            <div style="font-family:'Playfair Display',serif; font-size:1.9rem; color:{theme.GOLD_SOFT}; font-weight:700; white-space:nowrap; line-height:1.25;">{overall_pct}%</div>
        </div>
    </div>
""")
st.progress(overall_pct / 100, text=f"{overall_done}/{overall_total} items completed")
st.markdown("")

m1, m2, m3, m4, m5 = st.columns(5)
with m1:
    theme.metric_card("📋", "Modules", f"{mod_done}/{len(module_ids)}", f"{mod_pct}% complete", theme.GOLD)
with m2:
    theme.metric_card("✅", "Checklist", f"{chk_done}/{len(checklist_ids)}", f"{chk_pct}% complete", theme.SUCCESS)
with m3:
    theme.metric_card("🛠", "Tasks", f"{task_done}/{len(task_ids)}", f"{task_pct}% complete", theme.INFO)
with m4:
    theme.metric_card("❓", "Quizzes", f"{quiz_done}/{len(quiz_ids)}", f"{quiz_pct}% complete", theme.WARNING)
with m5:
    theme.metric_card("🎯", "Assessments", f"{assess_done}/{len(assessment_ids)}", f"{assess_pct}% complete", theme.DANGER)

theme.divider()

# ---------------------------------------------------------------------
# Learning Modules
# ---------------------------------------------------------------------
st.markdown("### 📋 Learning Modules")
if modules:
    for m in modules:
        status = progress["module_completion"].get(m["module_id"], "Not Started")
        badge_kind = "success" if status == "Completed" else "gold"
        with st.expander(f"{m['module_title']}  ·  {status}"):
            st.markdown(theme.badge(status, badge_kind), unsafe_allow_html=True)
            st.write(m.get("purpose"))
            st.write("**Objectives:**", m.get("learning_objectives"))
            st.caption(f"Source: {m.get('source_document_id')} / {m.get('source_section_id')} · Due: {m.get('due_stage')}")
            if status != "Completed":
                _mark_complete("module", m["module_id"], key=f"btn_mod_{m['module_id']}")
else:
    st.caption("No learning modules in this plan.")

theme.divider()

# ---------------------------------------------------------------------
# Checklist — each item with live status + a per-item complete action
# ---------------------------------------------------------------------
st.markdown("### ✅ Checklist")
if checklist:
    for c in checklist:
        status = progress["checklist_completion"].get(c["item_id"], "Not Started")
        badge_kind = "success" if status == "Completed" else ("danger" if c.get("required") else "gold")
        with st.container(border=True):
            row_l, row_r = st.columns([4, 1.1])
            with row_l:
                req_txt = "Required" if c.get("required") else "Optional"
                st.markdown(f"**{c.get('activity')}**  &nbsp; {theme.badge(status, badge_kind)}", unsafe_allow_html=True)
                st.caption(f"{req_txt} · Due: {c.get('due_stage')} · Source: {c.get('source_document_id')} / {c.get('source_section_id')}")
            with row_r:
                if status != "Completed":
                    _mark_complete("checklist", c["item_id"], key=f"btn_chk_{c['item_id']}")
                else:
                    st.markdown('<div style="text-align:right; padding-top:0.5rem;">' + theme.badge("Done ✓", "success") + '</div>', unsafe_allow_html=True)
else:
    st.caption("No checklist items in this plan.")

theme.divider()

# ---------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------
st.markdown("### 🛠 Tasks")
if tasks:
    for t in tasks:
        status = progress["task_completion"].get(t["task_id"], "Not Started")
        badge_kind = "success" if status == "Completed" else "gold"
        with st.expander(f"{t.get('description')}  ·  {status}"):
            st.markdown(theme.badge(status, badge_kind), unsafe_allow_html=True)
            st.write("**Expected outcome:**", t.get("expected_outcome"))
            st.caption(f"Difficulty: {t.get('difficulty')} · Due: {t.get('due_stage')} · Source: {t.get('source_document_id')} / {t.get('source_section_id')}")
            if status != "Completed":
                _mark_complete("task", t["task_id"], key=f"btn_task_{t['task_id']}")
else:
    st.caption("No tasks in this plan.")

theme.divider()

# ---------------------------------------------------------------------
# Quizzes
# ---------------------------------------------------------------------
st.markdown("### ❓ Quizzes")
if quizzes:
    for q in quizzes:
        status = progress["quiz_scores"].get(q["question_id"], "Not Attempted")
        badge_kind = "success" if status == "Completed" else "gold"
        with st.expander(f"{q['question']}  ·  {status}"):
            st.markdown(theme.badge(status, badge_kind), unsafe_allow_html=True)
            st.write("**Options:**", q.get("options"))
            st.caption(f"Difficulty: {q.get('difficulty')} · Source: {q.get('source_document_id')}")
            if status != "Completed":
                _mark_complete("quiz", q["question_id"], key=f"btn_quiz_{q['question_id']}")
else:
    st.caption("No quizzes in this plan.")

theme.divider()

# ---------------------------------------------------------------------
# Assessments — previously missing from the employee view entirely
# ---------------------------------------------------------------------
st.markdown("### 🎯 Assessments")
if assessments:
    for a in assessments:
        status = progress["assessment_scores"].get(a["assessment_id"], "Not Started")
        badge_kind = "success" if status == "Completed" else "gold"
        with st.expander(f"{a.get('topic')}  ·  {status}"):
            st.markdown(theme.badge(status, badge_kind), unsafe_allow_html=True)
            st.caption(f"Type: {a.get('type')} · Source: {a.get('source_document_id')} / {a.get('source_section_id')}")
            rubric = a.get("rubric") or []
            if rubric:
                st.dataframe(pd.DataFrame(rubric), use_container_width=True, hide_index=True)
            if status != "Completed":
                _mark_complete("assessment", a["assessment_id"], key=f"btn_assess_{a['assessment_id']}")
else:
    st.caption("No assessments in this plan.")

theme.divider()

# ---------------------------------------------------------------------
# Weak-Area Detection + Adaptive Recommendations (functional requirements
# liv/lv) — derived client-side from progress data: overdue-mandatory
# checklist items and any category stuck below 50% are surfaced so the
# employee (and their manager) know exactly where to focus next.
# ---------------------------------------------------------------------
st.markdown("### 🧭 Weak Areas & Recommendations")

weak_categories = [
    (name, pct, done, total) for name, pct, done, total in [
        ("Modules", mod_pct, mod_done, len(module_ids)),
        ("Checklist", chk_pct, chk_done, len(checklist_ids)),
        ("Tasks", task_pct, task_done, len(task_ids)),
        ("Quizzes", quiz_pct, quiz_done, len(quiz_ids)),
        ("Assessments", assess_pct, assess_done, len(assessment_ids)),
    ] if total > 0 and pct < 50
]
overdue_required = [
    c for c in checklist
    if c.get("required") and progress["checklist_completion"].get(c["item_id"]) != "Completed"
]

if not weak_categories and not overdue_required:
    with st.container(border=True):
        st.markdown(theme.badge("On track", "success"), unsafe_allow_html=True)
        st.caption("No weak areas detected — every category is at or above 50% completion and no mandatory checklist items are overdue.")
else:
    for name, pct, done, total in weak_categories:
        with st.container(border=True):
            st.markdown(f"**{name}** &nbsp; {theme.badge(f'{pct}% complete', 'danger' if pct < 25 else 'warning')}", unsafe_allow_html=True)
            st.caption(f"Recommendation: only {done}/{total} {name.lower()} items are done — prioritize this section before moving on to new material.")
    if overdue_required:
        with st.container(border=True):
            st.markdown(f"**Mandatory checklist items pending** &nbsp; {theme.badge(str(len(overdue_required)), 'danger')}", unsafe_allow_html=True)
            st.caption("Recommendation: these are required for role compliance and should be completed first:")
            for c in overdue_required:
                st.markdown(f"- {c.get('activity')} (due: {c.get('due_stage')})")

theme.divider()

# ---------------------------------------------------------------------
# Gaps flagged by the generator — grounded content couldn't cover these
# ---------------------------------------------------------------------
insufficient = plan.get("insufficient_information") or []
if insufficient:
    st.markdown("### ⚠ Insufficient Source Coverage")
    with st.container(border=True):
        st.caption("These requirements could not be grounded in the uploaded company documents:")
        for item in insufficient:
            st.markdown(f"- {item}")
