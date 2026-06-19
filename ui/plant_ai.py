from __future__ import annotations

import json
from html import escape

import streamlit as st

from config.settings import has_chatgpt_config, has_gemini_config
from services.app_service import buscar_planta_por_id, create_plant_from_ai
from services.plant_ai_service import PlantAiRequest, get_plant_ai_service


AMBIENTES = [
    "Ambiente interno com pouca luz",
    "Ambiente interno com boa luz indireta",
    "Varanda / meia-sombra",
    "Ambiente externo com sol direto",
]


def _render_plant_ai_hero(refazer: bool) -> None:
    eyebrow = "Refazer análise" if refazer else "Assistente inteligente"
    subtitle = (
        "Revise a rotina de cuidados da planta e gere um novo plano semanal com base no contexto atual."
        if refazer
        else "Descreva sua planta e receba uma rotina semanal pronta para virar tarefas dentro do app."
    )
    st.markdown(
        f"""
        <div class="home-hero-card plant-hero-card">
            <div class="home-hero-copy">
                <div class="home-hero-eyebrow">{eyebrow}</div>
                <div class="home-hero-title">Planta com IA</div>
                <div class="home-hero-text">{subtitle}</div>
            </div>
            <div class="home-hero-aside plant-hero-aside">
                <div class="home-hero-aside-label">Resultado</div>
                <div class="home-hero-aside-value">7 dias</div>
                <div class="home-hero-aside-text">de cuidados organizados</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_plant_ai_highlights() -> None:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            """
            <div class="plant-info-card">
                <div class="plant-info-title">O que a IA faz</div>
                <div class="plant-info-text">Organiza os cuidados da planta com linguagem simples, rotina semanal e tarefas prontas para acompanhar.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            """
            <div class="plant-info-card soft">
                <div class="plant-info-title">O que você informa</div>
                <div class="plant-info-text">Nome da planta, ambiente e objetivo da análise para gerar um plano mais útil e realista.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_ai_result(user: dict, data: dict) -> None:
    nome = data.get("nome_popular", "Planta")
    nome_safe = escape(nome)
    cientifico = escape(str(data.get("nome_cientifico", "")).strip())
    resumo = escape(str(data.get("resumo_cuidados", "")).strip())

    st.success(f"Plano gerado para {nome}.")
    st.markdown(
        f"""
        <div class="plant-result-card">
            <div class="home-section-eyebrow">Plano gerado</div>
            <div class="home-section-title">{nome_safe}</div>
            <div class="plant-result-scientific">{cientifico}</div>
            <div class="plant-result-summary">{resumo}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cuidados = data.get("cuidados_semanais", []) or []
    if cuidados:
        rows = []
        for cuidado in cuidados:
            dia = escape(str(cuidado.get("dia_semana", "")).strip())
            horario = escape(str(cuidado.get("horario", "")).strip())
            descricao = escape(str(cuidado.get("descricao", "")).strip())
            rows.append(
                f'<div class="plant-care-row">'
                f'<span class="plant-care-badge">{dia}</span>'
                f'<div class="plant-care-content">'
                f'<div class="plant-care-when">{horario}</div>'
                f'<div class="plant-care-what">{descricao}</div>'
                f"</div></div>"
            )
        st.markdown(
            '<div class="plant-care-list-card">'
            '<div class="home-section-eyebrow">Cuidados sugeridos</div>'
            '<div class="home-section-title">Tarefas que serão criadas</div>'
            f'<div class="plant-care-rows">{"".join(rows)}</div>'
            "</div>",
            unsafe_allow_html=True,
        )

    alertas = [a for a in data.get("alertas", []) if str(a).strip()]
    if alertas:
        st.markdown(
            """
            <div class="home-section-eyebrow">Atenção</div>
            <div class="home-section-title">Alertas da IA</div>
            """,
            unsafe_allow_html=True,
        )
        for alerta in alertas:
            st.markdown(
                f"""
                <div class="plant-alert-card">{escape(str(alerta))}</div>
                """,
                unsafe_allow_html=True,
            )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Cadastrar planta e criar tarefas", type="primary", use_container_width=True):
            try:
                create_plant_from_ai(
                    user=user,
                    prompt_usuario=data.get("_prompt_usuario", ""),
                    ai_data=data,
                )
                st.session_state.pop("plant_ai_result", None)
                st.session_state["save_message"] = "Planta cadastrada e cuidados criados."
                st.session_state["page"] = "🏠 Sua Rotina"
                st.rerun()
            except Exception as err:
                st.error(f"Não foi possível cadastrar a planta: {err}")
    with col2:
        if st.button("Descartar", use_container_width=True):
            st.session_state.pop("plant_ai_result", None)
            st.rerun()

   # with st.expander("Ver JSON estruturado"):
      #s  st.code(json.dumps({k: v for k, v in data.items() if k != "_prompt_usuario"}, ensure_ascii=False, indent=2), language="json")


def render_plant_ai(user: dict) -> None:
    refazer_id = st.session_state.pop("refazer_analise_planta_id", "")
    planta_refazer = buscar_planta_por_id(refazer_id) if refazer_id else None

    _render_plant_ai_hero(bool(planta_refazer))
    _render_plant_ai_highlights()

    if st.session_state.get("plant_ai_result"):
        _render_ai_result(user, st.session_state["plant_ai_result"])
        return

    st.markdown(
        """
        <div class="home-section-eyebrow">Análise</div>
        <div class="home-section-title">Conte para a IA sobre a sua planta</div>
        """,
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        with st.form("plant_ai_minimal_form"):
            planta = st.text_input(
                "Qual planta?",
                value=planta_refazer.get("nome_popular", "") if planta_refazer else "",
                placeholder="Ex: Jiboia",
            )
            ambiente = st.selectbox("Onde ela fica?", AMBIENTES)
            sintomas = st.text_area(
                "O que você quer saber?",
                value="Refazer rotina de cuidados semanais." if planta_refazer else "",
                placeholder="Ex: Quero uma rotina simples de cuidados semanais.",
                height=110,
            )
            contexto = st.text_input("Detalhe opcional", placeholder="Ex: apartamento, pouca luz, clima seco")

            preview_title = planta.strip() or "Sua planta"
            preview_text = sintomas.strip() or "A rotina será gerada com base nas informações preenchidas."
            st.markdown(
                f"""
                <div class="home-form-preview plant-preview-card">
                    <div class="home-form-preview-label">Prévia da análise</div>
                    <div class="home-form-preview-title">{escape(preview_title)} • {escape(ambiente)}</div>
                    <div class="home-form-preview-text">{escape(preview_text)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            gerar = st.form_submit_button("Gerar cuidados", type="primary", use_container_width=True)

    if gerar:
        if not planta.strip():
            st.warning("Informe o nome da planta.")
            return
        if not sintomas.strip():
            st.warning("Informe o objetivo ou dúvida sobre a planta.")
            return
        if not (has_gemini_config() or has_chatgpt_config()):
            st.error("Nenhuma API de IA configurada. Configure Gemini ou OpenAI em Configuração inicial.")
            return

        with st.spinner("Gerando rotina de cuidados..."):
            try:
                data = get_plant_ai_service().ask_for_guidance(
                    PlantAiRequest(
                        funcionalidade="Planejamento semanal de cuidados",
                        planta=planta.strip(),
                        ambiente=ambiente,
                        sintomas=sintomas.strip(),
                        contexto=contexto.strip(),
                    )
                )
                st.session_state["plant_ai_result"] = data
                st.rerun()
            except Exception as err:
                st.error(f"Não foi possível gerar a orientação: {err}")
