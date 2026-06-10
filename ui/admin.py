from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from services.analytics_service import get_analytics_service
from config.settings import has_chatgpt_config, has_gemini_config
from services.app_service import all_data, get_ai_settings, save_ai_settings
from services.metrics_service import (
    calculate_admin_metrics,
    category_counts,
    completions_by_day,
    sessions_by_day,
)
from ui.components import figure_card, metric_card


def render_admin(user: dict) -> None:
    if not st.session_state.get("admin_opened_tracked"):
        get_analytics_service().track("admin_opened", user.get("email", ""))
        st.session_state["admin_opened_tracked"] = True

    st.subheader("Admin • Métricas do Produto")
    st.markdown(
        """
        <div class="section-intro">
            Use os indicadores para identificar engajamento, retenção e pontos de melhoria na jornada do usuário.
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("🤖 Configuração de IA", expanded=False):
        ai_settings = get_ai_settings()
        provider_options = {
            "gemini": "Google Gemini",
            "openai": "OpenAI / ChatGPT",
        }

        provider_labels = list(provider_options.values())
        current_provider = ai_settings.get("provider", "gemini")
        current_label = provider_options.get(current_provider, "Google Gemini")

        col_ai1, col_ai2 = st.columns([1, 1])

        with col_ai1:
            provider_label = st.selectbox(
                "Provedor de IA",
                provider_labels,
                index=provider_labels.index(current_label),
            )

        selected_provider = {
            value: key for key, value in provider_options.items()
        }[provider_label]

        default_model = ai_settings.get("model", "")
        if selected_provider == "gemini" and not default_model.startswith("gemini"):
            default_model = "gemini-2.5-flash"
        elif selected_provider == "openai" and default_model.startswith("gemini"):
            default_model = "gpt-4.1-mini"

        with col_ai2:
            model = st.text_input(
                "Modelo",
                value=default_model,
                help="Exemplos: gemini-2.5-flash ou gpt-4.1-mini",
            )

        c_status1, c_status2 = st.columns(2)
        with c_status1:
            if has_gemini_config():
                st.success("Gemini API Key configurada.")
            else:
                st.warning("Gemini API Key não configurada nos Secrets.")

        with c_status2:
            if has_chatgpt_config():
                st.success("OpenAI API Key configurada.")
            else:
                st.warning("OpenAI API Key não configurada nos Secrets.")

        if st.button("Salvar configuração de IA", use_container_width=True):
            try:
                save_ai_settings(selected_provider, model)
                st.success("Configuração de IA salva com sucesso.")
                st.rerun()
            except Exception as exc:
                st.error(f"Erro ao salvar configuração de IA: {exc}")

        st.caption(
            "A escolha é salva na aba configuracoes do Google Sheets. "
            "As chaves continuam protegidas nos Secrets do Streamlit."
        )

    st.divider()

    help_col1, help_col2, help_col3 = st.columns(3)
    with help_col1:
        figure_card("👥", "Aquisição", "Usuários e MAU mostram alcance e base ativa do produto.")
    with help_col2:
        figure_card("🔁", "Retenção", "D1, D7 e D30 indicam constância após o cadastro.")
    with help_col3:
        figure_card("✅", "Conclusão", "Taxa de conclusão ajuda a medir valor percebido das atividades.")

    data = all_data()
    metrics = calculate_admin_metrics(data)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Usuários", str(metrics["usuarios"]))
    with c2:
        metric_card("MAU", str(metrics["mau"]))
    with c3:
        metric_card("Retenção D7", f'{metrics["retencao_d7"]}%')
    with c4:
        metric_card("Ativação", f'{metrics["ativacao"]}%')

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        metric_card("Atividades", str(metrics["atividades"]))
    with c6:
        metric_card("Conclusões", str(metrics["execucoes"]))
    with c7:
        metric_card("Taxa conclusão", f'{metrics["conclusao"]}%')
    with c8:
        metric_card("DAU / WAU", f'{metrics["dau"]} / {metrics["wau"]}')

    st.divider()

    st.markdown("### Retenção")
    retention_df = pd.DataFrame({
        "Período": ["D1", "D7", "D30"],
        "Retenção (%)": [
            metrics["retencao_d1"],
            metrics["retencao_d7"],
            metrics["retencao_d30"],
        ],
    })
    fig_ret = px.bar(
        retention_df,
        x="Período",
        y="Retenção (%)",
        text="Retenção (%)",
        title="Retenção de usuários",
    )
    st.plotly_chart(fig_ret, use_container_width=True)

    st.markdown("### Funil de conversão")
    usuarios = metrics["usuarios"]
    ativados = data["atividades"]["id_usuario"].nunique() if not data["atividades"].empty else 0
    concluintes = data["execucoes"]["id_usuario"].nunique() if not data["execucoes"].empty else 0
    recorrentes = metrics["recorrentes"]

    funnel = pd.DataFrame({
        "Etapa": ["Cadastrou", "Criou atividade", "Concluiu atividade", "Voltou ao app"],
        "Usuários": [usuarios, ativados, concluintes, recorrentes],
    })

    fig_funnel = px.bar(
        funnel,
        x="Etapa",
        y="Usuários",
        text="Usuários",
        title="Funil do CuidaFácil",
    )
    st.plotly_chart(fig_funnel, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Categorias mais usadas")
        cat = category_counts(data["atividades"])
        if not cat.empty:
            fig = px.bar(cat, x="categoria", y="quantidade", text="quantidade")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Ainda não há categorias para exibir.")

    with col2:
        st.markdown("### Usuários ativos por dia")
        sess = sessions_by_day(data["sessoes"])
        if not sess.empty:
            fig2 = px.line(sess, x="data", y="usuarios_ativos", markers=True)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Ainda não há sessões para exibir.")

    st.markdown("### Conclusões por dia")
    daily_done = completions_by_day(data["execucoes"])
    if not daily_done.empty:
        fig3 = px.line(daily_done, x="data", y="conclusoes", markers=True)
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("Ainda não há conclusões para exibir.")

    with st.expander("Ver dados brutos"):
        for name, df in data.items():
            st.write(f"#### {name}")
            st.dataframe(df, use_container_width=True)
