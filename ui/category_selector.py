from __future__ import annotations

import streamlit as st


CATEGORIAS = {
    "Água": "💧",
    "Saúde": "❤️",
    "Planta": "🌱",
    "Pet": "🐾",
    "Exercício": "🏃",
    "Estudo": "📘",
    "Feira": "🛒",
    "Casa": "🏠",
    "Outro": "⋯",
}


def _format_category(nome: str) -> str:
    return f"{CATEGORIAS.get(nome, '⋯')}  {nome}"


def render_category_selector(default: str = "Água") -> str:
    # Usa st.radio porque mantém estado automaticamente e evita botão "Selecionar".
    categorias = list(CATEGORIAS.keys())

    if "selected_category" not in st.session_state:
        st.session_state["selected_category"] = default

    if st.session_state["selected_category"] not in categorias:
        st.session_state["selected_category"] = default

    st.markdown("### 1. Escolha uma categoria")
    st.caption("Toque em uma opção. A categoria selecionada será usada na atividade.")

    selected = st.radio(
        label="Categoria",
        options=categorias,
        index=categorias.index(st.session_state["selected_category"]),
        format_func=_format_category,
        horizontal=True,
        label_visibility="collapsed",
        key="selected_category",
    )

    st.markdown(
        f'''
        <div class="selected-category-panel">
            <span class="selected-category-check">✓</span>
            <span>Categoria selecionada:</span>
            <strong>{CATEGORIAS[selected]} {selected}</strong>
        </div>
        ''',
        unsafe_allow_html=True,
    )

    return selected
