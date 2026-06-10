from __future__ import annotations

import hashlib
import urllib.parse
from datetime import date

import streamlit as st

from services.app_service import user_progress_summary


def _get_achievement_level(progress: float) -> str:
    """Retorna o nível de achievement."""
    if progress >= 100:
        return "Excepcional"
    elif progress >= 90:
        return "Excelente"
    elif progress >= 75:
        return "Muito Bom"
    elif progress >= 50:
        return "Bom"
    elif progress >= 25:
        return "Em Progresso"
    else:
        return "Iniciante"


def _get_level_color(progress: float) -> str:
    """Retorna a cor baseada no progresso."""
    if progress >= 100:
        return "#10b981"  # Verde escuro
    elif progress >= 90:
        return "#059669"  # Verde
    elif progress >= 75:
        return "#3b82f6"  # Azul
    elif progress >= 50:
        return "#f59e0b"  # Âmbar
    else:
        return "#ef4444"  # Vermelho


def _generate_share_message(progress: float, completed: int, planned: int, period: str, name: str = "Eu") -> str:
    """Gera uma mensagem compartilhável para redes sociais."""
    if period.lower() == "mês":
        return f"{name} completou {completed} de {planned} atividades neste mês! Progresso: {progress:.0f}% no CuidaFácil #BemEstar"
    else:
        return f"{name} teve uma semana produtiva! {completed} de {planned} atividades completadas ({progress:.0f}%) no CuidaFácil #BemEstar"


def _create_share_buttons(message: str, period: str) -> None:
    """Cria botões de compartilhamento para redes sociais."""
    col1, col2, col3, col4 = st.columns(4)
    
    encoded_message = urllib.parse.quote(message)
    
    with col1:
        twitter_url = f"https://twitter.com/intent/tweet?text={encoded_message}"
        st.link_button("Twitter", twitter_url, use_container_width=True)
    
    with col2:
        whatsapp_url = f"https://wa.me/?text={encoded_message}"
        st.link_button("WhatsApp", whatsapp_url, use_container_width=True)
    
    with col3:
        linkedin_url = f"https://www.linkedin.com/sharing/share-offsite/?url=cuidafacil.app&summary={encoded_message}"
        st.link_button("LinkedIn", linkedin_url, use_container_width=True)
    
    with col4:
        if st.button("Copiar", key=f"copy_{period}", use_container_width=True):
            st.toast("Mensagem copiada!")


def _render_activity_metrics(completed: int, planned: int) -> None:
    """Renderiza cards destacados para as métricas de atividades."""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        with st.container(border=True):
            st.markdown("### ✅ Concluídas")
            st.markdown(f"<h2 style='text-align: center; color: #10b981;'>{completed}</h2>", unsafe_allow_html=True)
    
    with col2:
        with st.container(border=True):
            st.markdown("### 📋 Previstas")
            st.markdown(f"<h2 style='text-align: center; color: #3b82f6;'>{planned}</h2>", unsafe_allow_html=True)
    
    with col3:
        restantes = max(0, planned - completed)
        with st.container(border=True):
            st.markdown("### ⏳ Restantes")
            st.markdown(f"<h2 style='text-align: center; color: #f59e0b;'>{restantes}</h2>", unsafe_allow_html=True)


def _render_progress_card(progress: float, completed: int, planned: int, period: str) -> None:
    """Renderiza um card limpo de progresso."""
    with st.container(border=True):
        col1, col2, col3 = st.columns([1.5, 1, 1])
        
        with col1:
            st.progress(progress / 100 if progress else 0)
            level = _get_achievement_level(progress)
            st.caption(f"**{level}**")
        
        with col2:
            st.metric("Progresso", f"{progress:.0f}%")
        
        with col3:
            st.metric("Atividades", f"{completed}/{planned}")


def render_progress(user: dict) -> None:
    """Renderiza uma interface limpa de progresso."""
    st.header("Evolução")
    
    summary = user_progress_summary(user)
    mes = summary["mes"]
    semana = summary["semana"]
    
    progresso_mes = float(mes["progresso"])
    concluidas_mes = int(mes["concluidas"])
    previstas_mes = int(mes["previstas"])
    
    progresso_semana = float(semana["progresso"])
    concluidas_semana = int(semana["concluidas"])
    previstas_semana = int(semana["previstas"])
    
    nome_usuario = user.get("nome", "Eu")
    
    # ==================== ABAS ====================
    tab_mes, tab_semana, tab_comparativo = st.tabs(["Mês", "Semana", "Comparativo"])
    
    # ==================== ABA: MÊS ====================
    with tab_mes:
        st.subheader("Progresso do Mês")
        _render_progress_card(progresso_mes, concluidas_mes, previstas_mes, "mês")
        
        st.divider()
        
        st.subheader("Atividades")
        _render_activity_metrics(concluidas_mes, previstas_mes)
        
        st.divider()
        st.subheader("Compartilhar")
        message_mes = _generate_share_message(progresso_mes, concluidas_mes, previstas_mes, "mês", nome_usuario)
        _create_share_buttons(message_mes, "mes")
    
    # ==================== ABA: SEMANA ====================
    with tab_semana:
        st.subheader("Progresso da Semana")
        _render_progress_card(progresso_semana, concluidas_semana, previstas_semana, "semana")
        
        st.divider()
        
        st.subheader("Atividades")
        _render_activity_metrics(concluidas_semana, previstas_semana)
        
        st.divider()
        st.subheader("Compartilhar")
        message_semana = _generate_share_message(progresso_semana, concluidas_semana, previstas_semana, "semana", nome_usuario)
        _create_share_buttons(message_semana, "semana")
    
    # ==================== ABA: COMPARATIVO ====================
    with tab_comparativo:
        st.subheader("Comparativo: Semana vs Mês")
        
        col1, col2 = st.columns(2)
        
        with col1:
            with st.container(border=True):
                st.metric("Progresso Mês", f"{progresso_mes:.0f}%")
                nivel_mes = _get_achievement_level(progresso_mes)
                st.caption(nivel_mes)
        
        with col2:
            with st.container(border=True):
                st.metric("Progresso Semana", f"{progresso_semana:.0f}%")
                nivel_semana = _get_achievement_level(progresso_semana)
                st.caption(nivel_semana)
        
        st.divider()
        
        # Análise comparativa
        if progresso_semana > progresso_mes:
            diferenca = progresso_semana - progresso_mes
            st.info(f"Sua semana está {diferenca:.1f}% acima da média mensal")
        elif progresso_semana < progresso_mes:
            diferenca = progresso_mes - progresso_semana
            st.warning(f"Sua semana está {diferenca:.1f}% abaixo da média mensal")
        else:
            st.success("Você mantém o mesmo ritmo entre semana e mês")
        
        st.divider()
        
        # Taxa de conclusão
        col1, col2 = st.columns(2)
        with col1:
            taxa_mes = (concluidas_mes / max(1, previstas_mes)) * 100
            st.metric("Taxa Conclusão Mês", f"{taxa_mes:.0f}%")
        with col2:
            taxa_semana = (concluidas_semana / max(1, previstas_semana)) * 100
            st.metric("Taxa Conclusão Semana", f"{taxa_semana:.0f}%")
