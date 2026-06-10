from __future__ import annotations

from html import escape

import streamlit as st

from ui.category_selector import CATEGORIAS


def render_activity_card(row, on_complete, on_uncomplete, on_cancel, completed: bool = False) -> None:
    categoria = str(row.get("categoria", "Outro"))
    icone = CATEGORIAS.get(categoria, "⋯")
    titulo = escape(str(row.get("titulo", categoria)))
    horario = escape(str(row.get("horario", "")))
    frequencia = escape(str(row.get("frequencia", "")))
    descricao = escape(str(row.get("descricao", "")))
    id_atividade = str(row.get("id_atividade", ""))

    card_class = "activity-paper-card done" if completed else "activity-paper-card pending"
    title_class = "activity-title done" if completed else "activity-title"
    desc_class = "activity-desc done" if completed else "activity-desc"
    status_badge = '<span class="activity-status-badge done">Realizada</span>' if completed else ""
    title_html = f"<s>{titulo}</s>" if completed else titulo
    desc_html = f"<s>{descricao}</s>" if completed else descricao

    with st.container():
        col_check, col_content, col_cancel = st.columns([0.75, 6.3, 0.85])

        with col_check:
            if completed:
                if st.button("✓", key=f"uncomplete_{id_atividade}", use_container_width=True, help="Desmarcar atividade"):
                    on_uncomplete(row)
            else:
                if st.button("✓", key=f"complete_{id_atividade}", use_container_width=True, help="Marcar como realizada"):
                    on_complete(row)

        with col_content:
            card_html = (
                f'<div class="{card_class}">'
                '<div class="activity-paper-line"></div>'
                '<div class="activity-card-header">'
                f'<span class="activity-card-icon">{icone}</span>'
                f'<span class="{title_class}">{title_html}</span>'
                f'{status_badge}'
                '</div>'
                f'<div class="activity-meta">{horario} • {frequencia}</div>'
                f'<div class="{desc_class}">{desc_html}</div>'
                '</div>'
            )
            st.markdown(card_html, unsafe_allow_html=True)

        with col_cancel:
            if st.button("×", key=f"cancel_{id_atividade}", use_container_width=True, help="Cancelar agendamento"):
                on_cancel(row)
