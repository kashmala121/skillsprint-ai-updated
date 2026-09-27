import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
from utils.api_client import api_get, api_post, api_delete, require_role
from utils import theme

_authed = "token" in st.session_state
st.set_page_config(page_title="Documents", page_icon="◆", layout="wide", initial_sidebar_state="expanded" if _authed else "collapsed")
theme.inject(authenticated=_authed)
require_role("admin", "training_manager")
theme.topnav("Documents", True, st.session_state.get("username", ""), st.session_state.get("role", "").replace("_", " ").title())

theme.hero("Company Documents", "Upload, validate, parse and chunk policies, SOPs and FAQs with full source traceability.", eyebrow="Document Intelligence")

with st.container(border=True):
    with st.expander("⬆  Upload a new document", expanded=False):
        with st.form("upload_form", clear_on_submit=True):
            file = st.file_uploader("Select PDF or DOCX file", type=["pdf", "docx", "txt", "md"])
            title = st.text_input("Document title")
            col1, col2 = st.columns(2)
            with col1:
                doc_type = st.selectbox("Document type", [
                    "Policy", "SOP", "RoleDescription", "ProcessManual", "FAQ",
                    "ComplianceDoc", "EmployeeHandbook", "Other"])
                department = st.text_input("Department", value="General")
                version = st.text_input("Version", value="1.0")
            with col2:
                effective_date = st.date_input("Effective date")
                precedence = st.selectbox("Precedence category", [
                    "Latest Approved Policy", "Department SOP", "FAQ", "Informal Guidance"])
                supersedes = st.text_input("Supersedes document_id (optional)")
            submitted = st.form_submit_button("Upload & Process", use_container_width=True)

            if submitted:
                if not file or not title:
                    st.error("File and title are required.")
                else:
                    files = {"file": (file.name, file.getvalue())}
                    data = {
                        "title": title, "doc_type": doc_type, "department": department,
                        "version": version, "effective_date": str(effective_date),
                        "precedence_category": precedence, "supersedes_document_id": supersedes or "",
                    }
                    resp = api_post("/documents/upload", data=data, files=files)
                    if resp.status_code == 200:
                        result = resp.json()
                        st.success(f"Uploaded — Document ID: {result['document']['document_id']} · "
                                   f"{result['chunk_count']} chunks created.")
                        if result["adversarial_flags_found"]:
                            st.warning(f"⚠ {result['adversarial_flags_found']} adversarial/prompt-injection "
                                       f"pattern(s) detected and flagged.")
                            st.json(result["adversarial_flags"])
                    else:
                        st.error(f"Upload failed: {resp.json().get('detail')}")

theme.divider()
st.markdown("### Document Library")

resp = api_get("/documents/")
if resp.status_code == 200:
    docs = resp.json()
    if docs:
        df = pd.DataFrame(docs)

        m1, m2, m3 = st.columns(3)
        with m1:
            theme.metric_card("📁", "Total Documents", str(len(df)), "in library", theme.GOLD)
        with m2:
            active_count = int((df["status"] == "active").sum()) if "status" in df.columns else len(df)
            theme.metric_card("✅", "Active", str(active_count), "current versions", theme.SUCCESS)
        with m3:
            obsolete_count = len(df) - active_count if "status" in df.columns else 0
            theme.metric_card("🗄", "Obsolete", str(obsolete_count), "superseded versions", theme.MUTED)

        st.markdown("")
        with st.container(border=True):
            fcol1, fcol2, fcol3 = st.columns(3)
            with fcol1:
                search_term = st.text_input("🔍 Search by title / filename", "")
            with fcol2:
                type_filter = st.selectbox("Filter by type", ["All"] + sorted(df["doc_type"].dropna().unique().tolist()))
            with fcol3:
                status_filter = st.selectbox("Filter by status", ["All"] + sorted(df["status"].dropna().unique().tolist()))

            filtered = df.copy()
            if search_term:
                mask = filtered["title"].str.contains(search_term, case=False, na=False) | \
                       filtered["filename"].str.contains(search_term, case=False, na=False)
                filtered = filtered[mask]
            if type_filter != "All":
                filtered = filtered[filtered["doc_type"] == type_filter]
            if status_filter != "All":
                filtered = filtered[filtered["status"] == status_filter]

            st.caption(f"Showing {len(filtered)} of {len(df)} documents")
            st.dataframe(filtered, use_container_width=True, hide_index=True)

            del_id = st.selectbox("Delete a document by ID", ["-- select --"] + [d["document_id"] for d in docs])
            if del_id != "-- select --" and st.button("Delete selected document"):
                d = api_delete(f"/documents/{del_id}")
                if d.status_code == 200:
                    st.success(d.json()["message"])
                    st.rerun()
    else:
        st.info("No documents uploaded yet.")

theme.divider()
st.markdown("### 🚩 Adversarial / Prompt-Injection Flags")
flags_resp = api_get("/documents/adversarial-flags")
if flags_resp.status_code == 200 and flags_resp.json():
    with st.container(border=True):
        st.dataframe(pd.DataFrame(flags_resp.json()), use_container_width=True, hide_index=True)
else:
    st.caption("No adversarial content detected in uploaded documents so far.")
