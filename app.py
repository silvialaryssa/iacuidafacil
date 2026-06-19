from __future__ import annotations

import streamlit as st

from config.settings import admin_email
from services.analytics_service import get_analytics_service
from services.app_service import record_session_once
from ui.admin import render_admin
from ui.auth import render_auth_section
from ui.components import load_css
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


with st.sidebar:
    st.title("🌿iACuidaFácil")
    st.caption("Planta com IA, rotinas e acompanhamento.")
    st.divider()

    if "user" not in st.session_state:
        st.caption("Use a tela principal, na aba 'Entrar', para acessar sua conta ou se cadastrar.")

    else:
        user = st.session_state["user"]
        st.success(f"Logado como {user.get('nome', '')}")
        st.caption(user.get("email", ""))

        is_admin_sidebar = user.get("email", "").strip().lower() == admin_email()
        page_options = ["🏠 Sua Rotina", "🗓️ Calendário", "📈 Evolução", "🌱 Planta com IA"]
        if is_admin_sidebar:
            page_options.insert(2, "🧪 Admin")

        current_page = st.session_state.get("page", "🏠 Sua Rotina")
        if current_page not in page_options:
            current_page = "🏠 Sua Rotina"

        st.session_state["page"] = st.radio(
            "Navegação",
            page_options,
            index=page_options.index(current_page),
        )

        if st.button("Sair"):
            for key in [
                "user",
                "session_recorded",
                "login_message",
                "page",
                "auth_user_id",
                "auth_access_token",
                "auth_refresh_token",
                "last_tracked_section_access",
            ]:
                st.session_state.pop(key, None)
            st.rerun()

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

st.info("⬅️ Use o menu lateral para navegar entre as seções (Sua Rotina, Calendário, Evolução, Planta com IA).")

page = st.session_state.get("page", "🏠 Sua Rotina")
is_admin = user.get("email", "").strip().lower() == admin_email()
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
