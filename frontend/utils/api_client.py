import os
import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def _headers():
    token = st.session_state.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def login(username: str, password: str):
    resp = requests.post(f"{BACKEND_URL}/auth/login", data={"username": username, "password": password})
    if resp.status_code == 200:
        data = resp.json()
        st.session_state["token"] = data["access_token"]
        st.session_state["role"] = data["role"]
        st.session_state["username"] = data["username"]
        ok_me, me_data = get_me()
        if ok_me and me_data.get("full_name"):
            st.session_state["full_name"] = me_data["full_name"]
        return True, data
    return False, resp.json().get("detail", "Login failed")


def register(username: str, password: str, role: str = "employee", full_name: str = None):
    resp = requests.post(
        f"{BACKEND_URL}/auth/register",
        json={"username": username, "password": password, "role": role, "full_name": full_name},
    )
    if resp.status_code == 200:
        return True, resp.json()
    try:
        return False, resp.json().get("detail", "Registration failed")
    except Exception:
        return False, "Registration failed"


def logout():
    for key in ("token", "role", "username", "full_name"):
        st.session_state.pop(key, None)


def get_me():
    resp = requests.get(f"{BACKEND_URL}/auth/me", headers=_headers())
    if resp.status_code == 200:
        return True, resp.json()
    return False, None


def update_profile(full_name: str = None, current_password: str = None, new_password: str = None):
    payload = {}
    if full_name is not None:
        payload["full_name"] = full_name
    if new_password:
        payload["current_password"] = current_password
        payload["new_password"] = new_password
    resp = requests.put(f"{BACKEND_URL}/auth/me", headers=_headers(), json=payload)
    if resp.status_code == 200:
        data = resp.json()
        if "full_name" in data:
            st.session_state["full_name"] = data["full_name"]
        return True, data
    try:
        return False, resp.json().get("detail", "Update failed")
    except Exception:
        return False, "Update failed"


def api_get(path: str, params: dict = None):
    resp = requests.get(f"{BACKEND_URL}{path}", headers=_headers(), params=params)
    return resp


def api_post(path: str, json: dict = None, data: dict = None, files=None):
    resp = requests.post(f"{BACKEND_URL}{path}", headers=_headers(), json=json, data=data, files=files)
    return resp


def api_delete(path: str):
    resp = requests.delete(f"{BACKEND_URL}{path}", headers=_headers())
    return resp


def require_login():
    if "token" not in st.session_state:
        st.session_state["_redirect_notice"] = "Please sign in to continue."
        st.switch_page("app.py")
        st.stop()


def require_role(*roles):
    require_login()
    if st.session_state.get("role") not in roles:
        st.error(f"Access denied. Your role '{st.session_state.get('role')}' cannot view this page.")
        st.page_link("app.py", label="⟵ Back to Home")
        st.stop()
