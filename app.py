from __future__ import annotations

import streamlit as st

from config.settings import admin_email
from services.analytics_service import get_analytics_service
from services.auth_service import sign_in_with_email_password, sign_up_with_email_password
from services.app_service import (
    ensure_user_profile,
    is_valid_email,
    record_session_once,
)
from ui.admin import render_admin
from ui.components import load_css
from ui.calendar import render_calendar
from ui.home import render_home
from ui.landing import render_landing
from ui.plant_ai import render_plant_ai
from ui.progress import render_progress
from ui.setup import render_setup


st.set_page_config(
    page_title="CuidaFácil",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="collapsed",
)

load_css()


def track_page_once(page_name: str, email: str = "", page_group: str = "public") -> None:
    analytics = get_analytics_service()
    signature = f"{page_group}:{page_name}:{email}"
    if st.session_state.get("last_tracked_page") == signature:
        return

    if hasattr(analytics, "track_page_view"):
        analytics.track_page_view(page_name, email=email, params={"page_group": page_group})
    else:
        analytics.track(
            "page_view",
            email=email,
            params={
                "page_title": page_name,
                "page_name": page_name,
                "page_group": page_group,
            },
        )
    st.session_state["last_tracked_page"] = signature


def track_section_access_once(page_name: str, email: str = "") -> None:
    analytics = get_analytics_service()
    methods_by_page = {
        "🏠 Hoje": "track_hoje_access",
        "🗓️ Calendário": "track_calendario_access",
        "📈 Evolução": "track_evolucao_access",
        "🌱 Planta com IA": "track_planta_ia_access",
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
    st.title("CuidaFácil")
    st.caption("Planta com IA, rotina e acompanhamento.")
    st.divider()

    if "user" not in st.session_state:
        st.markdown("### Acesso")

        tipo_acesso = st.radio(
            "Como deseja acessar?",
            ["Já tenho cadastro", "Quero me cadastrar"],
            index=0,
        )

        if tipo_acesso == "Já tenho cadastro":
            with st.form("login_existente_form"):
                email_login = st.text_input(
                    "E-mail cadastrado",
                    placeholder="seuemail@exemplo.com",
                    max_chars=120,
                )
                senha_login = st.text_input(
                    "Senha",
                    type="password",
                    max_chars=128,
                )
                entrar = st.form_submit_button("Entrar")

            if entrar:
                email_limpo = email_login.strip().lower()
                senha_limpa = senha_login.strip()

                if not is_valid_email(email_limpo):
                    st.warning("Informe um e-mail válido.")
                elif not senha_limpa:
                    st.warning("Informe sua senha.")
                else:
                    with st.spinner("Entrando..."):
                        auth_result = sign_in_with_email_password(
                            email=email_limpo,
                            password=senha_limpa,
                        )

                    if not auth_result.get("ok"):
                        st.error(str(auth_result.get("message", "Falha ao autenticar.")))
                    else:
                        with st.spinner("Carregando seus dados..."):
                            user = ensure_user_profile(email=auth_result.get("email", email_limpo))

                        if user is None:
                            st.error(
                                "Falha ao carregar seu perfil local. "
                                "Tente novamente em instantes."
                            )
                        else:
                            st.session_state["user"] = user
                            st.session_state["nome"] = user.get("nome", "")
                            st.session_state["email"] = user.get("email", email_limpo)
                            st.session_state["auth_user_id"] = auth_result.get("auth_user_id", "")
                            st.session_state["auth_access_token"] = auth_result.get("access_token", "")
                            st.session_state["auth_refresh_token"] = auth_result.get("refresh_token", "")
                            st.session_state["session_recorded"] = False
                            st.session_state["page"] = "🏠 Hoje"
                            st.session_state["login_message"] = (
                                f"Bem-vindo de volta, {user.get('nome', '')}!"
                            )
                            st.rerun()

        else:
            with st.form("novo_cadastro_form"):
                primeiro_nome = st.text_input(
                    "Primeiro nome",
                    placeholder="Ex: Silvia",
                    max_chars=40,
                )
                email_cadastro = st.text_input(
                    "E-mail",
                    placeholder="seuemail@exemplo.com",
                    max_chars=120,
                )
                senha_cadastro = st.text_input(
                    "Senha",
                    type="password",
                    max_chars=128,
                    help="Use no mínimo 6 caracteres.",
                )
                confirmar_senha = st.text_input(
                    "Confirmar senha",
                    type="password",
                    max_chars=128,
                )
                cadastrar = st.form_submit_button("Cadastrar")

            if cadastrar:
                primeiro_nome_limpo = primeiro_nome.strip()
                email_limpo = email_cadastro.strip().lower()
                senha_limpa = senha_cadastro.strip()
                confirmar_senha_limpa = confirmar_senha.strip()

                if not primeiro_nome_limpo:
                    st.warning("Informe seu primeiro nome.")
                elif len(primeiro_nome_limpo.split()) > 1:
                    st.warning("Informe apenas o primeiro nome.")
                elif not is_valid_email(email_limpo):
                    st.warning("Informe um e-mail válido.")
                elif len(senha_limpa) < 6:
                    st.warning("A senha deve ter pelo menos 6 caracteres.")
                elif senha_limpa != confirmar_senha_limpa:
                    st.warning("A confirmação de senha não confere.")
                else:
                    with st.spinner("Criando conta..."):
                        auth_result = sign_up_with_email_password(
                            first_name=primeiro_nome_limpo,
                            email=email_limpo,
                            password=senha_limpa,
                        )

                    status = auth_result.get("status")
                    if status == "error":
                        st.error(str(auth_result.get("message", "Falha ao criar sua conta.")))
                    elif status == "pending_confirmation":
                        st.success(str(auth_result.get("message", "Cadastro criado.")))
                        st.info(
                            "Após confirmar seu e-mail, volte em 'Já tenho cadastro' para entrar com e-mail e senha."
                        )
                    else:
                        with st.spinner("Carregando seus dados..."):
                            user = ensure_user_profile(
                                email=auth_result.get("email", email_limpo),
                                first_name=primeiro_nome_limpo,
                            )

                        if user is None:
                            st.error(
                                "Conta criada no Auth, mas não foi possível criar seu perfil local. "
                                "Tente entrar novamente."
                            )
                        else:
                            st.session_state["user"] = user
                            st.session_state["nome"] = user.get("nome", primeiro_nome_limpo)
                            st.session_state["email"] = user.get("email", email_limpo)
                            st.session_state["auth_user_id"] = auth_result.get("auth_user_id", "")
                            st.session_state["auth_access_token"] = auth_result.get("access_token", "")
                            st.session_state["auth_refresh_token"] = auth_result.get("refresh_token", "")
                            st.session_state["session_recorded"] = False
                            st.session_state["page"] = "🏠 Hoje"
                            st.session_state["login_message"] = (
                                "Cadastro criado com sucesso. Bem-vindo ao CuidaFácil!"
                            )
                            st.rerun()

    else:
        user = st.session_state["user"]
        st.success(f"Logado como {user.get('nome', '')}")
        st.caption(user.get("email", ""))

        is_admin_sidebar = user.get("email", "").strip().lower() == admin_email()
        page_options = ["🏠 Hoje", "🗓️ Calendário", "📈 Evolução", "🌱 Planta com IA", "⚙️ Configuração inicial"]
        if is_admin_sidebar:
            page_options.insert(2, "🧪 Admin")

        current_page = st.session_state.get("page", "🏠 Hoje")
        if current_page not in page_options:
            current_page = "🏠 Hoje"

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
                "last_tracked_page",
                "last_tracked_section_access",
            ]:
                st.session_state.pop(key, None)
            st.rerun()

st.title("CuidaFácil")
st.caption("Cuide da planta com IA e acompanhe suas atividades do dia a dia.")

if st.session_state.get("login_message"):
    st.success(st.session_state.pop("login_message"))

if "user" not in st.session_state:
    page = st.radio(
        "Antes de começar",
        ["Landing", "Entrar", "Configuração inicial"],
        horizontal=True,
        label_visibility="collapsed",
    )

    if page == "Landing":
        track_page_once("Landing", page_group="public")
        render_landing()
    elif page == "Entrar":
        track_page_once("Entrar", page_group="public")
        st.info(
            "Escolha na lateral se você já tem cadastro ou se deseja criar uma conta. "
            "O acesso é feito por e-mail e senha via Supabase Auth."
        )
    else:
        track_page_once("Configuracao inicial", page_group="public")
        render_setup()

    st.stop()

user = st.session_state["user"]
record_session_once(user)

page = st.session_state.get("page", "🏠 Hoje")
is_admin = user.get("email", "").strip().lower() == admin_email()
track_page_once(page, email=user.get("email", ""), page_group="authenticated")
track_section_access_once(page, email=user.get("email", ""))

if page == "🏠 Hoje":
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
    render_setup()
