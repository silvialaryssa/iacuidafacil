from __future__ import annotations

import streamlit as st

from ui.components import figure_card


BENEFICIOS = [
    ("🌱", "Planta com IA", "A principal experiência do app ajuda a montar uma rotina de cuidados para sua planta."),
    ("🗓️", "Atividades do dia a dia", "No mesmo lugar, você pode cadastrar tarefas rotineiras com horário e frequência."),
    ("📈", "Acompanhamento simples", "Veja o andamento das conclusões e mantenha clareza sobre o que já foi feito."),
]


def render_landing() -> None:
    st.subheader("CuidaFácil")
    st.markdown(
        """
        <div class="section-intro">
            Um espaço simples para cuidar melhor das suas plantas com apoio de IA e,
            no mesmo fluxo, organizar atividades rotineiras e acompanhar suas conclusões.
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_left, col_right = st.columns([1.35, 1], gap="large")

    with col_left:
        st.markdown(
            """
            <div class="landing-highlight">
                <h3>Seu assistente de cuidado com plantas</h3>
                <p>
                    A funcionalidade principal do CuidaFácil é orientar o cuidado da planta com um assistente de IA,
                    ajudando você a transformar recomendações em uma rotina prática.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        feat_1, feat_2 = st.columns(2)
        with feat_1:
            figure_card("🤖", "IA que orienta", "Receba ajuda para definir cuidados e criar uma rotina para cada planta.")
        with feat_2:
            figure_card("✅", "Rotina no mesmo lugar", "Cadastre tarefas do cotidiano e acompanhe o que foi concluído.")

        st.markdown(
            """
            <div class="landing-cta">
                <strong>Comece pela planta ou pela sua rotina.</strong>
                <span>Entre no app para usar a Planta com IA, cadastrar atividades e acompanhar sua evolução ao longo do dia.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_right:
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
