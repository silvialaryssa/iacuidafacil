from __future__ import annotations

import streamlit as st

from config.settings import admin_email
from services.analytics_service import get_analytics_service
from services.app_service import record_session_once
from ui.admin import render_admin
from ui.auth import render_auth_section
from ui.components import load_css, render_top_nav
from ui.calendar import render_calendar
from ui.home import render_home
from ui.landing import render_landing
from ui.plant_ai import render_plant_ai
from ui.progress import render_progress


st.set_page_config(
    page_title="iACuidaFácil",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="collapsed",
)

try:
    st.markdown("""
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#4F6F52">
    <script>
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.register("/service-worker.js").catch(function(error) {
        console.log("Service Worker não registrado:", error);
      });
    }
    </script>
    """, unsafe_allow_html=True)
except Exception:
    pass

load_css()


def track_section_access_once(page_name: str, email: str = "") -> None:
    analytics = get_analytics_service()
    methods_by_page = {
        "🏠 Sua Rotina": "track_hoje_access",
        "🗓️ Calendário": "track_calendario_access",
        "📈 Evolução": "track_evolucao_access",
        "🌱 Planta com IA": "track_planta_ia_access",
        "🧪 Admin": "track_admin_access",
    }

    method_name = methods_by_page.get(page_name)
    if not method_name:
        return

    signature = f"section:{page_name}:{email}"
    if st.session_state.get("last_tracked_section_access") == signature:
        return

    track_method = getattr(analytics, method_name, None)
    if callable(track_method):
        track_method(email=email)
        st.session_state["last_tracked_section_access"] = signature


st.title("🌿 iACuidaFácil")
#st.caption("Cuide da planta com IA e acompanhe suas atividades do dia a dia.")

if st.session_state.get("login_message"):
    st.success(st.session_state.pop("login_message"))

if "user" not in st.session_state:
    nav_options = ["Landing", "Entrar"]
    nav_default = st.session_state.get("nav_page", nav_options[0])

    page = st.radio(
        "Antes de começar",
        nav_options,
        index=nav_options.index(nav_default) if nav_default in nav_options else 0,
        horizontal=True,
        label_visibility="collapsed",
    )
    st.session_state["nav_page"] = page

    if page == "Landing":
        render_landing()
    else:
        render_auth_section()

    st.stop()

user = st.session_state["user"]
record_session_once(user)

is_admin = user.get("email", "").strip().lower() == admin_email()
selected = render_top_nav(user, is_admin)

if selected == "🚪 Sair":
    for key in [
        "user",
        "session_recorded",
        "login_message",
        "page",
        "nav_page",
        "auth_user_id",
        "auth_access_token",
        "auth_refresh_token",
        "last_tracked_section_access",
    ]:
        st.session_state.pop(key, None)
    st.rerun()

st.session_state["page"] = selected
page = selected
track_section_access_once(page, email=user.get("email", ""))

if page == "🏠 Sua Rotina":
    render_home(user)
elif page == "🗓️ Calendário":
    render_calendar(user)
elif page == "📈 Evolução":
    render_progress(user)
elif page == "🌱 Planta com IA":
    render_plant_ai(user)
elif page == "🧪 Admin" and is_admin:
    render_admin(user)
else:
    render_home(user)
