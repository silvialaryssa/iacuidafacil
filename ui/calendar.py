from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from services.app_service import (
    cancel_activity,
    complete_activity,
    uncomplete_activity,
    user_executions_for_date,
    user_scheduled_activities,
)
from ui.activity_cards import render_activity_card


def _calendar_summary(user: dict, target_date: date) -> tuple[int, int, float]:
    activities = user_scheduled_activities(user, target_date)
    executions = user_executions_for_date(user, target_date)

    completed_ids = set()
    if not executions.empty and "id_atividade" in executions.columns:
        completed_ids = set(executions["id_atividade"].astype(str))

    total = len(activities)
    completed = 0
    if total and not activities.empty and "id_atividade" in activities.columns:
        activity_ids = set(activities["id_atividade"].astype(str))
        completed = sum(1 for item in completed_ids if item in activity_ids)

    progress = (completed / total) if total else 0.0
    return total, completed, progress


def render_calendar(user: dict) -> None:
    st.subheader("🗓️ Calendário")
    st.caption("Escolha um dia e veja as atividades previstas em uma interface simples e mobile friendly.")

    if st.session_state.get("save_message"):
        st.success(st.session_state.pop("save_message"))
    if st.session_state.get("save_error"):
        st.error(st.session_state.pop("save_error"))

    if "calendar_date" not in st.session_state:
        st.session_state["calendar_date"] = date.today()

    top_left, top_center, top_right = st.columns([1.1, 3.6, 1.1])

    with top_left:
        if st.button("←", use_container_width=True, help="Dia anterior"):
            st.session_state["calendar_date"] = st.session_state["calendar_date"] - timedelta(days=1)
            st.rerun()

    with top_center:
        st.session_state["calendar_date"] = st.date_input(
            "Selecione a data",
            value=st.session_state["calendar_date"],
            key="calendar_date_picker",
        )

    with top_right:
        if st.button("→", use_container_width=True, help="Próximo dia"):
            st.session_state["calendar_date"] = st.session_state["calendar_date"] + timedelta(days=1)
            st.rerun()

    c1, c2, c3 = st.columns(3)
    total, completed, progress = _calendar_summary(user, st.session_state["calendar_date"])

    with c1:
        st.markdown(
            f'''
            <div class="calendar-summary-card">
                <div class="summary-label">Previstas</div>
                <div class="summary-value">{total}</div>
            </div>
            ''',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'''
            <div class="calendar-summary-card">
                <div class="summary-label">Concluídas</div>
                <div class="summary-value">{completed}</div>
            </div>
            ''',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f'''
            <div class="calendar-summary-card">
                <div class="summary-label">Progresso</div>
                <div class="summary-value">{int(progress * 100)}%</div>
            </div>
            ''',
            unsafe_allow_html=True,
        )

    st.progress(progress)

    selected_date = st.session_state["calendar_date"]
    weekday_label = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"][selected_date.weekday()]

    st.markdown(
        f'''
        <div class="calendar-day-card">
            <div class="calendar-day-title">{weekday_label}, {selected_date.strftime("%d/%m/%Y")}</div>
            <div class="calendar-day-subtitle">Agenda do dia selecionado</div>
        </div>
        ''',
        unsafe_allow_html=True,
    )

    activities = user_scheduled_activities(user, selected_date)
    executions = user_executions_for_date(user, selected_date)

    completed_ids = set()
    if not executions.empty and "id_atividade" in executions.columns:
        completed_ids = set(executions["id_atividade"].astype(str))

    if activities.empty:
        st.info("Nenhuma atividade encontrada para este dia. Se quiser, volte para Hoje e crie uma rotina nova.")
        if st.button("Ir para Hoje", use_container_width=True):
            st.session_state["page"] = "🏠 Hoje"
            st.rerun()
        return

    def concluir(row):
        id_atividade = str(row.get("id_atividade", ""))
        if id_atividade not in completed_ids:
            try:
                complete_activity(user, id_atividade, row.get("titulo", ""), data_referencia=selected_date.isoformat())
                st.session_state["save_message"] = "Atividade marcada como realizada."
            except Exception as erro:
                st.session_state["save_error"] = f"Não foi possível marcar atividade: {erro}"
            st.rerun()

    def desmarcar(row):
        id_atividade = str(row.get("id_atividade", ""))
        if id_atividade in completed_ids:
            try:
                uncomplete_activity(user, id_atividade, row.get("titulo", ""), data_referencia=selected_date.isoformat())
                st.session_state["save_message"] = "Atividade desmarcada."
            except Exception as erro:
                st.session_state["save_error"] = f"Não foi possível desmarcar atividade: {erro}"
            st.rerun()

    def cancelar(row):
        cancel_activity(user, str(row.get("id_atividade", "")), row.get("titulo", ""))
        st.rerun()

    for _, row in activities.iterrows():
        completed = str(row.get("id_atividade", "")) in completed_ids
        render_activity_card(row, concluir, desmarcar, cancelar, completed=completed)