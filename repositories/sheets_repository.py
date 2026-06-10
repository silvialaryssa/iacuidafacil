from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

try:
    import gspread
    from google.oauth2.service_account import Credentials
except Exception:
    gspread = None
    Credentials = None

from config.settings import has_google_sheets_config, spreadsheet_id

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

REQUIRED_SHEETS = {
    "usuarios": ["id_usuario", "nome", "email", "data_cadastro", "ultimo_acesso", "ativo"],
    "atividades": [
        "id_atividade", "id_usuario", "titulo", "categoria", "descricao",
        "frequencia", "horario", "data_inicio", "data_fim", "dias_semana",
        "data_criacao", "data_cancelamento", "data_exclusao", "status",
    ],
    "execucoes": [
        "id_execucao", "id_atividade", "id_usuario",
        "data_referencia", "data_hora_execucao",
    ],
    "sessoes": ["id_sessao", "id_usuario", "data_hora_acesso"],
    "eventos_uso": ["id_evento", "id_usuario", "evento", "data_hora", "detalhes"],
    "configuracoes": ["chave", "valor", "data_atualizacao"],
}


class SheetsRepository:
    def __init__(self) -> None:
        self.enabled = False
        self.spreadsheet = None
        self.error_message = ""
        self._worksheets = {}

        if not has_google_sheets_config():
            self.error_message = "Google Sheets não configurado em st.secrets."
            return

        if gspread is None or Credentials is None:
            self.error_message = "Dependências gspread/google-auth não instaladas."
            return

        try:
            creds_dict = dict(st.secrets["gcp_service_account"])
            credentials = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
            client = gspread.authorize(credentials)
            self.spreadsheet = client.open_by_key(spreadsheet_id())
            self.enabled = True
            self.ensure_sheets()
        except Exception as exc:
            self.error_message = str(exc)
            self.enabled = False

    def _worksheet(self, sheet_name: str):
        if sheet_name not in self._worksheets:
            self._worksheets[sheet_name] = self.spreadsheet.worksheet(sheet_name)
        return self._worksheets[sheet_name]

    def ensure_sheets(self) -> None:
        if not self.enabled or not self.spreadsheet:
            return

        existing = {ws.title: ws for ws in self.spreadsheet.worksheets()}

        for sheet_name, headers in REQUIRED_SHEETS.items():
            if sheet_name not in existing:
                ws = self.spreadsheet.add_worksheet(
                    title=sheet_name,
                    rows=1000,
                    cols=max(len(headers), 10),
                )
                ws.append_row(headers, value_input_option="USER_ENTERED")
                self._worksheets[sheet_name] = ws
            else:
                ws = existing[sheet_name]
                self._worksheets[sheet_name] = ws
                current_headers = ws.row_values(1)

                if not current_headers:
                    ws.append_row(headers, value_input_option="USER_ENTERED")
                    continue

                missing = [h for h in headers if h not in current_headers]
                if missing:
                    ws.update("1:1", [current_headers + missing])

    def read(self, sheet_name: str) -> pd.DataFrame:
        headers = REQUIRED_SHEETS.get(sheet_name, [])

        if not self.enabled or not self.spreadsheet:
            return pd.DataFrame(columns=headers)

        try:
            ws = self._worksheet(sheet_name)
            values = ws.get_all_values()

            if not values:
                return pd.DataFrame(columns=headers)

            actual_headers = [str(h).strip() for h in values[0]]
            rows = values[1:]

            records = []
            for row in rows:
                if not any(str(cell).strip() for cell in row):
                    continue

                record = {}
                for header in headers:
                    if header in actual_headers:
                        idx = actual_headers.index(header)
                        record[header] = row[idx] if idx < len(row) else ""
                    else:
                        record[header] = ""

                records.append(record)

            df = pd.DataFrame(records, columns=headers)

            for col in headers:
                if col not in df.columns:
                    df[col] = ""

            return df[headers] if headers else df

        except Exception as exc:
            self.error_message = f"Erro ao ler aba {sheet_name}: {exc}"
            return pd.DataFrame(columns=headers)

    def append(self, sheet_name: str, row: dict[str, Any]) -> bool:
        """Adiciona uma linha respeitando a ordem real dos cabeçalhos no Google Sheets.

        Isso é importante porque uma planilha antiga pode ter cabeçalhos em ordem diferente
        da ordem definida em REQUIRED_SHEETS. Se gravarmos pela ordem fixa do código,
        os dados ficam em colunas erradas e a atividade é salva, mas não aparece na tela.
        """
        if sheet_name not in REQUIRED_SHEETS:
            self.error_message = f"Aba desconhecida: {sheet_name}"
            return False

        if not self.enabled or not self.spreadsheet:
            self.error_message = self.error_message or "Google Sheets não está conectado."
            return False

        try:
            ws = self._worksheet(sheet_name)

            actual_headers = [str(h).strip() for h in ws.row_values(1)]

            if not actual_headers:
                actual_headers = REQUIRED_SHEETS[sheet_name]
                ws.append_row(actual_headers, value_input_option="USER_ENTERED")

            # Garante que todos os campos esperados existam no cabeçalho real.
            changed = False
            for header in REQUIRED_SHEETS[sheet_name]:
                if header not in actual_headers:
                    actual_headers.append(header)
                    changed = True

            if changed:
                if getattr(ws, "col_count", len(actual_headers)) < len(actual_headers):
                    ws.add_cols(len(actual_headers) - ws.col_count)

                for col_number, header in enumerate(actual_headers, start=1):
                    ws.update_cell(1, col_number, header)

            values = [row.get(header, "") for header in actual_headers]

            ws.append_row(values, value_input_option="USER_ENTERED")

            return True

        except Exception as exc:
            self.error_message = f"Erro ao salvar na aba {sheet_name}: {exc}"
            return False

    def update_user_last_access(self, id_usuario: str, data_hora: str) -> bool:
        if not self.enabled or not self.spreadsheet:
            return False

        try:
            ws = self._worksheet("usuarios")
            values = ws.get_all_values()

            if not values:
                return False

            headers = values[0]
            id_idx = headers.index("id_usuario") + 1
            last_idx = headers.index("ultimo_acesso") + 1

            for row_number, row in enumerate(values[1:], start=2):
                if len(row) >= id_idx and row[id_idx - 1] == id_usuario:
                    ws.update_cell(row_number, last_idx, data_hora)
                    return True

            return False
        except Exception as exc:
            self.error_message = str(exc)
            return False


    def delete_rows_where(self, sheet_name: str, filters: dict[str, Any]) -> int:
        """Remove linhas da aba que atendam todos os filtros informados.

        Exemplo:
            delete_rows_where("execucoes", {
                "id_usuario": "U123",
                "id_atividade": "A123"
            })

        Retorna a quantidade de linhas removidas.
        """
        if sheet_name not in REQUIRED_SHEETS:
            self.error_message = f"Aba desconhecida: {sheet_name}"
            return 0

        if not self.enabled or not self.spreadsheet:
            return 0

        try:
            ws = self._worksheet(sheet_name)
            values = ws.get_all_values()

            if len(values) <= 1:
                return 0

            headers = values[0]
            filter_indexes = {}

            for key, expected_value in filters.items():
                if key not in headers:
                    return 0
                filter_indexes[headers.index(key)] = str(expected_value)

            rows_to_delete = []

            for row_number, row in enumerate(values[1:], start=2):
                match = True

                for col_idx, expected_value in filter_indexes.items():
                    actual_value = row[col_idx] if col_idx < len(row) else ""
                    if str(actual_value) != expected_value:
                        match = False
                        break

                if match:
                    rows_to_delete.append(row_number)

            for row_number in reversed(rows_to_delete):
                ws.delete_rows(row_number)

            return len(rows_to_delete)

        except Exception as exc:
            self.error_message = str(exc)
            return 0


    def update_row_values(self, sheet_name: str, key_column: str, key_value: str, updates: dict[str, Any]) -> bool:
        if sheet_name not in REQUIRED_SHEETS:
            self.error_message = f"Aba desconhecida: {sheet_name}"
            return False

        if not self.enabled or not self.spreadsheet:
            return False

        try:
            ws = self._worksheet(sheet_name)
            values = ws.get_all_values()

            if not values:
                return False

            headers = values[0]
            if key_column not in headers:
                return False

            key_idx = headers.index(key_column)

            for row_number, row in enumerate(values[1:], start=2):
                actual_value = row[key_idx] if key_idx < len(row) else ""
                if str(actual_value) == str(key_value):
                    for col_name, new_value in updates.items():
                        if col_name not in headers:
                            continue
                        col_idx = headers.index(col_name) + 1
                        ws.update_cell(row_number, col_idx, new_value)
                    return True

            return False

        except Exception as exc:
            self.error_message = str(exc)
            return False


    def upsert_config(self, chave: str, valor: str, data_atualizacao: str) -> bool:
        if not self.enabled or not self.spreadsheet:
            self.error_message = self.error_message or "Google Sheets não está conectado."
            return False

        try:
            ws = self._worksheet("configuracoes")
            values = ws.get_all_values()

            if not values:
                ws.append_row(REQUIRED_SHEETS["configuracoes"], value_input_option="USER_ENTERED")
                values = ws.get_all_values()

            headers = values[0]

            if "chave" not in headers:
                headers = REQUIRED_SHEETS["configuracoes"]
                ws.update("1:1", [headers])

            chave_idx = headers.index("chave")
            valor_idx = headers.index("valor") + 1
            data_idx = headers.index("data_atualizacao") + 1

            for row_number, row in enumerate(values[1:], start=2):
                atual = row[chave_idx] if chave_idx < len(row) else ""
                if str(atual).strip() == str(chave).strip():
                    ws.update_cell(row_number, valor_idx, valor)
                    ws.update_cell(row_number, data_idx, data_atualizacao)
                    return True

            ws.append_row([chave, valor, data_atualizacao], value_input_option="USER_ENTERED")
            return True

        except Exception as exc:
            self.error_message = f"Erro ao salvar configuração: {exc}"
            return False

    def read_config(self) -> dict[str, str]:
        df = self.read("configuracoes")

        if df.empty or "chave" not in df.columns or "valor" not in df.columns:
            return {}

        config: dict[str, str] = {}

        for _, row in df.iterrows():
            chave = str(row.get("chave", "")).strip()
            valor = str(row.get("valor", "")).strip()
            if chave:
                config[chave] = valor

        return config

    def status(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "spreadsheet_id": spreadsheet_id(),
            "error_message": self.error_message,
            "required_sheets": list(REQUIRED_SHEETS.keys()),
        }
