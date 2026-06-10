-- Schema Supabase para o CuidaFácil
-- Rode este script no Supabase > SQL Editor.

create table if not exists usuarios (
  id_usuario text primary key,
  nome text,
  email text unique not null,
  data_cadastro text,
  ultimo_acesso text,
  ativo text default 'Sim'
);

alter table usuarios
  add column if not exists id_usuario text;

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

create table if not exists atividades (
  id_atividade text primary key,
  id_usuario text references usuarios(id_usuario) on delete cascade,
  titulo text,
  categoria text,
  descricao text,
  frequencia text,
  horario text,
  data_inicio text,
  data_fim text,
  dias_semana text,
  data_criacao text,
  data_cancelamento text,
  data_exclusao text,
  status text default 'Ativa',
  planta_id text,
  origem text default 'manual',
  tipo_cuidado text
);

create table if not exists execucoes (
  id_execucao text primary key,
  id_atividade text references atividades(id_atividade) on delete cascade,
  id_usuario text references usuarios(id_usuario) on delete cascade,
  data_referencia text,
  data_hora_execucao text
);

create table if not exists sessoes (
  id_sessao text primary key,
  id_usuario text references usuarios(id_usuario) on delete cascade,
  data_hora_acesso text
);

create table if not exists eventos_uso (
  id_evento text primary key,
  id_usuario text references usuarios(id_usuario) on delete cascade,
  evento text,
  data_hora text,
  detalhes text
);

create table if not exists configuracoes (
  chave text primary key,
  valor text,
  data_atualizacao text
);

create table if not exists plantas (
  id_planta text primary key,
  id_usuario text references usuarios(id_usuario) on delete cascade,
  nome_popular text not null,
  nome_cientifico text,
  ambiente text,
  observacoes text,
  resumo_cuidados text,
  data_criacao text,
  status text default 'Ativa'
);

create table if not exists recomendacoes_ia_plantas (
  id_recomendacao text primary key,
  id_planta text references plantas(id_planta) on delete cascade,
  prompt_usuario text,
  resposta_ia text,
  data_criacao text
);

alter table atividades
  drop constraint if exists atividades_planta_id_fkey;

alter table atividades
  add column if not exists id_atividade text;

alter table atividades
  add column if not exists id_usuario text;

alter table atividades
  add column if not exists titulo text;

alter table atividades
  add column if not exists categoria text;

alter table atividades
  add column if not exists descricao text;

alter table atividades
  add column if not exists frequencia text;

alter table atividades
  add column if not exists horario text;

alter table atividades
  add column if not exists data_inicio text;

alter table atividades
  add column if not exists data_fim text;

alter table atividades
  add column if not exists dias_semana text;

alter table atividades
  add column if not exists data_criacao text;

alter table atividades
  add column if not exists data_cancelamento text;

alter table atividades
  add column if not exists data_exclusao text;

alter table atividades
  add column if not exists status text;

alter table atividades
  add column if not exists planta_id text;

alter table atividades
  add column if not exists origem text;

alter table atividades
  add column if not exists tipo_cuidado text;

alter table atividades
  add constraint atividades_planta_id_fkey
  foreign key (planta_id) references plantas(id_planta) on delete set null;

-- Para projeto acadêmico/MVP simples com anon key:
-- O ideal em produção é ativar RLS e criar políticas por usuário autenticado.
-- Como este app usa login simples por e-mail, mantenha as tabelas sem RLS durante o MVP.
