"""
Premium visual theme for SkillSprint AI — top-navbar SaaS dashboard style
(charcoal + gold), no left sidebar. Every "card" renders from ONE
st.markdown() call — Streamlit does not nest HTML across separate calls,
so splitting an open <div> and a later closing </div> across two calls
produces an empty box followed by unstyled content. Everything here avoids
that trap.

Usage: call inject() once at the top of every page (after set_page_config),
then topnav(...) to render the header, then use card()/metric_card()/
panel_card() — each is a single call with the full inner content passed in.
"""
import streamlit as st

GOLD = "#C9A227"
GOLD_SOFT = "#E4C766"
CHARCOAL = "#0B0B0F"
CARD = "#14141B"
CARD_BORDER = "#262631"
TEXT = "#EDEBE6"
MUTED = "#8F8FA0"
SUCCESS = "#2E9E6B"
WARNING = "#C9A227"
DANGER = "#C0453D"
INFO = "#4A8FA6"

NAV_PAGES = [
    ("app", "Home", "app.py"),
    ("Documents", "Documents", "pages/1_Documents.py"),
    ("Roles_and_Requirements", "Roles & Reqs", "pages/2_Roles_and_Requirements.py"),
    ("Employees", "Employees", "pages/3_Employees.py"),
    ("Generate_Onboarding", "Generate", "pages/4_Generate_Onboarding.py"),
    ("Validation_Review", "Validation", "pages/5_Validation_Review.py"),
    ("Admin_Dashboard", "Admin", "pages/6_Admin_Dashboard.py"),
    ("Employee_Dashboard", "Employee Dashboard", "pages/7_Employee_Dashboard.py"),
]


def _clean(html: str) -> str:
    """Strips per-line leading/trailing whitespace from a multi-line HTML
    string before handing it to st.markdown(). This matters because Python's
    indentation inside functions/if-blocks otherwise leaves 4+ leading spaces
    on each line, which Markdown's parser interprets as a code block —
    causing raw HTML tags to be displayed as literal text instead of being
    rendered. Always route multi-line HTML through this before markdown()."""
    return "\n".join(line.strip() for line in html.strip().splitlines())


def inject(authenticated: bool = True):
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Inter:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {{ font-family: 'Inter', -apple-system, sans-serif; }}

        .stApp {{
            background:
                radial-gradient(circle at 15% 0%, rgba(201,162,39,0.06) 0%, transparent 45%),
                linear-gradient(180deg, {CHARCOAL} 0%, #08080B 100%);
            color: {TEXT};
        }}

        * {{ scrollbar-width: thin; scrollbar-color: {GOLD} {CARD}; }}
        ::-webkit-scrollbar {{ width: 10px; height: 10px; }}
        ::-webkit-scrollbar-track {{ background: {CHARCOAL}; }}
        ::-webkit-scrollbar-thumb {{ background: linear-gradient(180deg, {GOLD}, #7A611A); border-radius: 999px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: {GOLD_SOFT}; }}

        /* ---- Fully remove every native Streamlit chrome element: the
           hamburger/"..." menu, the Deploy button, the running-man status
           widget and the top decoration bar — this app has its own navbar. */
        #MainMenu {{ display: none !important; visibility: hidden !important; }}
        footer {{ display: none !important; visibility: hidden !important; }}
        header[data-testid="stHeader"] {{ display: none !important; background: transparent; }}
        div[data-testid="stToolbar"] {{ display: none !important; visibility: hidden !important; }}
        div[data-testid="stDecoration"] {{ display: none !important; }}
        div[data-testid="stStatusWidget"] {{ display: none !important; }}
        a[data-testid="stAppDeployButton"], button[data-testid="stAppDeployButton"] {{ display: none !important; }}
        div[data-testid="stAppViewBlockContainer"], div[data-testid="stMainBlockContainer"] {{ padding-top: 1.4rem !important; }}
        #stDecoration {{ display: none !important; }}

        /* ---- Hide Streamlit's auto-generated page list; we render our own
           grouped, role-aware navigation inside st.sidebar instead. ---- */
        div[data-testid="stSidebarNav"] {{ display: none !important; }}

        /* ---- Fixed, premium sidebar: stays in place while the page
           content scrolls, like a dashboard rail rather than a page block. ---- */
        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, {CARD} 0%, #101018 100%) !important;
            border-right: 1px solid {CARD_BORDER};
            position: sticky !important; top: 0; height: 100vh !important;
            min-width: 290px !important; max-width: 290px !important;
        }}
        section[data-testid="stSidebar"] > div {{
            padding-top: 0.8rem; height: 100%; overflow-y: auto; overflow-x: hidden;
        }}
        section[data-testid="stSidebar"] div[data-testid="stPageLink"] {{
            border-radius: 10px; margin-bottom: 0.3rem; overflow: hidden;
        }}
        section[data-testid="stSidebar"] div[data-testid="stPageLink"] p {{
            font-size: 0.92rem !important;
        }}
        /* Gold sliding-accent hover/active state for every sidebar link */
        section[data-testid="stSidebar"] div[data-testid="stPageLink"] a {{
            padding: 0.7rem 0.85rem !important; font-size: 0.92rem !important;
            border-radius: 10px !important; position: relative; border: 1px solid transparent;
            transition: background .28s cubic-bezier(.4,0,.2,1), color .28s ease,
                        border-color .28s ease, box-shadow .28s ease, padding-left .28s ease;
        }}
        section[data-testid="stSidebar"] div[data-testid="stPageLink"] a::before {{
            content: ""; position: absolute; left: 0; top: 12%; bottom: 12%; width: 3px;
            border-radius: 0 3px 3px 0; background: linear-gradient(180deg, {GOLD_SOFT}, {GOLD});
            transform: scaleY(0); transition: transform .28s ease;
        }}
        section[data-testid="stSidebar"] div[data-testid="stPageLink"] a:hover {{
            background: linear-gradient(90deg, rgba(201,162,39,0.16), rgba(201,162,39,0.03)) !important;
            color: {GOLD_SOFT} !important; padding-left: 1.1rem !important;
        }}
        section[data-testid="stSidebar"] div[data-testid="stPageLink"] a:hover::before {{ transform: scaleY(1); }}
        section[data-testid="stSidebar"] div[data-testid="stPageLink"] a[aria-current="page"] {{
            background: linear-gradient(90deg, rgba(201,162,39,0.22), rgba(201,162,39,0.05)) !important;
            color: {GOLD_SOFT} !important; font-weight: 700 !important;
            box-shadow: inset 0 0 0 1px rgba(201,162,39,0.25);
        }}
        section[data-testid="stSidebar"] div[data-testid="stPageLink"] a[aria-current="page"]::before {{ transform: scaleY(1); }}
        .ss-sidebar-brand {{
            font-family: 'Playfair Display', serif; font-weight: 700; color: {GOLD_SOFT};
            font-size: 1.35rem; padding: 0.5rem 0.3rem 1.3rem; letter-spacing: 0.3px;
            display: flex; align-items: center; gap: 0.5rem;
        }}
        .ss-sidebar-section {{
            color: {MUTED}; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 1px;
            font-weight: 700; margin: 1.2rem 0 0.5rem 0.5rem;
        }}
        .ss-sidebar-user {{
            display: flex; align-items: center; gap: 0.6rem; padding: 0.8rem 0.5rem;
            border-top: 1px solid {CARD_BORDER}; margin-top: 0.8rem;
            background: rgba(201,162,39,0.05); border-radius: 10px;
        }}

        /* ---- Edge-to-edge layout: no dead black gutters on wide screens ---- */
        html, body {{ overflow-x: hidden; }}
        div[data-testid="stAppViewContainer"] {{ width: 100%; }}
        .main .block-container {{
            max-width: 1600px; width: 96%; margin: 0 auto;
            padding-top: 1.2rem; padding-bottom: 2.5rem;
            padding-left: clamp(1rem, 2vw, 2.4rem); padding-right: clamp(1rem, 2vw, 2.4rem);
            animation: ssFadeIn .35s ease both;
        }}
        @keyframes ssFadeIn {{
            from {{ opacity: 0; transform: translateY(6px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        @media (min-width: 1900px) {{
            .main .block-container {{ max-width: 1800px; }}
        }}

        /* ---- Logged-out pages (login / register): there is no sidebar
           navigation to show, so fully remove the sidebar column and its
           collapse arrow — otherwise Streamlit reserves an empty black
           strip on the left even when nothing is rendered inside it. The
           content area is then free to use the full browser width. ---- */
        /* ---- Logged-out pages (login / register): there is no sidebar
           navigation to show, so fully remove the sidebar column and its
           collapse arrow — otherwise Streamlit reserves an empty black
           strip on the left even when nothing is rendered inside it. The
           content area is then free to use the full browser width. Every
           known Streamlit testid for the sidebar + its collapsed rail is
           targeted here so this holds across Streamlit versions. ---- */
        {"" if authenticated else '''
        section[data-testid="stSidebar"],
        div[data-testid="stSidebarCollapsedControl"],
        button[data-testid="stSidebarCollapsedControl"],
        div[data-testid="collapsedControl"],
        [data-testid="stSidebarContent"] {
            display: none !important; width: 0 !important; min-width: 0 !important; max-width: 0 !important;
        }
        div[data-testid="stAppViewContainer"] { margin-left: 0 !important; }
        div[data-testid="stAppViewContainer"] > .main,
        section.main {
            margin-left: 0 !important; width: 100% !important; max-width: 100% !important;
        }
        '''}

        h1, h2, h3 {{ font-family: 'Playfair Display', serif !important; color: {TEXT} !important; letter-spacing: 0.3px; }}

        /* ---- Big display headings get the signature gold gradient treatment ---- */
        .ss-hero h1 {{
            background: linear-gradient(100deg, {GOLD_SOFT} 0%, {GOLD} 45%, #FFF6DD 75%, {GOLD_SOFT} 100%);
            -webkit-background-clip: text; background-clip: text; color: transparent !important;
        }}
        .ss-logo-text {{
            background: linear-gradient(100deg, {GOLD_SOFT} 0%, {GOLD} 55%, #FFF6DD 100%);
            -webkit-background-clip: text; background-clip: text; color: transparent !important;
            font-family: 'Playfair Display', serif; font-weight: 700; font-size: 1.15rem;
            white-space: nowrap; letter-spacing: 0.2px;
        }}

        /* ---- Top navbar (built from st.container(border=True) + st.page_link widgets) ---- */
        .ss-navbar-status {{
            display: inline-flex; align-items: center; gap: 0.35rem;
            background: rgba(46,158,107,0.12); color: {SUCCESS};
            border: 1px solid {SUCCESS}; border-radius: 999px;
            padding: 0.15rem 0.6rem; font-size: 0.68rem; font-weight: 700; letter-spacing: 0.5px;
        }}
        .ss-navbar-status .dot {{
            width: 6px; height: 6px; border-radius: 50%; background: {SUCCESS};
            box-shadow: 0 0 6px {SUCCESS};
        }}
        /* Style native st.page_link widgets to look like nav pills */
        div[data-testid="stPageLink"] {{
            padding: 0 !important;
        }}
        div[data-testid="stPageLink"] a {{
            color: {MUTED} !important; text-decoration: none !important; font-size: 0.76rem !important;
            font-weight: 600 !important; padding: 0.45rem 0.4rem !important; border-radius: 8px !important;
            transition: background-color .25s ease, color .25s ease, box-shadow .25s ease, transform .12s ease;
            justify-content: center !important; white-space: nowrap !important; overflow: visible !important;
            position: relative;
        }}
        div[data-testid="stPageLink"] a p {{
            font-size: 0.76rem !important; white-space: nowrap !important; overflow: visible !important;
        }}
        div[data-testid="stPageLink"] a:hover {{
            color: {TEXT} !important; background: rgba(201,162,39,0.12) !important;
        }}
        div[data-testid="stPageLink"] a:active {{
            transform: scale(0.95); background: rgba(201,162,39,0.3) !important; color: {GOLD_SOFT} !important;
        }}
        div[data-testid="stPageLink"] a[aria-current="page"] {{
            color: {CHARCOAL} !important; background: linear-gradient(135deg, {GOLD_SOFT}, {GOLD}) !important;
            font-weight: 700 !important; box-shadow: 0 2px 12px rgba(201,162,39,0.35);
        }}
        @media (max-width: 1100px) {{
            div[data-testid="stPageLink"] a, div[data-testid="stPageLink"] a p {{ font-size: 0.66rem !important; padding: 0.4rem 0.25rem !important; }}
        }}

        /* ---- Sticky, glassy top navbar ---- */
        #ss-navbar-anchor + div[data-testid="stVerticalBlockBorderWrapper"] {{
            position: sticky; top: 0; z-index: 999;
            background: rgba(11,11,15,0.82) !important;
            backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
            box-shadow: 0 4px 24px rgba(0,0,0,0.35);
        }}

        /* ---- Buttons ---- */
        .stButton > button, .stFormSubmitButton > button {{
            background: linear-gradient(135deg, {GOLD} 0%, #9C7C1B 100%);
            color: #14140F; font-weight: 700; border: none; border-radius: 8px;
            padding: 0.55rem 1.4rem; letter-spacing: 0.3px; transition: all 0.15s ease;
            box-shadow: 0 2px 10px rgba(201, 162, 39, 0.18);
        }}
        .stButton > button:hover, .stFormSubmitButton > button:hover {{
            box-shadow: 0 4px 16px rgba(201, 162, 39, 0.4); transform: translateY(-1px); color: #14140F;
        }}

        /* ---- Native Streamlit metric (fallback use) ---- */
        div[data-testid="stMetric"] {{
            background: {CARD}; border: 1px solid {CARD_BORDER}; border-left: 3px solid {GOLD};
            border-radius: 10px; padding: 1rem 1.2rem;
        }}
        div[data-testid="stMetricLabel"] {{ color: {MUTED} !important; font-size: 0.78rem !important; text-transform: uppercase; letter-spacing: 0.6px; }}
        div[data-testid="stMetricValue"] {{ color: {GOLD_SOFT} !important; font-family: 'Playfair Display', serif !important; }}

        /* ---- Native bordered containers (st.container(border=True)) styled as premium panels ---- */
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background: {CARD} !important; border: 1px solid {CARD_BORDER} !important;
            border-radius: 12px !important;
        }}

        /* ---- Tabs ---- */
        .stTabs [data-baseweb="tab-list"] {{ gap: 4px; border-bottom: 1px solid {CARD_BORDER}; }}
        .stTabs [data-baseweb="tab"] {{ background: transparent; color: {MUTED}; border-radius: 8px 8px 0 0; padding: 0.5rem 1.1rem; }}
        .stTabs [aria-selected="true"] {{ background: {CARD} !important; color: {GOLD} !important; border-bottom: 2px solid {GOLD} !important; }}

        /* ---- Expanders ---- */
        div[data-testid="stExpander"] {{
            background: {CARD}; border: 1px solid {CARD_BORDER}; border-radius: 10px;
            transition: border-color .2s ease, box-shadow .2s ease;
        }}
        div[data-testid="stExpander"]:hover {{ border-color: {GOLD}; box-shadow: 0 2px 14px rgba(201,162,39,0.1); }}

        /* ---- Inputs ---- */
        .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"],
        .stDateInput input, .stNumberInput input {{
            background-color: #1B1B24 !important; color: {TEXT} !important;
            border: 1px solid {CARD_BORDER} !important; border-radius: 8px !important;
            transition: border-color .2s ease, box-shadow .2s ease;
        }}
        .stTextInput input:focus, .stTextArea textarea:focus {{ border-color: {GOLD} !important; box-shadow: 0 0 0 1px {GOLD} !important; }}

        /* ---- Dataframes ---- */
        div[data-testid="stDataFrame"] {{ border: 1px solid {CARD_BORDER}; border-radius: 10px; overflow: hidden; }}

        /* ---- Progress ---- */
        div[data-testid="stProgress"] div[role="progressbar"] > div {{
            background: linear-gradient(90deg, {GOLD} 0%, {GOLD_SOFT} 100%) !important;
            transition: width .4s ease;
        }}

        /* ---- Native alert boxes (st.success / st.warning / st.error / st.info) ---- */
        div[data-testid="stAlertContentSuccess"] {{ color: {SUCCESS} !important; }}
        div[data-testid="stAlertContentWarning"] {{ color: {WARNING} !important; }}
        div[data-testid="stAlertContentError"] {{ color: {DANGER} !important; }}
        div[data-testid="stAlertContentInfo"] {{ color: {INFO} !important; }}
        div[data-testid="stAlert"] {{
            border-radius: 10px !important; border: 1px solid {CARD_BORDER} !important;
            animation: ssFadeIn .3s ease both;
        }}

        /* ---- Spinner ---- */
        div[data-testid="stSpinner"] > div {{ border-top-color: {GOLD} !important; }}

        /* ---- Custom static building blocks (all single-call) ---- */
        .ss-card {{
            background: {CARD}; border: 1px solid {CARD_BORDER}; border-radius: 12px;
            padding: 1.3rem 1.5rem; margin-bottom: 1rem;
            transition: border-color .2s ease, box-shadow .2s ease, transform .2s ease;
        }}
        .ss-card:hover {{ border-color: {GOLD}; box-shadow: 0 6px 20px rgba(201,162,39,0.12); transform: translateY(-2px); }}
        .ss-hero {{
            background: radial-gradient(circle at top left, #1A1A24 0%, {CHARCOAL} 70%);
            border: 1px solid {CARD_BORDER}; border-radius: 14px; padding: 2.2rem 2.4rem; margin-bottom: 1.4rem;
        }}
        .ss-badge {{ display: inline-block; padding: 0.25rem 0.75rem; border-radius: 999px; font-size: 0.76rem; font-weight: 700; letter-spacing: 0.3px; }}
        .ss-badge-gold {{ background: rgba(201,162,39,0.14); color: {GOLD_SOFT}; border: 1px solid {GOLD}; }}
        .ss-badge-success {{ background: rgba(46,158,107,0.14); color: {SUCCESS}; border: 1px solid {SUCCESS}; }}
        .ss-badge-warning {{ background: rgba(201,162,39,0.14); color: {WARNING}; border: 1px solid {WARNING}; }}
        .ss-badge-danger {{ background: rgba(192,69,61,0.14); color: {DANGER}; border: 1px solid {DANGER}; }}
        .ss-muted {{ color: {MUTED}; font-size: 0.9rem; }}
        .ss-divider {{ border: none; border-top: 1px solid {CARD_BORDER}; margin: 1.3rem 0; }}

        /* ---- Metric card grid (reference-style: icon chip + big value + trend) ---- */
        .ss-metric {{
            background: {CARD}; border: 1px solid {CARD_BORDER}; border-radius: 12px;
            padding: 1.1rem 1.3rem; position: relative; overflow: hidden;
        }}
        .ss-metric::before {{
            content: ""; position: absolute; top: 0; left: 0; right: 0; height: 3px;
        }}
        .ss-metric {{ transition: transform .2s ease, box-shadow .2s ease; }}
        .ss-metric:hover {{ transform: translateY(-3px); box-shadow: 0 8px 22px rgba(201,162,39,0.14); }}
        .ss-metric-icon {{
            position: absolute; top: 1rem; right: 1rem; width: 30px; height: 30px; border-radius: 8px;
            display: flex; align-items: center; justify-content: center; font-size: 0.95rem;
        }}
        .ss-metric-label {{ color: {MUTED}; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.6px; font-weight: 700; }}
        .ss-metric-value {{ font-family: 'Playfair Display', serif; font-size: 1.9rem; font-weight: 700; margin: 0.25rem 0 0.15rem; }}
        .ss-metric-sub {{ font-size: 0.78rem; color: {MUTED}; }}

        /* ---- Progress bar rows (ML pipeline style) ---- */
        .ss-progress-row {{ margin-bottom: 0.9rem; }}
        .ss-progress-row .row-top {{ display: flex; justify-content: space-between; font-size: 0.82rem; margin-bottom: 0.35rem; }}
        .ss-progress-track {{ height: 6px; background: #1E1E28; border-radius: 999px; overflow: hidden; }}
        .ss-progress-fill {{ height: 100%; border-radius: 999px; }}
    </style>
    """, unsafe_allow_html=True)


SIDEBAR_SECTIONS = [
    ("Setup", [
        ("Documents", "📤  Documents", "pages/1_Documents.py", None),
        ("Roles_and_Requirements", "🗂  Roles & Requirements", "pages/2_Roles_and_Requirements.py", None),
        ("Employees", "👥  Employees", "pages/3_Employees.py", None),
    ]),
    ("Generate & Review", [
        ("Generate_Onboarding", "✨  Generate Onboarding", "pages/4_Generate_Onboarding.py", None),
        ("Validation_Review", "⚖  Validation & Review", "pages/5_Validation_Review.py", None),
    ]),
    ("Insights", [
        ("Admin_Dashboard", "📊  Admin Dashboard", "pages/6_Admin_Dashboard.py", ("admin", "training_manager", "reviewer")),
        ("Employee_Dashboard", "🎯  Employee Dashboard", "pages/7_Employee_Dashboard.py", ("employee", "manager", "admin", "training_manager", "reviewer")),
    ]),
]


def sidebar_nav(active: str, username: str = "", role: str = ""):
    """Renders the app's grouped, role-aware navigation inside Streamlit's
    native left sidebar (st.page_link keeps session_state intact across
    clicks — no full page reload)."""
    role_key = (role or "").lower().replace(" ", "_")
    with st.sidebar:
        st.markdown(_clean("""
            <div class="ss-sidebar-brand">
                <span style="width:34px; height:34px; border-radius:10px; flex-shrink:0;
                    background:linear-gradient(135deg,#E4C766,#C9A227 55%,#7A611A);
                    display:inline-flex; align-items:center; justify-content:center;
                    font-size:1.1rem; color:#14140F; box-shadow:0 4px 14px rgba(201,162,39,0.35);">◆</span>
                <span>SkillSprint AI</span>
            </div>
        """), unsafe_allow_html=True)
        st.page_link("app.py", label="🏠  Home", use_container_width=True)
        for section_title, items in SIDEBAR_SECTIONS:
            visible = [it for it in items if it[3] is None or role_key in it[3]]
            if not visible:
                continue
            st.markdown(f'<div class="ss-sidebar-section">{section_title}</div>', unsafe_allow_html=True)
            for key, label, target, _roles in visible:
                st.page_link(target, label=label, use_container_width=True)

        if username:
            initial = (username or "?")[0].upper()
            display_name = st.session_state.get("full_name") or username
            st.markdown(_clean(f"""
                <div class="ss-sidebar-user">
                    <div style="width:32px; height:32px; border-radius:50%; background:linear-gradient(135deg,#C9A227,#7A611A);
                                display:flex; align-items:center; justify-content:center; font-weight:700; color:#14140F; font-size:0.85rem; flex-shrink:0;">{initial}</div>
                    <div style="line-height:1.15; overflow:hidden;">
                        <div style="font-weight:700; font-size:0.82rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{display_name}</div>
                        <div style="font-size:0.7rem; color:#E4C766; text-transform:uppercase; letter-spacing:0.4px;">{role}</div>
                    </div>
                </div>
            """), unsafe_allow_html=True)

            with st.expander("✏️  Update Profile"):
                from utils.api_client import update_profile
                with st.form("ss_update_profile_form"):
                    new_full_name = st.text_input("Full Name", value=st.session_state.get("full_name", ""))
                    new_employee_id = None
                    if role_key == "employee":
                        new_employee_id = st.text_input(
                            "Linked Employee ID",
                            value=st.session_state.get("employee_id", ""),
                            placeholder="e.g. EMP-08d7da2c6d — ask your admin",
                            help="This links your login to your employee profile so your dashboard only shows your own onboarding progress.",
                        )
                    st.markdown('<div class="ss-muted" style="font-size:0.75rem; margin-top:0.4rem;">Leave the fields below empty to keep your current password.</div>', unsafe_allow_html=True)
                    cur_pw = st.text_input("Current Password", type="password", key="ss_up_cur_pw")
                    new_pw = st.text_input("New Password", type="password", key="ss_up_new_pw")
                    new_pw_confirm = st.text_input("Confirm New Password", type="password", key="ss_up_new_pw2")
                    save_clicked = st.form_submit_button("Save Changes", use_container_width=True, type="primary")

                    if save_clicked:
                        if new_pw or new_pw_confirm or cur_pw:
                            if new_pw != new_pw_confirm:
                                st.error("New passwords do not match.")
                            elif not cur_pw:
                                st.error("Enter your current password to set a new one.")
                            elif len(new_pw) < 6:
                                st.error("New password must be at least 6 characters.")
                            else:
                                ok, data = update_profile(new_full_name, cur_pw, new_pw, employee_id=new_employee_id)
                                if ok:
                                    st.success("Profile updated.")
                                    st.rerun()
                                else:
                                    st.error(f"Update failed: {data}")
                        else:
                            ok, data = update_profile(new_full_name, employee_id=new_employee_id)
                            if ok:
                                st.success("Profile updated.")
                                st.rerun()
                            else:
                                st.error(f"Update failed: {data}")

            if st.button("↪  Sign Out", use_container_width=True, key="ss_sidebar_logout"):
                from utils.api_client import logout
                logout()
                st.rerun()


def topnav(active: str, authenticated: bool, username: str = "", role: str = ""):
    """Renders the grouped left-sidebar navigation for authenticated pages.
    st.page_link is used everywhere (never raw <a href>) because raw anchors
    force a full browser reload, which would wipe Streamlit's session_state
    and silently log the user out.

    There used to also be a bordered top bar here repeating the brand name
    and the username/avatar — but the sidebar already shows the brand at
    the top and the user's name/role/avatar in its own card at the bottom,
    so that strip was pure duplication (and looked like a stray empty box
    with no content on the login screen). It has been removed entirely;
    the sidebar is now the single source of navigation and identity."""
    if authenticated:
        sidebar_nav(active, username, role)


def hero(title: str, subtitle: str = "", eyebrow: str = ""):
    eyebrow_html = f'<div class="ss-muted" style="letter-spacing:2px; text-transform:uppercase; margin-bottom:0.4rem;">{eyebrow}</div>' if eyebrow else ""
    st.markdown(_clean(f"""
        <div class="ss-hero">
            {eyebrow_html}
            <h1 style="margin:0; border:none; padding:0;">{title}</h1>
            <p class="ss-muted" style="margin-top:0.6rem; font-size:1.02rem;">{subtitle}</p>
        </div>
    """), unsafe_allow_html=True)


def badge(text: str, kind: str = "gold") -> str:
    return f'<span class="ss-badge ss-badge-{kind}">{text}</span>'


def status_badge_kind(status: str) -> str:
    mapping = {
        "Verified": "success",
        "Verified with Warning": "warning",
        "Partially Verified": "warning",
        "Requirement Missing": "danger",
        "Unsupported Requirement": "danger",
        "Contradiction Detected": "danger",
        "Manual Review Required": "danger",
    }
    return mapping.get(status, "gold")


def card(content_html: str):
    """A single self-contained bordered card. Pass the full inner HTML."""
    st.markdown(_clean(f'<div class="ss-card">{content_html}</div>'), unsafe_allow_html=True)


def card_start():
    """DEPRECATED no-op — kept so old calls don't crash. See card()."""
    pass


def card_end():
    """DEPRECATED no-op — see card()."""
    pass


def icon_circle(icon: str, size: str = "3rem", accent: str = None) -> str:
    accent = accent or GOLD
    return _clean(f"""<div style="width:{size}; height:{size}; min-width:{size};
        border-radius:14px; background:linear-gradient(135deg, rgba(201,162,39,0.22), rgba(201,162,39,0.05));
        border:1px solid {accent}; display:flex; align-items:center;
        justify-content:center; font-size:calc({size} * 0.5); box-shadow: 0 4px 14px rgba(201,162,39,0.1);">{icon}</div>""")


def metric_card(icon: str, label: str, value: str, sub: str = "", accent: str = GOLD):
    """Reference-style metric card: colored top accent, icon chip, big value, trend line."""
    st.markdown(_clean(f"""
        <div class="ss-metric" style="border-top: 3px solid {accent};">
            <div class="ss-metric-icon" style="background: rgba(201,162,39,0.12); border:1px solid {accent}; color:{accent};">{icon}</div>
            <div class="ss-metric-label">{label}</div>
            <div class="ss-metric-value" style="color:{accent};">{value}</div>
            <div class="ss-metric-sub">{sub}</div>
        </div>
    """), unsafe_allow_html=True)


def progress_row(label: str, pct: float, right_text: str = None, color: str = GOLD):
    right_text = right_text if right_text is not None else f"{pct}%"
    pct = max(0, min(100, pct))
    st.markdown(_clean(f"""
        <div class="ss-progress-row">
            <div class="row-top"><span>{label}</span><span style="color:{color}; font-weight:700;">{right_text}</span></div>
            <div class="ss-progress-track"><div class="ss-progress-fill" style="width:{pct}%; background:linear-gradient(90deg,{color},{GOLD_SOFT});"></div></div>
        </div>
    """), unsafe_allow_html=True)


def panel_header(icon: str, title: str, badge_text: str = None, badge_kind: str = "success"):
    badge_html = f'<span class="ss-badge ss-badge-{badge_kind}">{badge_text}</span>' if badge_text else ""
    st.markdown(_clean(f"""
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:1rem;">
            <div style="display:flex; align-items:center; gap:0.6rem;">
                <span style="font-size:1.1rem;">{icon}</span>
                <span style="font-weight:700; font-size:0.95rem; letter-spacing:0.3px;">{title}</span>
            </div>
            {badge_html}
        </div>
    """), unsafe_allow_html=True)


def divider():
    st.markdown('<hr class="ss-divider">', unsafe_allow_html=True)
