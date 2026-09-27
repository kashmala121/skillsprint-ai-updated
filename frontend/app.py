import sys, os
sys.path.append(os.path.dirname(__file__))

import streamlit as st
from utils.api_client import login, logout, register
from utils import theme

is_authenticated = "token" in st.session_state

st.set_page_config(
    page_title="SkillSprint AI",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded" if is_authenticated else "collapsed",
)
theme.inject(authenticated=is_authenticated)

theme.topnav(
    active="app",
    authenticated=is_authenticated,
    username=st.session_state.get("username", ""),
    role=st.session_state.get("role", "").replace("_", " ").title(),
)

# ---------------------------------------------------------------------
# UNAUTHENTICATED: centered hero + centered sign-in card + feature steps
# ---------------------------------------------------------------------
if not is_authenticated:
    _notice = st.session_state.pop("_redirect_notice", None)

    st.markdown("""
    <div style="text-align:center; padding-top:4.5vh; margin-bottom:3rem;">
        <div class="ss-logo-text" style="font-size:1.5rem; margin-bottom:1rem; display:inline-flex; align-items:center; gap:0.5rem;">
            ◆ SkillSprint AI
        </div>
        <h1 style="border:none; padding:0; margin-bottom:0.8rem; font-size:3.2rem;">Onboarding, grounded in your policies</h1>
        <p class="ss-muted" style="font-size:1.15rem; max-width:680px; margin:0 auto;">
            Upload company policy, build a role requirement matrix, and let OpenAI generate
            onboarding plans that are checked against your source documents — not guesses.
        </p>
    </div>
    """, unsafe_allow_html=True)

    if _notice:
        st.info(_notice)

    col_gap_l, col_card, col_features, col_gap_r = st.columns([0.25, 1.6, 1.85, 0.25])

    with col_card:
        with st.container(border=True):
            st.markdown("### Welcome Back")
            st.markdown('<p class="ss-muted" style="margin-top:-0.6rem; font-size:1rem;">Sign in to continue</p>', unsafe_allow_html=True)

            tab_signin, tab_signup = st.tabs(["Sign In", "Create Account"])

            with tab_signin:
                with st.form("login_form"):
                    username = st.text_input("👤  Username", value="", placeholder="Enter your username")
                    password = st.text_input("🔒  Password", type="password", value="", placeholder="Enter your password")
                    submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")
                    if submitted:
                        if not username or not password:
                            st.error("Please enter both username and password.")
                        else:
                            ok, data = login(username, password)
                            if ok:
                                st.success("Signed in successfully.")
                                st.rerun()
                            else:
                                st.error(f"Sign-in failed: {data}")

            with tab_signup:
                st.caption("New here? Create a login to access SkillSprint AI.")
                with st.form("register_form"):
                    r_full_name = st.text_input("Full Name", placeholder="e.g. Kashmala Khan")
                    r_username = st.text_input("Choose a Username", placeholder="e.g. kashmala@gmail.com")
                    r_role = st.selectbox(
                        "Role",
                        ["employee", "manager", "training_manager", "reviewer", "admin"],
                        format_func=lambda r: r.replace("_", " ").title(),
                    )
                    r_password = st.text_input("Choose a Password", type="password", placeholder="Minimum 6 characters")
                    r_password_confirm = st.text_input("Confirm Password", type="password")
                    r_submitted = st.form_submit_button("Create Account", use_container_width=True, type="primary")
                    if r_submitted:
                        if not r_username or not r_password:
                            st.error("Username and password are required.")
                        elif r_password != r_password_confirm:
                            st.error("Passwords do not match.")
                        elif len(r_password) < 6:
                            st.error("Password must be at least 6 characters.")
                        else:
                            ok, data = register(r_username, r_password, r_role, r_full_name)
                            if ok:
                                st.success("Account created. You can now sign in from the 'Sign In' tab.")
                            else:
                                st.error(f"Registration failed: {data}")

            with st.expander("First-Time Setup?"):
                st.caption(
                    "Run `python -m app.seed_admin` in the backend to create the default "
                    "admin login (**admin** / **Admin@123**), or use the **Create Account** "
                    "tab above to register any other user (employee, manager, reviewer, etc.)."
                )

    with col_features:
        steps = [
            ("📤", "01", "Upload", "PDF / DOCX policies, SOPs, FAQs — validated, parsed, and chunked with full source traceability.", theme.GOLD),
            ("🗂", "02", "Ground truth", "Build the Role Requirement Matrix: mandatory vs. optional, per role, cited to a source section.", theme.INFO),
            ("✨", "03", "Generate", "OpenAI produces a structured, source-grounded onboarding plan as JSON — never free text.", theme.SUCCESS),
        ]
        for icon, num, title, desc, color in steps:
            theme.card(f"""
                <div style="display:flex; gap:1.2rem; align-items:flex-start; padding:0.3rem 0.1rem;">
                    {theme.icon_circle(icon, size="3.4rem", accent=color)}
                    <div>
                        <div class="ss-muted" style="font-family:'Playfair Display',serif; font-size:0.9rem; letter-spacing:1px;">STEP {num}</div>
                        <div style="font-weight:700; font-size:1.25rem; margin:0.2rem 0 0.4rem;">{title}</div>
                        <div class="ss-muted" style="font-size:0.95rem; line-height:1.5;">{desc}</div>
                    </div>
                </div>
            """)

# ---------------------------------------------------------------------
# AUTHENTICATED: account summary + pipeline overview
# ---------------------------------------------------------------------
else:
    import datetime
    _hour = datetime.datetime.now().hour
    _greeting = "Good morning" if _hour < 12 else ("Good afternoon" if _hour < 18 else "Good evening")
    _display_name = st.session_state.get("full_name") or st.session_state["username"].split("@")[0].replace(".", " ").title()
    _role_label = st.session_state["role"].replace("_", " ").title()

    st.markdown(f"""
        <div style="padding-top:0.4rem; margin-bottom:0.3rem;">
            <div class="ss-muted" style="letter-spacing:2px; text-transform:uppercase; font-size:0.78rem;">SkillSprint AI · Onboarding Workspace</div>
            <h1 style="margin:0.3rem 0 0.2rem; border:none; padding:0;">{_greeting}, {_display_name}</h1>
            <p class="ss-muted" style="font-size:1.02rem; margin:0;">You're signed in as <b style="color:#E4C766;">{_role_label}</b>. Here's where you can pick up.</p>
        </div>
    """, unsafe_allow_html=True)

    theme.divider()
    st.markdown("### Quick Actions")
    actions = [("📤", "Upload Documents", "pages/1_Documents.py", theme.GOLD),
               ("🗂", "Requirement Matrix", "pages/2_Roles_and_Requirements.py", theme.INFO),
               ("✨", "Generate Onboarding", "pages/4_Generate_Onboarding.py", theme.SUCCESS),
               ("⚖", "Validation & Review", "pages/5_Validation_Review.py", theme.WARNING)]
    qa_cols = st.columns(4)
    for qc, (icon, label, target, accent) in zip(qa_cols, actions):
        with qc:
            with st.container(border=True):
                st.markdown(f'<div style="margin-bottom:0.7rem;">{theme.icon_circle(icon, size="3rem", accent=accent)}</div>', unsafe_allow_html=True)
                st.page_link(target, label=label, use_container_width=True)

    theme.divider()
    st.markdown("### Pipeline Overview")
    cols = st.columns(5)
    stages = [
        ("📤", "Upload & Chunk", theme.GOLD), ("🗂", "Requirement Matrix", theme.INFO), ("✨", "OpenAI Generation", theme.SUCCESS),
        ("🐍", "Python Validation", theme.WARNING), ("⚖", "Compare & Review", theme.DANGER),
    ]
    for c, (icon, label, accent) in zip(cols, stages):
        with c:
            theme.card(f"""
                <div style="text-align:center; padding:0.4rem 0;">
                    <div style="display:flex; justify-content:center; margin-bottom:0.6rem;">{theme.icon_circle(icon, size="2.6rem", accent=accent)}</div>
                    <div class="ss-muted" style="font-size:0.78rem; text-transform:uppercase; letter-spacing:0.5px;">{label}</div>
                </div>
            """)

    st.markdown("")
    st.caption("Use the sidebar to jump into Documents, the Requirement Matrix, "
               "Employees, Generate Onboarding, Validation & Review, or the dashboards.")
