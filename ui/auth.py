from __future__ import annotations

import streamlit as st

from services.app_service import ensure_user_profile, is_valid_email
from services.auth_service import sign_in_with_email_password, sign_up_with_email_password


def _complete_login(user: dict, message: str) -> None:
    st.session_state["user"] = user
    st.session_state["nome"] = user.get("nome", "")
    st.session_state["email"] = user.get("email", "")
    st.session_state["session_recorded"] = False
    st.session_state["page"] = "🏠 Sua Rotina"
    st.session_state["login_message"] = message


def render_login_form() -> None:
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
        entrar = st.form_submit_button("Entrar", type="primary", use_container_width=True)

    if not entrar:
        return

    email_limpo = email_login.strip().lower()
    senha_limpa = senha_login.strip()

    if not is_valid_email(email_limpo):
        st.warning("Informe um e-mail válido.")
        return
    if not senha_limpa:
        st.warning("Informe sua senha.")
        return

    with st.spinner("Entrando..."):
        auth_result = sign_in_with_email_password(email=email_limpo, password=senha_limpa)

    if not auth_result.get("ok"):
        st.error(str(auth_result.get("message", "Falha ao autenticar.")))
        return

    with st.spinner("Carregando seus dados..."):
        user = ensure_user_profile(email=auth_result.get("email", email_limpo))

    if user is None:
        st.error("Falha ao carregar seu perfil local. Tente novamente em instantes.")
        return

    st.session_state["auth_user_id"] = auth_result.get("auth_user_id", "")
    st.session_state["auth_access_token"] = auth_result.get("access_token", "")
    st.session_state["auth_refresh_token"] = auth_result.get("refresh_token", "")
    _complete_login(user, f"Bem-vindo de volta, {user.get('nome', '')}!")
    st.rerun()


def render_cadastro_form() -> None:
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
        cadastrar = st.form_submit_button("Cadastrar", type="primary", use_container_width=True)

    if not cadastrar:
        return

    primeiro_nome_limpo = primeiro_nome.strip()
    email_limpo = email_cadastro.strip().lower()
    senha_limpa = senha_cadastro.strip()
    confirmar_senha_limpa = confirmar_senha.strip()

    if not primeiro_nome_limpo:
        st.warning("Informe seu primeiro nome.")
        return
    if len(primeiro_nome_limpo.split()) > 1:
        st.warning("Informe apenas o primeiro nome.")
        return
    if not is_valid_email(email_limpo):
        st.warning("Informe um e-mail válido.")
        return
    if len(senha_limpa) < 6:
        st.warning("A senha deve ter pelo menos 6 caracteres.")
        return
    if senha_limpa != confirmar_senha_limpa:
        st.warning("A confirmação de senha não confere.")
        return

    with st.spinner("Criando conta..."):
        auth_result = sign_up_with_email_password(
            first_name=primeiro_nome_limpo,
            email=email_limpo,
            password=senha_limpa,
        )

    status = auth_result.get("status")
    if status == "error":
        st.error(str(auth_result.get("message", "Falha ao criar sua conta.")))
        return
    if status == "pending_confirmation":
        st.success(str(auth_result.get("message", "Cadastro criado.")))
        st.info(
            "Após confirmar seu e-mail, volte em 'Já tenho cadastro' para entrar com e-mail e senha."
        )
        return

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
        return

    st.session_state["auth_user_id"] = auth_result.get("auth_user_id", "")
    st.session_state["auth_access_token"] = auth_result.get("access_token", "")
    st.session_state["auth_refresh_token"] = auth_result.get("refresh_token", "")
    _complete_login(user, "Cadastro criado com sucesso. Bem-vindo ao CuidaFácil!")
    st.rerun()


def render_auth_section() -> None:
    opcoes = ["Já tenho cadastro", "Quero me cadastrar"]
    padrao = st.session_state.get("auth_tab", opcoes[0])

    tipo_acesso = st.radio(
        "Como deseja acessar?",
        opcoes,
        index=opcoes.index(padrao) if padrao in opcoes else 0,
    )
    st.session_state["auth_tab"] = tipo_acesso

    if tipo_acesso == "Já tenho cadastro":
        render_login_form()
    else:
        render_cadastro_form()
