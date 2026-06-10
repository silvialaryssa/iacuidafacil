from __future__ import annotations

from datetime import date, time

import streamlit as st

from services.app_service import (
    buscar_planta_por_id,
    cancel_activity,
    complete_activity,
    excluir_cuidados_da_planta,
    uncomplete_activity,
    user_executions_for_date,
    user_scheduled_activities,
)
from services.app_service import create_activity
from ui.activity_cards import render_activity_card
from ui.category_selector import CATEGORIAS


FREQUENCIAS = ["Todos os dias", "Algumas vezes por semana", "Apenas uma vez"]
DIAS_SEMANA = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
NEW_ACTIVITY_CATEGORY_KEY = "new_activity_category"
RESET_NEW_ACTIVITY_CATEGORY_KEY = "reset_new_activity_category"


def _time_to_str(value) -> str:
    if hasattr(value, "strftime"):
        return value.strftime("%H:%M")
    return str(value)


def _to_app_frequency(label: str) -> str:
    return {
        "Todos os dias": "Diária",
        "Algumas vezes por semana": "Semanal",
        "Apenas uma vez": "Uma vez",
    }.get(label, "Diária")


def _default_description(categoria: str) -> str:
    exemplos = {
        "Água": "Beber água",
        "Saúde": "Tomar medicação",
        "Planta": "Regar planta",
        "Pet": "Cuidar do pet",
        "Exercício": "Caminhar 20 minutos",
        "Estudo": "Estudar 30 minutos",
        "Feira": "Comprar frutas",
        "Casa": "Organizar a casa",
        "Outro": "Minha atividade",
    }
    return exemplos.get(categoria, "Minha atividade")


def _default_category() -> str:
    for categoria in CATEGORIAS.keys():
        if categoria != "Planta":
            return categoria
    return next(iter(CATEGORIAS.keys()), "Outro")


def _go_to_plant_ai() -> None:
    st.session_state["page"] = "🌱 Planta com IA"
    st.session_state["show_new_activity_form"] = False
    st.session_state[RESET_NEW_ACTIVITY_CATEGORY_KEY] = True
    st.rerun()


def _render_stat_card(label: str, value: int | str, description: str, tone: str = "default") -> None:
    st.markdown(
        f"""
        <div class="home-stat-card {tone}">
            <div class="home-stat-label">{label}</div>
            <div class="home-stat-value">{value}</div>
            <div class="home-stat-description">{description}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_home_summary(nome: str, total: int, concluidas: int, progresso: int) -> None:
    restantes = max(total - concluidas, 0)

    st.markdown(
        f"""
        <div class="home-hero-card">
            <div class="home-hero-copy">
                <div class="home-hero-eyebrow">Painel de hoje</div>
                <div class="home-hero-title">Olá, {nome}</div>
                <div class="home-hero-text">
                    Organize sua rotina do dia e acompanhe o que já avançou com uma visualização mais clara e leve.
                </div>
                <div class="home-hero-progress-row">
                    <div class="home-hero-progress-track">
                        <span style="width: {progresso if total else 0}%;"></span>
                    </div>
                    <div class="home-hero-progress-value">{progresso}%</div>
                </div>
            </div>
            <div class="home-hero-aside">
                <div class="home-hero-aside-label">Resumo do dia</div>
                <div class="home-hero-aside-value">{concluidas}/{total}</div>
                <div class="home-hero-aside-text">atividades concluídas</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    stat_col1, stat_col2, stat_col3 = st.columns(3)
    with stat_col1:
        _render_stat_card("Atividades", total, "planejadas para hoje")
    with stat_col2:
        _render_stat_card("Concluídas", concluidas, "já marcadas como feitas", tone="success")
    with stat_col3:
        _render_stat_card("Restantes", restantes, "ainda pendentes no dia", tone="accent")

def _render_new_activity(user: dict, hoje: date) -> None:
    with st.container(border=True):
        st.markdown("### Nova atividade")
        st.caption("Cadastre uma rotina simples ou escolha Planta para seguir direto para o assistente com IA.")

        if st.session_state.pop(RESET_NEW_ACTIVITY_CATEGORY_KEY, False):
            st.session_state[NEW_ACTIVITY_CATEGORY_KEY] = _default_category()

        intro_col, helper_col = st.columns([1.6, 1])
        with intro_col:
            categoria = st.selectbox(
                "Categoria",
                list(CATEGORIAS.keys()),
                format_func=lambda c: f"{CATEGORIAS.get(c, '•')} {c}",
                key=NEW_ACTIVITY_CATEGORY_KEY,
            )
        with helper_col:
            st.markdown("##### Sugestão")
            st.caption(_default_description(categoria))

        if categoria == "Planta":
            _go_to_plant_ai()

        with st.form("new_activity_form", clear_on_submit=True):
            descricao = st.text_input(
                "Descrição da atividade",
                placeholder=f"Ex: {_default_description(categoria)}",
                help="Use uma descrição curta e direta para ficar fácil de reconhecer depois.",
            )

            st.markdown("##### Frequência")
            frequencia_label = st.radio(
                "Quando essa atividade deve aparecer?",
                FREQUENCIAS,
                horizontal=True,
                label_visibility="collapsed",
            )
            frequencia = _to_app_frequency(frequencia_label)

            dias_semana = ""
            data_inicio = hoje
            agenda_col, horario_col = st.columns([1.5, 1])
            with agenda_col:
                if frequencia == "Semanal":
                    dias = st.multiselect(
                        "Dias da semana",
                        DIAS_SEMANA,
                        default=[DIAS_SEMANA[hoje.weekday()]],
                        help="Selecione em quais dias essa atividade deve aparecer.",
                    )
                    dias_semana = ",".join(dias)
                elif frequencia == "Uma vez":
                    data_inicio = st.date_input("Data da atividade", value=hoje)
                else:
                    st.text_input("Agenda", value="Todos os dias", disabled=True)

            with horario_col:
                horario = st.time_input("Horário", value=time(8, 0), step=300)

            preview = descricao.strip() or _default_description(categoria)
            st.markdown(
                f"""
                <div class="home-form-preview">
                    <div class="home-form-preview-label">Prévia</div>
                    <div class="home-form-preview-title">{categoria}</div>
                    <div class="home-form-preview-text">{preview} • {_time_to_str(horario)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            action_col1, action_col2 = st.columns([1.4, 1])
            with action_col1:
                submit = st.form_submit_button("Salvar atividade", type="primary", use_container_width=True)
            with action_col2:
                cancel_form = st.form_submit_button("Cancelar", use_container_width=True)

        if cancel_form:
            st.session_state["show_new_activity_form"] = False
            st.rerun()

        if submit:
            if frequencia == "Semanal" and not dias_semana:
                st.warning("Escolha pelo menos um dia da semana.")
                return
            try:
                create_activity(
                    user=user,
                    titulo=categoria,
                    categoria=categoria,
                    descricao=descricao.strip() or _default_description(categoria),
                    frequencia=frequencia,
                    horario=_time_to_str(horario),
                    data_inicio=data_inicio.isoformat(),
                    data_fim="",
                    dias_semana=dias_semana,
                )
                st.session_state["save_message"] = "Atividade criada."
                st.rerun()
            except Exception as erro:
                st.error(f"Não foi possível salvar: {erro}")


def _render_new_activity_entry(user: dict, hoje: date) -> None:
    is_open = st.session_state.get("show_new_activity_form", False)

    if not is_open:
        st.markdown(
            """
            <div class="home-actions-header">
                <div>
                    <div class="home-section-eyebrow">Ações rápidas</div>
                    <div class="home-section-title">Escolha como quer começar</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        action_col1, action_col2 = st.columns(2)
        with action_col1:
            st.markdown(
                """
                <div class="home-action-card primary">
                    <div class="home-action-title">Planta com IA</div>
                    <div class="home-action-text">Monte uma rotina de cuidados com apoio do assistente inteligente.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Abrir Planta com IA", key="open_plant_ai_home", use_container_width=True):
                _go_to_plant_ai()
        with action_col2:
            st.markdown(
                """
                <div class="home-action-card secondary">
                    <div class="home-action-title">Nova atividade</div>
                    <div class="home-action-text">Cadastre tarefas do dia a dia e acompanhe as conclusões em um só lugar.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Cadastrar nova atividade", key="open_new_activity_home", type="primary", use_container_width=True):
                st.session_state["show_new_activity_form"] = True
                st.rerun()
        return

    top_col1, top_col2 = st.columns([1.3, 1])
    with top_col1:
        st.markdown(
            """
            <div class="home-section-eyebrow">Cadastro aberto</div>
            <div class="home-section-title">Nova atividade manual</div>
            """,
            unsafe_allow_html=True,
        )
    with top_col2:
        if st.button("Fechar cadastro", use_container_width=True):
            st.session_state["show_new_activity_form"] = False
            st.rerun()

    _render_new_activity(user, hoje)


def _confirmar_cancelamento_planta(user: dict, row) -> None:
    id_atividade = str(row.get("id_atividade", ""))
    id_planta = str(row.get("planta_id", ""))
    planta = buscar_planta_por_id(id_planta) if id_planta else None
    nome_planta = planta.get("nome_popular", "sua planta") if planta else "sua planta"

    st.warning(
        f"Este cuidado faz parte da rotina da planta **{nome_planta}**. "
        "Se você remover este cuidado, a rotina criada pela IA pode ficar incompleta."
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Manter", key=f"keep_{id_atividade}", use_container_width=True):
            st.session_state.pop("pending_cancel_activity", None)
            st.rerun()
    with c2:
        if st.button("Excluir este cuidado", key=f"delete_one_{id_atividade}", use_container_width=True):
            cancel_activity(user, id_atividade, row.get("titulo", ""))
            st.session_state.pop("pending_cancel_activity", None)
            st.rerun()
    with c3:
        if st.button("Refazer análise IA", key=f"redo_ai_{id_atividade}", use_container_width=True):
            st.session_state["refazer_analise_planta_id"] = id_planta
            st.session_state.pop("pending_cancel_activity", None)
            st.session_state["page"] = "🌱 Planta com IA"
            st.rerun()

    if st.button("Excluir todos os cuidados desta planta", key=f"delete_all_{id_atividade}", use_container_width=True):
        excluir_cuidados_da_planta(user, id_planta)
        st.session_state.pop("pending_cancel_activity", None)
        st.rerun()


def render_home(user: dict) -> None:
    hoje = date.today()
    nome = user.get("nome", "") or "você"

    if st.session_state.get("save_message"):
        st.success(st.session_state.pop("save_message"))
    if st.session_state.get("save_error"):
        st.error(st.session_state.pop("save_error"))

    activities = user_scheduled_activities(user, hoje)
    executions = user_executions_for_date(user, hoje)

    completed_ids = set()
    if not executions.empty and "id_atividade" in executions.columns:
        completed_ids = set(executions["id_atividade"].astype(str))

    total = len(activities)
    concluidas = sum(1 for item in completed_ids if item in set(activities.get("id_atividade", [] ).astype(str))) if total else 0
    progresso = int((concluidas / total) * 100) if total else 0

    _render_home_summary(nome, total, concluidas, progresso)

    _render_new_activity_entry(user, hoje)

    st.divider()

    pending_id = st.session_state.get("pending_cancel_activity")
    if pending_id and not activities.empty:
        pending = activities[activities["id_atividade"].astype(str) == str(pending_id)]
        if not pending.empty:
            _confirmar_cancelamento_planta(user, pending.iloc[0])
            st.divider()

    if activities.empty:
        st.info("Nada previsto para hoje. Crie uma atividade simples ou gere cuidados de plantas com IA.")
        return

    st.markdown(
        """
        <div class="home-section-eyebrow">Agenda</div>
        <div class="home-section-title">Atividades de hoje</div>
        """,
        unsafe_allow_html=True,
    )

    def concluir(row):
        id_atividade = str(row.get("id_atividade", ""))
        if id_atividade not in completed_ids:
            try:
                complete_activity(user, id_atividade, row.get("titulo", ""), data_referencia=hoje.isoformat())
                st.session_state["save_message"] = "Atividade marcada como realizada."
            except Exception as erro:
                st.session_state["save_error"] = f"Não foi possível marcar atividade: {erro}"
            st.rerun()

    def desmarcar(row):
        id_atividade = str(row.get("id_atividade", ""))
        if id_atividade in completed_ids:
            try:
                uncomplete_activity(user, id_atividade, row.get("titulo", ""), data_referencia=hoje.isoformat())
                st.session_state["save_message"] = "Atividade desmarcada."
            except Exception as erro:
                st.session_state["save_error"] = f"Não foi possível desmarcar atividade: {erro}"
            st.rerun()

    def cancelar(row):
        id_atividade = str(row.get("id_atividade", ""))
        if str(row.get("origem", "")) == "ia_planta" and str(row.get("planta_id", "")):
            st.session_state["pending_cancel_activity"] = id_atividade
            st.rerun()
        else:
            cancel_activity(user, id_atividade, row.get("titulo", ""))
            st.rerun()

    for _, row in activities.iterrows():
        completed = str(row.get("id_atividade", "")) in completed_ids
        render_activity_card(row, concluir, desmarcar, cancelar, completed=completed)
