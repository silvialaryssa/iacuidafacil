from __future__ import annotations

import streamlit as st

from ui.components import figure_card


BENEFICIOS = [
    ("🌱", "Planta com IA", "A principal experiência do app ajuda a montar uma rotina de cuidados para sua planta."),
    ("🗓️", "Atividades do dia a dia", "No mesmo lugar, você pode cadastrar tarefas rotineiras com horário e frequência."),
    ("📈", "Acompanhamento simples", "Veja o andamento das conclusões e mantenha clareza sobre o que já foi feito."),
]


def render_landing() -> None:
    st.subheader("IACuidaFácil")

    st.markdown(
        """
        <div class="landing-figure" aria-hidden="true">
            <div class="landing-figure-main">🌿</div>
            <div class="landing-figure-chip">Planta com IA + rotina</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for icon, title, text in BENEFICIOS:
        figure_card(icon, title, text)

    st.markdown(
        """
        <div class="landing-cta">
            <strong>👉 Ainda não tem conta?</strong>
            <span>Crie seu cadastro gratuito e comece agora a cuidar das suas plantas com IA.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Quero me cadastrar agora", type="primary", use_container_width=True):
        st.session_state["nav_page"] = "Entrar"
        st.session_state["auth_tab"] = "Quero me cadastrar"
        st.rerun()
