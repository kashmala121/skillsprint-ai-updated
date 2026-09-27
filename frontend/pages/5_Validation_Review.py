import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
from utils.api_client import api_get, api_post, require_role
from utils import theme

_authed = "token" in st.session_state
st.set_page_config(page_title="Validation & Review", page_icon="◆", layout="wide", initial_sidebar_state="expanded" if _authed else "collapsed")
theme.inject(authenticated=_authed)
require_role("admin", "training_manager", "reviewer")
theme.topnav("Validation_Review", True, st.session_state.get("username", ""), st.session_state.get("role", "").replace("_", " ").title())

theme.hero("Manual Review Queue", "Every plan not fully Verified lands here for human review before it's trusted.", eyebrow="Human-in-the-Loop")

st.markdown("### Items requiring review")
queue_resp = api_get("/validation/manual-review-queue")
if queue_resp.status_code == 200 and queue_resp.json():
    theme.metric_card("🔍", "Pending Review", str(len(queue_resp.json())), "plans flagged", theme.WARNING)
    st.markdown("")
    for item in queue_resp.json():
        kind = theme.status_badge_kind(item['final_status'])
        with st.expander(f"{item['employee_id']} — {item['final_status']}"):
            st.markdown(theme.badge(item['final_status'], kind), unsafe_allow_html=True)
            st.json(item)
else:
    theme.metric_card("✅", "Pending Review", "0", "nothing flagged right now", theme.SUCCESS)

theme.divider()
with st.container(border=True):
    st.markdown("### Record a reviewer decision")
    with st.form("review_form"):
        item_id = st.text_input("Item ID (module_id / task_id / question_id / plan_id etc.)")
        decision = st.selectbox("Decision", ["approve", "reject", "edit", "regenerate"])
        comment = st.text_area("Comment")
        if st.form_submit_button("Submit decision", use_container_width=True):
            payload = {
                "item_id": item_id, "decision": decision, "comment": comment,
                "reviewer": st.session_state["username"],
            }
            resp = api_post("/validation/reviewer-decision", json=payload)
            if resp.status_code == 200:
                st.success("Decision recorded to audit trail.")
            else:
                st.error(resp.json().get("detail"))

theme.divider()
st.markdown("### Audit Trail")
audit_resp = api_get("/validation/audit-trail")
if audit_resp.status_code == 200 and audit_resp.json():
    with st.container(border=True):
        adf = pd.DataFrame(audit_resp.json())
        search = st.text_input("🔍 Search audit trail (action / employee_id / user)", "")
        if search:
            mask = False
            for col in ["action", "employee_id", "user", "decided_by_user"]:
                if col in adf.columns:
                    mask = mask | adf[col].astype(str).str.contains(search, case=False, na=False)
            adf = adf[mask]
        st.dataframe(adf, use_container_width=True, hide_index=True)
else:
    st.caption("No audit events yet.")
