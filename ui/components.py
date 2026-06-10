from __future__ import annotations

import streamlit as st


def load_css() -> None:
    with open("assets/style.css", "r", encoding="utf-8") as f:
        st.markdown(f.read(), unsafe_allow_html=True)


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
