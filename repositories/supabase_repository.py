from __future__ import annotations

import re
from datetime import datetime
from typing import Any

import pandas as pd

from config.settings import is_publishable_supabase_key, supabase_key, supabase_url

try:
    from supabase import create_client
except Exception:  # pragma: no cover
    create_client = None


REQUIRED_TABLES = {
    "usuarios": ["id_usuario", "nome", "email", "data_cadastro", "ultimo_acesso", "ativo"],
    "atividades": [
        "id_atividade", "id_usuario", "titulo", "categoria", "descricao",
        "frequencia", "horario", "data_inicio", "data_fim", "dias_semana",
        "data_criacao", "data_cancelamento", "data_exclusao", "status",
        "planta_id", "origem", "tipo_cuidado",
    ],
    "execucoes": ["id_execucao", "id_atividade", "id_usuario", "data_referencia", "data_execucao", "data_hora_execucao"],
    "sessoes": ["id_sessao", "id_usuario", "data_hora_acesso"],
    "eventos_uso": ["id_evento", "id_usuario", "evento", "data_hora", "detalhes"],
    "configuracoes": ["chave", "valor", "data_atualizacao"],
    "plantas": [
        "id_planta", "id_usuario", "nome_popular", "nome_cientifico", "ambiente",
        "observacoes", "resumo_cuidados", "data_criacao", "status",
    ],
    "recomendacoes_ia_plantas": [
        "id_recomendacao", "id_planta", "prompt_usuario", "resposta_ia", "data_criacao",
    ],
}

CRITICAL_UPDATE_COLUMNS = {
    "atividades": {"id_atividade", "id_usuario", "data_inicio", "data_criacao", "data_cancelamento", "data_exclusao", "data_fim"},
}

CRITICAL_INSERT_COLUMNS = {
    "atividades": {
        "id_atividade", "id_usuario", "titulo", "categoria", "descricao",
        "frequencia", "horario", "data_inicio", "data_fim", "dias_semana",
        "data_criacao", "data_cancelamento", "data_exclusao", "status",
        "planta_id", "origem", "tipo_cuidado",
    },
}


class SupabaseRepository:
    """Repositório Supabase com a mesma interface usada pelo app antigo em Google Sheets."""

    def __init__(self) -> None:
        self.enabled = False
        self.error_message = ""
        self.client = None

        url = supabase_url()
        key = supabase_key()

        if not url or not key:
            self.error_message = (
                "Supabase não configurado. Informe SUPABASE_URL e uma chave válida "
                "(SUPABASE_ANON_KEY, SUPABASE_KEY ou SUPABASE_SERVICE_ROLE_KEY) em st.secrets."
            )
            return

        if is_publishable_supabase_key():
            self.error_message = (
                "Chave Supabase no formato publishable detectada (sb_publishable_). "
                "Use SUPABASE_ANON_KEY (JWT) ou SUPABASE_SERVICE_ROLE_KEY em st.secrets."
            )
            return

        if create_client is None:
            self.error_message = "Dependência supabase não instalada. Adicione supabase ao requirements.txt."
            return

        try:
            self.client = create_client(url, key)
            self.enabled = True
        except Exception as exc:
            self.error_message = f"Erro ao conectar no Supabase: {exc}"
            self.enabled = False

    def _friendly_error(self, action: str, table_name: str, exc: Exception) -> str:
        text = str(exc or "").strip()
        text_lower = text.lower()

        if "invalid api key" in text_lower:
            return (
                f"Erro ao {action} em {table_name}: chave Supabase inválida. "
                "Use a anon key (SUPABASE_ANON_KEY) ou service role key válidas no secrets."
            )

        if "could not find the table" in text_lower:
            if table_name == "plantas":
                return (
                    "Tabela 'plantas' não encontrada no Supabase. "
                    "Execute o script database/supabase_schema.sql (ou crie a tabela plantas) no SQL Editor."
                )
            if table_name == "recomendacoes_ia_plantas":
                return (
                    "Tabela 'recomendacoes_ia_plantas' não encontrada no Supabase. "
                    "Execute o script database/supabase_schema.sql no SQL Editor."
                )
            return (
                f"Tabela '{table_name}' não encontrada no Supabase. "
                "Execute o script database/supabase_schema.sql no SQL Editor."
            )

        return f"Erro ao {action} em {table_name}: {text}"

    def _extract_missing_column(self, exc: Exception) -> str:
        text = str(exc or "")
        match = re.search(r"Could not find the '([^']+)' column", text)
        if not match:
            return ""
        return str(match.group(1)).strip()

    def _critical_missing_column_message(self, table_name: str, column_name: str) -> str:
        if table_name == "atividades" and column_name in CRITICAL_INSERT_COLUMNS["atividades"]:
            return (
                "Schema da tabela atividades incompleto para agendamento/cancelamento/exclusão. "
                f"A coluna '{column_name}' é obrigatória para registrar histórico. "
                "Execute o bloco SQL de migração da tela Configuração inicial para alinhar todas as colunas."
            )
        return (
            f"Schema da tabela {table_name} não contém a coluna obrigatória '{column_name}'. "
            "Atualize o schema no Supabase."
        )

    def _empty_df(self, table_name: str) -> pd.DataFrame:
        return pd.DataFrame(columns=REQUIRED_TABLES.get(table_name, []))

    def read(self, table_name: str) -> pd.DataFrame:
        headers = REQUIRED_TABLES.get(table_name, [])
        if table_name not in REQUIRED_TABLES:
            self.error_message = f"Tabela desconhecida: {table_name}"
            return pd.DataFrame()
        if not self.enabled or self.client is None:
            return self._empty_df(table_name)

        try:
            response = self.client.table(table_name).select("*").execute()
            df = pd.DataFrame(response.data or [])
            for col in headers:
                if col not in df.columns:
                    df[col] = ""
            return df[headers] if headers else df
        except Exception as exc:
            self.error_message = self._friendly_error("ler tabela", table_name, exc)
            return self._empty_df(table_name)

    def append(self, table_name: str, row: dict[str, Any]) -> bool:
        if table_name not in REQUIRED_TABLES:
            self.error_message = f"Tabela desconhecida: {table_name}"
            return False
        if not self.enabled or self.client is None:
            return False

        # Compatibilidade com schemas legados onde data_execucao e obrigatoria.
        if table_name == "execucoes":
            if not row.get("data_execucao"):
                row["data_execucao"] = row.get("data_hora_execucao") or datetime.utcnow().isoformat()
            if not row.get("data_hora_execucao"):
                row["data_hora_execucao"] = row.get("data_execucao") or datetime.utcnow().isoformat()

        allowed = set(REQUIRED_TABLES[table_name])
        clean_row = {k: v for k, v in row.items() if k in allowed}

        for _ in range(6):
            try:
                self.client.table(table_name).insert(clean_row).execute()
                return True
            except Exception as exc:
                missing_column = self._extract_missing_column(exc)
                if missing_column and missing_column in clean_row:
                    critical_columns = CRITICAL_INSERT_COLUMNS.get(table_name, set())
                    if missing_column in critical_columns:
                        self.error_message = self._critical_missing_column_message(table_name, missing_column)
                        return False

                    clean_row.pop(missing_column, None)
                    continue

                self.error_message = self._friendly_error("salvar", table_name, exc)
                return False

        self.error_message = (
            f"Erro ao salvar em {table_name}: não foi possível compatibilizar o payload com o schema da tabela."
        )
        return False

    def update_user_last_access(self, id_usuario: str, data_hora: str) -> bool:
        return self.update_row_values("usuarios", "id_usuario", id_usuario, {"ultimo_acesso": data_hora})

    def update_row_values(self, table_name: str, key_column: str, key_value: str, updates: dict[str, Any]) -> bool:
        if table_name not in REQUIRED_TABLES:
            self.error_message = f"Tabela desconhecida: {table_name}"
            return False
        if not self.enabled or self.client is None:
            return False

        allowed = set(REQUIRED_TABLES[table_name])
        clean_updates = {k: v for k, v in updates.items() if k in allowed}

        for _ in range(6):
            try:
                self.client.table(table_name).update(clean_updates).eq(key_column, key_value).execute()
                return True
            except Exception as exc:
                missing_column = self._extract_missing_column(exc)
                if missing_column and missing_column in clean_updates:
                    critical_columns = CRITICAL_UPDATE_COLUMNS.get(table_name, set())
                    if missing_column in critical_columns:
                        self.error_message = self._critical_missing_column_message(table_name, missing_column)
                        return False

                    clean_updates.pop(missing_column, None)
                    if not clean_updates:
                        return True
                    continue

                self.error_message = self._friendly_error("atualizar", table_name, exc)
                return False

        self.error_message = (
            f"Erro ao atualizar {table_name}: não foi possível compatibilizar os campos com o schema da tabela."
        )
        return False

    def delete_rows_where(self, table_name: str, filters: dict[str, Any]) -> int:
        if table_name not in REQUIRED_TABLES:
            self.error_message = f"Tabela desconhecida: {table_name}"
            return 0
        if not self.enabled or self.client is None:
            return 0

        try:
            query = self.client.table(table_name).delete()
            for key, value in filters.items():
                query = query.eq(key, value)
            query.execute()
            return 1
        except Exception as exc:
            self.error_message = self._friendly_error("excluir", table_name, exc)
            return 0

    def upsert_config(self, chave: str, valor: str, data_atualizacao: str) -> bool:
        if not self.enabled or self.client is None:
            return False
        try:
            self.client.table("configuracoes").upsert({
                "chave": chave,
                "valor": valor,
                "data_atualizacao": data_atualizacao,
            }, on_conflict="chave").execute()
            return True
        except Exception as exc:
            self.error_message = self._friendly_error("salvar configuração", "configuracoes", exc)
            return False

    def read_config(self) -> dict[str, str]:
        df = self.read("configuracoes")
        if df.empty:
            return {}
        return {str(row.get("chave", "")).strip(): str(row.get("valor", "")).strip() for _, row in df.iterrows() if str(row.get("chave", "")).strip()}

    def status(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "provider": "Supabase",
            "error_message": self.error_message,
            "tables": list(REQUIRED_TABLES.keys()),
        }
