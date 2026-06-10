# CuidaFácil — Streamlit Cloud + Google Sheets + GA4

Aplicativo responsivo com autenticação por e-mail e senha via Supabase Auth, criação e conclusão de atividades, progresso do usuário e área Admin com métricas de produto.

## Funcionalidades

- Login com e-mail e senha via Supabase Auth
- Tela de configuração inicial
- Cadastro de atividades
- Conclusão de atividades
- Progresso do usuário
- Dashboard Admin com cards, funil e retenção D1/D7/D30
- Cuidador IA de Plantas com opções de diagnóstico e plano de cuidados
- Integração Google Sheets via `sheets_repository.py`
- Integração Google Analytics 4 via Measurement Protocol
- Integração ChatGPT API para orientações de cuidado de plantas
- Deploy pronto para Streamlit Community Cloud
- Provérbios em `assets/proverbios.json`, sem gravar no banco

## Como rodar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Como configurar

Copie:

```text
.streamlit/secrets.example.toml
```

para:

```text
.streamlit/secrets.toml
```

Preencha o `spreadsheet_id`, as credenciais da Service Account e, se quiser, as chaves do GA4.

Para autenticação no Supabase, adicione também:

```toml
SUPABASE_URL = "https://seu-projeto.supabase.co"
SUPABASE_ANON_KEY = "sua-anon-key"
# opcional legado:
# SUPABASE_KEY = "sua-anon-key"
```

No painel do Supabase, habilite `Authentication > Providers > Email`.

Para habilitar o Cuidador IA de Plantas, adicione também:

```toml
chatgpt_api_key = "sk-..."
chatgpt_model = "gpt-4.1-mini"
chatgpt_api_base_url = "https://api.openai.com/v1"
```

## Abas do Google Sheets

Você só precisa criar uma planilha vazia no Google Sheets. O app cria/valida automaticamente as abas:

- usuarios
- atividades
- execucoes
- sessoes
- eventos_uso

Compartilhe a planilha com o `client_email` da Service Account como **Editor**.

## Admin

A aba Admin aparece quando o e-mail usado no login for igual ao valor de:

```toml
admin_email = "admin@cuidafacil.com"
```

## Streamlit Community Cloud

1. Suba este projeto para o GitHub.
2. Crie o app no Streamlit Cloud apontando para `app.py`.
3. Em **App > Settings > Secrets**, cole o conteúdo do seu `secrets.toml`.
4. Faça o deploy.

## Documentação de arquitetura

- Desenho da arquitetura da solução: [docs/arquitetura-solucao.md](docs/arquitetura-solucao.md)


## Ajustes de performance

Esta versão evita que todas as telas sejam processadas ao mesmo tempo. A navegação usa `st.radio` no menu lateral, em vez de `st.tabs`, porque `st.tabs` executa o conteúdo de todas as abas a cada recarregamento.

Também há cache de leitura do Google Sheets com TTL de 45 segundos em `services/app_service.py`. Após gravações, o cache é limpo automaticamente.

## Migração para Supabase

1. Crie um projeto gratuito no Supabase.
2. Abra `database/supabase_schema.sql` no Supabase SQL Editor e execute o script.
3. Configure `.streamlit/secrets.toml` ou os secrets do Streamlit Cloud:

```toml
SUPABASE_URL = "https://seu-projeto.supabase.co"
SUPABASE_ANON_KEY = "sua-anon-key"
```

4. Garanta no schema da tabela `atividades` as colunas abaixo (necessárias para criação, cancelamento e exclusão de agendamentos):

```sql
alter table usuarios add column if not exists id_usuario text;

do $$
begin
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
```

O app agora usa `repositories/supabase_repository.py` em vez de Google Sheets.

### Supabase Auth (e-mail + senha)

1. No Supabase, abra **Authentication > Providers**.
2. Ative o provider **Email**.
3. Opcional: ative confirmação de e-mail para novos cadastros.
4. No app, use o menu lateral em **Quero me cadastrar** para criar conta.
5. Entre em **Já tenho cadastro** com e-mail e senha.

## Funcionalidade Planta com IA

A tela **Planta com IA** pede para a IA retornar JSON estruturado. O usuário revisa o plano e, ao confirmar, o app cadastra a planta e cria automaticamente tarefas semanais em `atividades` com `origem = 'ia_planta'`.
