from __future__ import annotations

import streamlit as st
from streamlit_option_menu import option_menu

PAGE_ICONS = {
    "🏠 Sua Rotina": "house",
    "🌱 Planta com IA": "flower1",
    "🗓️ Calendário": "calendar3",
    "📈 Evolução": "graph-up",  
    "🧪 Admin": "gear",
}
SAIR_OPTION = "🚪 Sair"


def load_css() -> None:
    with open("assets/style.css", "r", encoding="utf-8") as f:
        st.markdown(f.read(), unsafe_allow_html=True)


def render_top_nav(user: dict, is_admin: bool) -> str:
    page_options = ["🏠 Sua Rotina","🌱 Planta com IA", "🗓️ Calendário", "📈 Evolução"]
    if is_admin:
        page_options.insert(2, "🧪 Admin")
    page_options.append(SAIR_OPTION)

    icons = [PAGE_ICONS.get(option, "circle") for option in page_options[:-1]] + ["box-arrow-right"]

    current_page = st.session_state.get("page", page_options[0])
    if current_page not in page_options:
        current_page = page_options[0]
    default_index = page_options.index(current_page)

    st.caption(f"Logado como {user.get('nome', '')} · {user.get('email', '')}")

    return option_menu(
        menu_title=None,
        options=page_options,
        icons=icons,
        orientation="horizontal",
        default_index=default_index,
        styles={
            "container": {"padding": "0!important", "background-color": "#f6f4ea"},
            "icon": {"color": "#2f6f42", "font-size": "16px"},
            "nav-link": {
                "font-size": "14px",
                "text-align": "center",
                "margin": "0px",
                "color": "#1f2a23",
                "--hover-color": "#e8f3e6",
            },
            "nav-link-selected": {"background-color": "#2f6f42", "color": "white"},
        },
    )


def hero(title: str, subtitle: str) -> None:
    st.markdown(
        f'''
        <div class="hero-card">
            <div class="hero-content">
                <div class="hero-copy">
                    <div class="hero-title">{title}</div>
                    <div class="hero-subtitle">{subtitle}</div>
                    <div class="hero-badges">
                        <span class="hero-badge">Rotina simples</span>
                        <span class="hero-badge">Visual claro</span>
                        <span class="hero-badge">Mobile friendly</span>
                    </div>
                </div>
                <div class="hero-figure" aria-hidden="true">🌿</div>
            </div>
        </div>
        ''',
        unsafe_allow_html=True,
    )


def quote_card(text: str) -> None:
    st.markdown(
        f'''
        <div class="quote-card">
            <div style="color:#5F6368; font-size:14px;">🌿 Provérbio do dia</div>
            <div style="font-size:19px; font-weight:650; color:#33401D; margin-top:6px;">“{text}”</div>
        </div>
        ''',
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str) -> None:
    st.markdown(
        f'''
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
        </div>
        ''',
        unsafe_allow_html=True,
    )


def figure_card(icon: str, title: str, text: str) -> None:
    st.markdown(
        f'''
        <div class="figure-card">
            <div class="figure-icon">{icon}</div>
            <div class="figure-copy">
                <strong>{title}</strong>
                <span>{text}</span>
            </div>
        </div>
        ''',
        unsafe_allow_html=True,
    )
