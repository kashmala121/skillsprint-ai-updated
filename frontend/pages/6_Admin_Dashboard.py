import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.api_client import api_get, api_post, require_role
from utils import theme

_authed = "token" in st.session_state
st.set_page_config(page_title="Admin Dashboard", page_icon="◆", layout="wide", initial_sidebar_state="expanded" if _authed else "collapsed")
theme.inject(authenticated=_authed)
require_role("admin", "training_manager")
theme.topnav("Admin_Dashboard", True, st.session_state.get("username", ""), st.session_state.get("role", "").replace("_", " ").title())

theme.hero("Administrator Dashboard", "A live view of onboarding coverage, traceability and verification health across the organization.", eyebrow="Command Center")

resp = api_get("/dashboard/admin")
if resp.status_code == 200:
    d = resp.json()
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        theme.metric_card("👥", "Employees", str(d["total_employees"]), "in the system", theme.GOLD)
    with c2:
        theme.metric_card("📁", "Documents", str(d["total_documents"]), "uploaded & chunked", theme.INFO)
    with c3:
        theme.metric_card("📋", "Plans Generated", str(d["total_plans_generated"]), "onboarding plans", theme.SUCCESS)
    with c4:
        theme.metric_card("📊", "Avg. Coverage", f"{d['average_coverage_score']}%", "mandatory requirement coverage", theme.WARNING)

    st.markdown("")
    col_chart, col_gauge = st.columns([1.3, 1])

    with col_chart:
        with st.container(border=True):
            theme.panel_header("📈", "VERIFICATION STATUS BREAKDOWN")
            if d["status_breakdown"]:
                status_df = pd.DataFrame(list(d["status_breakdown"].items()), columns=["Status", "Count"])
                fig = px.pie(status_df, names="Status", values="Count", hole=0.55,
                             color_discrete_sequence=["#C9A227", "#2E9E6B", "#4A8FA6", "#C0453D", "#9A9AA5", "#E4C766"])
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#EDEBE6", legend=dict(orientation="h", y=-0.1),
                    margin=dict(t=10, b=10, l=10, r=10),
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.caption("No validation data yet — generate an onboarding plan first.")

    with col_gauge:
        with st.container(border=True):
            theme.panel_header("🎯", "TRACEABILITY SCORE")
            fig2 = go.Figure(go.Indicator(
                mode="gauge+number",
                value=d["average_traceability_score"],
                number={"suffix": "%", "font": {"color": "#E4C766"}},
                gauge={
                    "axis": {"range": [0, 100], "tickcolor": "#9A9AA5"},
                    "bar": {"color": "#C9A227"},
                    "bgcolor": "#17171F",
                    "borderwidth": 1, "bordercolor": "#2A2A35",
                    "steps": [
                        {"range": [0, 60], "color": "#2A1616"},
                        {"range": [60, 90], "color": "#2A2416"},
                        {"range": [90, 100], "color": "#16281F"},
                    ],
                },
            ))
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#EDEBE6",
                                margin=dict(t=30, b=10, l=20, r=20), height=260)
            st.plotly_chart(fig2, use_container_width=True)

theme.divider()
st.markdown("### ⬇ Export Reports")
with st.container(border=True):
    e1, e2, e3 = st.columns(3)
    with e1:
        csv_resp = api_get("/reports/coverage.csv")
        if csv_resp.status_code == 200:
            st.download_button("📄 Coverage Report (CSV)", data=csv_resp.content,
                                file_name="coverage_report.csv", mime="text/csv", use_container_width=True)
    with e2:
        xlsx_resp = api_get("/reports/coverage.xlsx")
        if xlsx_resp.status_code == 200:
            st.download_button("📊 Coverage Report (Excel)", data=xlsx_resp.content,
                                file_name="coverage_report.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True)
    with e3:
        pdf_resp = api_get("/reports/coverage.pdf")
        if pdf_resp.status_code == 200:
            st.download_button("🖨 Coverage Report (PDF)", data=pdf_resp.content,
                                file_name="coverage_report.pdf", mime="application/pdf", use_container_width=True)

    matrix_xlsx = api_get("/reports/requirement-matrix.xlsx")
    if matrix_xlsx.status_code == 200:
        st.download_button("📊 Full Role Requirement Matrix (Excel)", data=matrix_xlsx.content,
                            file_name="role_requirement_matrix.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

theme.divider()
st.markdown("### 🔁 Policy Update Impact Analysis")
docs_resp = api_get("/documents/")
docs = docs_resp.json() if docs_resp.status_code == 200 else []
if docs:
    with st.container(border=True):
        doc_id = st.selectbox("Select an updated/replaced document", [d["document_id"] for d in docs])
        if st.button("Run Impact Analysis", use_container_width=True):
            result = api_post("/policy-update/impact-analysis", json={"document_id": doc_id})
            if result.status_code == 200:
                data = result.json()
                m1, m2, m3 = st.columns(3)
                with m1:
                    theme.metric_card("📋", "Affected Requirements", str(len(data['affected_requirements'])), "", theme.WARNING)
                with m2:
                    theme.metric_card("👥", "Affected Employees", str(len(data['affected_employees'])), "", theme.DANGER)
                with m3:
                    theme.metric_card("🔁", "Plans to Regenerate", str(len(data['plans_requiring_regeneration'])), "", theme.INFO)
                st.write(f"**Affected roles:** {', '.join(data['affected_roles']) or 'None'}")
                st.info(data["recommendation"])
            else:
                st.error(result.json().get("detail"))
else:
    st.caption("Upload documents first to run impact analysis.")
