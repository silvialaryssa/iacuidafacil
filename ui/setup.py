from __future__ import annotations

import streamlit as st

from config.settings import (
    chatgpt_model,
    gemini_model,
    has_chatgpt_config,
    has_gemini_config,
    has_ga4_config,
    has_google_sheets_config,
    has_supabase_config,
    spreadsheet_id,
)
from services.auth_service import certify_supabase_configuration
from services.app_service import repository_status
from ui.components import figure_card


def render_setup() -> None:
    from config.settings import (
        chatgpt_api_key,
        default_ai_provider,
        gemini_api_key,
    )

    st.subheader("🔍 Diagnóstico IA")

    st.write("Secrets carregados:")
    st.write(list(st.secrets.keys()))

    st.write("Gemini:", bool(gemini_api_key()))
    st.write("OpenAI:", bool(chatgpt_api_key()))
    st.write("Provider:", default_ai_provider())
        
    st.subheader("Configuração inicial")
    st.markdown(
        """
        <div class="section-intro">
            Configure as integrações em poucos passos para liberar analytics, dados e IA no aplicativo.
        </div>
        """,
        unsafe_allow_html=True,
    )

    info_col1, info_col2 = st.columns(2)
    with info_col1:
        figure_card("🧩", "Integrações", "Google Sheets e GA4 podem funcionar juntos para visão completa do uso.")
    with info_col2:
        figure_card("🤖", "Assistente de plantas", "Configure a chave da API para ativar o Cuidador IA de Plantas.")

    status = repository_status()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("### Google Sheets")
        if has_google_sheets_config() and status.get("enabled"):
            st.success("Google Sheets configurado e conectado.")
        elif has_google_sheets_config() and not status.get("enabled"):
            st.warning("Credenciais encontradas, mas não foi possível conectar.")
            st.code(status.get("error_message", "Erro não informado."))
        else:
            st.info("Google Sheets ainda não configurado.")

        st.write("`spreadsheet_id` atual:")
        st.code(spreadsheet_id() or "não informado")

    with col2:
        st.markdown("### Google Analytics 4")
        if has_ga4_config():
            st.success("GA4 configurado.")
        else:
            st.info("GA4 ainda não configurado. O app funciona, mas sem enviar eventos.")

    with col3:
        st.markdown("### IA do Cuidador")
        if has_gemini_config() or has_chatgpt_config():
            st.success("IA configurada.")
            if has_gemini_config():
                st.caption(f"Gemini disponível: {gemini_model()}")
            if has_chatgpt_config():
                st.caption(f"OpenAI disponível: {chatgpt_model()}")
        else:
            st.info("Nenhuma API de IA configurada. A funcionalidade de IA ficará desativada.")

    with col4:
        st.markdown("### Supabase")
        cert = certify_supabase_configuration()
        if has_supabase_config() and status.get("enabled") and cert.get("ok"):
            st.success("Supabase configurado e conectado.")
            st.caption("Auth por e-mail/senha ativo no app.")
        elif has_supabase_config() and not status.get("enabled"):
            st.warning("Credenciais encontradas, mas não foi possível conectar.")
            st.code(status.get("error_message", "Erro não informado."))
        else:
            st.info("Supabase ainda não configurado.")

    st.markdown("### Certificação da Configuração Supabase")
    cert = certify_supabase_configuration()

    if cert.get("ok"):
        st.success(str(cert.get("message", "Certificação Supabase aprovada.")))
    else:
        st.error(str(cert.get("message", "Certificação Supabase reprovada.")))

    for check in cert.get("checks", []):
        check_name = str(check.get("name", "Validação"))
        check_detail = str(check.get("detail", ""))
        if check.get("ok"):
            st.success(f"{check_name}: {check_detail}")
        else:
            st.warning(f"{check_name}: {check_detail}")

    st.divider()

    st.markdown("### Tabelas esperadas no Supabase")
    st.write(", ".join(status.get("tables", [])))

    st.markdown("### Como configurar")
    st.code(
        '''
admin_email = "seu_email@gmail.com"
spreadsheet_id = "ID_DA_PLANILHA"
ga4_measurement_id = "G-XXXXXXXXXX"
ga4_api_secret = "API_SECRET"
# IA - escolha padrão inicial; a área Admin pode trocar depois
ai_provider = "gemini"

# Google Gemini
gemini_api_key = "SUA_CHAVE_GEMINI"
gemini_model = "gemini-2.5-flash"
gemini_api_base_url = "https://generativelanguage.googleapis.com/v1beta"

# OpenAI / ChatGPT
chatgpt_api_key = "sk-..."
chatgpt_model = "gpt-4.1-mini"
chatgpt_api_base_url = "https://api.openai.com/v1"

# Supabase (dados + autenticação)
SUPABASE_URL = "https://seu-projeto.supabase.co"
SUPABASE_ANON_KEY = "sua-anon-key"
# Opcional legado:
# SUPABASE_KEY = "sua-anon-key"

[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "..."
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
universe_domain = "googleapis.com"
        '''.strip(),
        language="toml",
    )

    st.markdown("### SQL de migração (Supabase)")
    st.caption("Execute no Supabase SQL Editor para garantir tabelas e colunas do app (atividades e plantas).")
    st.code(
        '''
alter table usuarios add column if not exists id_usuario text;

do $$
begin
create table if not exists public.plantas (
    id_planta text primary key,
    id_usuario text,
    nome_popular text not null,
    nome_cientifico text,
    ambiente text,
    observacoes text,
    resumo_cuidados text,
    data_criacao text,
    status text default 'Ativa'
);

create table if not exists public.recomendacoes_ia_plantas (
    id_recomendacao text primary key,
    id_planta text,
    prompt_usuario text,
    resposta_ia text,
    data_criacao text
);

do $$
begin
    if exists (
        select 1
        from information_schema.columns
        where table_schema = 'public' and table_name = 'plantas' and column_name = 'id_usuario'
    ) and exists (
        select 1
        from information_schema.columns
        where table_schema = 'public' and table_name = 'usuarios' and column_name = 'id_usuario'
    ) and exists (
        select 1
        from pg_constraint c
        join pg_class t on t.oid = c.conrelid
        join pg_attribute a on a.attrelid = t.oid and a.attnum = any(c.conkey)
        where t.relname = 'usuarios'
            and a.attname = 'id_usuario'
            and c.contype in ('p', 'u')
    ) and not exists (
        select 1 from pg_constraint where conname = 'plantas_id_usuario_fkey'
    ) then
        alter table public.plantas
            add constraint plantas_id_usuario_fkey
            foreign key (id_usuario) references public.usuarios(id_usuario) on delete cascade;
    end if;
end $$;

do $$
begin
    if exists (
        select 1
        from information_schema.columns
        where table_schema = 'public' and table_name = 'recomendacoes_ia_plantas' and column_name = 'id_planta'
    ) and exists (
        select 1
        from information_schema.columns
        where table_schema = 'public' and table_name = 'plantas' and column_name = 'id_planta'
    ) and exists (
        select 1
        from pg_constraint c
        join pg_class t on t.oid = c.conrelid
        join pg_attribute a on a.attrelid = t.oid and a.attnum = any(c.conkey)
        where t.relname = 'plantas'
            and a.attname = 'id_planta'
            and c.contype in ('p', 'u')
    ) and not exists (
        select 1 from pg_constraint where conname = 'recomendacoes_ia_plantas_id_planta_fkey'
    ) then
        alter table public.recomendacoes_ia_plantas
            add constraint recomendacoes_ia_plantas_id_planta_fkey
            foreign key (id_planta) references public.plantas(id_planta) on delete cascade;
    end if;
end $$;

    if not exists (
        select 1
        from pg_constraint
        where conname = 'usuarios_pkey'
    ) then
        begin
            alter table public.usuarios add constraint usuarios_pkey primary key (id_usuario);
        exception when others then
            null;
        end;
    end if;
end $$;

alter table atividades add column if not exists id_atividade text;
alter table atividades add column if not exists id_usuario text;
    alter table atividades add column if not exists titulo text;
    alter table atividades add column if not exists categoria text;
    alter table atividades add column if not exists descricao text;
    alter table atividades add column if not exists frequencia text;
    alter table atividades add column if not exists horario text;
alter table atividades add column if not exists data_inicio text;
alter table atividades add column if not exists data_fim text;
    alter table atividades add column if not exists dias_semana text;
alter table atividades add column if not exists data_criacao text;
alter table atividades add column if not exists data_cancelamento text;
alter table atividades add column if not exists data_exclusao text;
    alter table atividades add column if not exists status text;
    alter table atividades add column if not exists planta_id text;
    alter table atividades add column if not exists origem text;
    alter table atividades add column if not exists tipo_cuidado text;

do $$
begin
    if exists (
        select 1
        from information_schema.columns
        where table_schema = 'public' and table_name = 'atividades' and column_name = 'id_usuario'
    ) and exists (
        select 1
        from information_schema.columns
        where table_schema = 'public' and table_name = 'usuarios' and column_name = 'id_usuario'
    ) and exists (
        select 1
        from pg_constraint c
        join pg_class t on t.oid = c.conrelid
        join pg_attribute a on a.attrelid = t.oid and a.attnum = any(c.conkey)
        where t.relname = 'usuarios'
            and a.attname = 'id_usuario'
            and c.contype in ('p', 'u')
    ) and not exists (
        select 1 from pg_constraint where conname = 'atividades_id_usuario_fkey'
    ) then
        alter table public.atividades
            add constraint atividades_id_usuario_fkey
            foreign key (id_usuario) references public.usuarios(id_usuario) on delete cascade;
    end if;
end $$;
        '''.strip(),
        language="sql",
    )

    st.info("No Streamlit Cloud, cole esse conteúdo em App > Settings > Secrets.")
