from __future__ import annotations

import streamlit as st


def render_summary_cards(total: int, concluidas: int, pendentes: int, progresso: float) -> None:
    st.markdown("### Resumo do dia")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f'''
            <div class="summary-card">
                <div class="summary-value">{total}</div>
                <div class="summary-label">Total</div>
            </div>
            ''',
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f'''
            <div class="summary-card">
                <div class="summary-value">{concluidas}</div>
                <div class="summary-label">Concluídas</div>
            </div>
            ''',
            unsafe_allow_html=True,
        )

    col3, col4 = st.columns(2)
    with col3:
        st.markdown(
            f'''
            <div class="summary-card">
                <div class="summary-value">{pendentes}</div>
                <div class="summary-label">Pendentes</div>
            </div>
            ''',
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            f'''
            <div class="summary-card">
                <div class="summary-value">{progresso:.0f}%</div>
                <div class="summary-label">Progresso</div>
            </div>
            ''',
            unsafe_allow_html=True,
        )
