from __future__ import annotations

import re
from typing import Any

import requests

from config.settings import is_publishable_supabase_key, supabase_key, supabase_url

try:
    from supabase import create_client
except Exception:  # pragma: no cover
    create_client = None


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _auth_client():
    if create_client is None:
        raise RuntimeError("Dependência supabase não instalada. Adicione supabase ao requirements.txt.")

    url = supabase_url()
    key = supabase_key()

    if not url or not key:
        raise RuntimeError("Supabase Auth não configurado. Informe SUPABASE_URL e SUPABASE_KEY em st.secrets.")

    if is_publishable_supabase_key():
        raise RuntimeError(
            "Chave Supabase no formato publishable detectada (sb_publishable_). "
            "Para este app, use SUPABASE_ANON_KEY (JWT) ou SUPABASE_SERVICE_ROLE_KEY."
        )

    return create_client(url, key)


def _friendly_auth_error(exc: Exception) -> str:
    text = str(exc or "").strip()
    text_lower = text.lower()

    if "invalid api key" in text_lower:
        return (
            "Chave do Supabase inválida. Confira os secrets SUPABASE_KEY (ou SUPABASE_ANON_KEY) "
            "e SUPABASE_URL na tela de Configuração inicial."
        )
    if "invalid login credentials" in text_lower:
        return "E-mail ou senha inválidos."
    if "email not confirmed" in text_lower:
        return "E-mail ainda não confirmado. Verifique sua caixa de entrada para concluir o cadastro."
    if "user already registered" in text_lower:
        return "Este e-mail já está cadastrado. Use a opção 'Já tenho cadastro'."
    if "password" in text_lower and "weak" in text_lower:
        return "Senha muito fraca. Use ao menos 6 caracteres."
    if "signup is disabled" in text_lower:
        return "Cadastro por e-mail está desativado no Supabase Auth."
    if "email rate limit exceeded" in text_lower:
        return "Muitas tentativas em pouco tempo. Aguarde alguns minutos e tente novamente."

    return f"Falha na autenticação Supabase: {text or 'erro desconhecido.'}"


def certify_supabase_configuration() -> dict[str, Any]:
    url = supabase_url().strip()
    key = supabase_key().strip()
    checks: list[dict[str, str]] = []

    def add_check(name: str, ok: bool, detail: str) -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    has_url = bool(url)
    add_check(
        "SUPABASE_URL presente",
        has_url,
        "OK" if has_url else "Defina SUPABASE_URL em st.secrets.",
    )

    has_key = bool(key)
    add_check(
        "SUPABASE_KEY/SUPABASE_ANON_KEY presente",
        has_key,
        "OK" if has_key else "Defina SUPABASE_KEY (ou SUPABASE_ANON_KEY) em st.secrets.",
    )

    if not has_url or not has_key:
        return {
            "ok": False,
            "message": "Configuração incompleta do Supabase.",
            "checks": checks,
        }

    url_ok = bool(re.match(r"^https://[a-z0-9-]+\.supabase\.co/?$", url, re.IGNORECASE))
    add_check(
        "Formato da URL",
        url_ok,
        "OK" if url_ok else "Use formato: https://SEU-PROJETO.supabase.co",
    )

    key_has_placeholder = any(token in key for token in ["<", ">", "SEU_", "SUA_"])
    publishable_key = key.startswith("sb_publishable_")
    key_ok = not key_has_placeholder and len(key) >= 20 and not publishable_key
    key_hint = "OK"
    if key_has_placeholder or len(key) < 20:
        key_hint = "Chave parece placeholder ou inválida. Copie a chave completa do projeto."
    elif publishable_key:
        key_hint = (
            "Formato publishable detectado (sb_publishable_). Para este app/Python, "
            "use SUPABASE_ANON_KEY (JWT) ou SUPABASE_SERVICE_ROLE_KEY."
        )
    add_check(
        "Formato da chave",
        key_ok,
        key_hint,
    )

    if not url_ok or not key_ok:
        return {
            "ok": False,
            "message": "Formato de URL/chave do Supabase inválido.",
            "checks": checks,
        }

    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
    }

    try:
        auth_response = requests.get(
            f"{url.rstrip('/')}/auth/v1/settings",
            headers=headers,
            timeout=12,
        )
        auth_ok = auth_response.status_code < 400
        auth_detail = (
            "OK"
            if auth_ok
            else f"HTTP {auth_response.status_code}: {auth_response.text[:160]}"
        )
        add_check("Auth API acessível", auth_ok, auth_detail)
    except Exception as exc:
        add_check("Auth API acessível", False, f"Falha de conexão: {exc}")

    try:
        rest_response = requests.get(
            f"{url.rstrip('/')}/rest/v1/",
            headers=headers,
            timeout=12,
        )
        rest_text = (rest_response.text or "")[:240]
        service_role_only = (
            rest_response.status_code == 401
            and "service_role" in rest_text.lower()
            and "only" in rest_text.lower()
        )

        rest_ok = rest_response.status_code < 400 or service_role_only

        if rest_response.status_code < 400:
            rest_detail = "OK"
        elif service_role_only:
            rest_detail = (
                "Chave reconhecida. O endpoint raiz /rest/v1 exige service_role em alguns projetos; "
                "isso não indica chave inválida."
            )
        else:
            rest_detail = f"HTTP {rest_response.status_code}: {rest_text[:160]}"

        add_check("REST API acessível", rest_ok, rest_detail)
    except Exception as exc:
        add_check("REST API acessível", False, f"Falha de conexão: {exc}")

    try:
        users_probe = requests.get(
            f"{url.rstrip('/')}/rest/v1/usuarios",
            headers={
                **headers,
                "Accept": "application/json",
            },
            params={"select": "*", "limit": "1"},
            timeout=12,
        )

        probe_ok = users_probe.status_code < 400
        if probe_ok:
            probe_detail = "OK"
        elif users_probe.status_code == 404:
            probe_detail = "Tabela usuarios não encontrada. Execute o schema SQL no Supabase."
        elif users_probe.status_code in {401, 403}:
            probe_detail = (
                "Sem permissão de leitura em usuarios com a chave atual. "
                "Revise a chave e as políticas RLS/permissões da tabela."
            )
        else:
            probe_detail = f"HTTP {users_probe.status_code}: {(users_probe.text or '')[:160]}"

        add_check("Leitura de dados (usuarios)", probe_ok, probe_detail)
    except Exception as exc:
        add_check("Leitura de dados (usuarios)", False, f"Falha de conexão: {exc}")

    try:
        atividades_probe = requests.get(
            f"{url.rstrip('/')}/rest/v1/atividades",
            headers={
                **headers,
                "Accept": "application/json",
            },
            params={
                "select": (
                    "id_atividade,id_usuario,titulo,categoria,descricao,frequencia,horario,"
                    "data_inicio,data_fim,dias_semana,data_criacao,data_cancelamento,"
                    "data_exclusao,status,planta_id,origem,tipo_cuidado"
                ),
                "limit": "1",
            },
            timeout=12,
        )

        atividades_ok = atividades_probe.status_code < 400
        if atividades_ok:
            atividades_detail = "OK"
        elif atividades_probe.status_code == 400 and "does not exist" in (atividades_probe.text or ""):
            atividades_detail = (
                "Schema de atividades incompleto. Rode no Supabase SQL Editor: "
                "alter table atividades add column if not exists id_atividade text; "
                "alter table atividades add column if not exists id_usuario text; "
                "alter table atividades add column if not exists titulo text; "
                "alter table atividades add column if not exists categoria text; "
                "alter table atividades add column if not exists descricao text; "
                "alter table atividades add column if not exists frequencia text; "
                "alter table atividades add column if not exists horario text; "
                "alter table atividades add column if not exists data_inicio text; "
                "alter table atividades add column if not exists data_fim text; "
                "alter table atividades add column if not exists dias_semana text; "
                "alter table atividades add column if not exists data_criacao text; "
                "alter table atividades add column if not exists data_cancelamento text; "
                "alter table atividades add column if not exists data_exclusao text; "
                "alter table atividades add column if not exists status text; "
                "alter table atividades add column if not exists planta_id text; "
                "alter table atividades add column if not exists origem text; "
                "alter table atividades add column if not exists tipo_cuidado text;"
            )
        elif atividades_probe.status_code == 404:
            atividades_detail = "Tabela atividades não encontrada. Execute o schema SQL no Supabase."
        elif atividades_probe.status_code in {401, 403}:
            atividades_detail = "Sem permissão para validar schema de atividades com a chave atual."
        else:
            atividades_detail = f"HTTP {atividades_probe.status_code}: {(atividades_probe.text or '')[:160]}"

        add_check("Schema atividades (agendamento)", atividades_ok, atividades_detail)
    except Exception as exc:
        add_check("Schema atividades (cancelamento)", False, f"Falha de conexão: {exc}")

    try:
        plantas_probe = requests.get(
            f"{url.rstrip('/')}/rest/v1/plantas",
            headers={
                **headers,
                "Accept": "application/json",
            },
            params={
                "select": (
                    "id_planta,id_usuario,nome_popular,nome_cientifico,ambiente,"
                    "observacoes,resumo_cuidados,data_criacao,status"
                ),
                "limit": "1",
            },
            timeout=12,
        )

        plantas_ok = plantas_probe.status_code < 400
        if plantas_ok:
            plantas_detail = "OK"
        elif plantas_probe.status_code == 400 and "does not exist" in (plantas_probe.text or ""):
            plantas_detail = (
                "Schema de plantas incompleto. Rode no Supabase SQL Editor: "
                "create table if not exists plantas ("
                "id_planta text primary key, "
                "id_usuario text, "
                "nome_popular text not null, "
                "nome_cientifico text, "
                "ambiente text, "
                "observacoes text, "
                "resumo_cuidados text, "
                "data_criacao text, "
                "status text default 'Ativa');"
            )
        elif plantas_probe.status_code == 404:
            plantas_detail = "Tabela plantas não encontrada. Execute o schema SQL no Supabase."
        elif plantas_probe.status_code in {401, 403}:
            plantas_detail = "Sem permissão para validar schema de plantas com a chave atual."
        else:
            plantas_detail = f"HTTP {plantas_probe.status_code}: {(plantas_probe.text or '')[:160]}"

        add_check("Schema plantas", plantas_ok, plantas_detail)
    except Exception as exc:
        add_check("Schema plantas", False, f"Falha de conexão: {exc}")

    ok = all(bool(item.get("ok")) for item in checks)
    message = (
        "Certificação Supabase aprovada."
        if ok
        else "Certificação Supabase reprovada. Ajuste URL/chave e teste novamente."
    )

    return {
        "ok": ok,
        "message": message,
        "checks": checks,
    }


def sign_in_with_email_password(email: str, password: str) -> dict[str, Any]:
    email_clean = _normalize_email(email)

    try:
        client = _auth_client()
        response = client.auth.sign_in_with_password(
            {
                "email": email_clean,
                "password": password,
            }
        )
        user = getattr(response, "user", None)
        session = getattr(response, "session", None)

        if user is None:
            return {
                "ok": False,
                "message": "Não foi possível autenticar no Supabase Auth.",
            }

        return {
            "ok": True,
            "message": "",
            "email": str(getattr(user, "email", email_clean) or email_clean).strip().lower(),
            "auth_user_id": str(getattr(user, "id", "") or ""),
            "access_token": str(getattr(session, "access_token", "") or ""),
            "refresh_token": str(getattr(session, "refresh_token", "") or ""),
        }
    except Exception as exc:
        return {
            "ok": False,
            "message": _friendly_auth_error(exc),
        }


def sign_up_with_email_password(first_name: str, email: str, password: str) -> dict[str, Any]:
    email_clean = _normalize_email(email)
    first_name_clean = " ".join(first_name.strip().split())

    try:
        client = _auth_client()
        response = client.auth.sign_up(
            {
                "email": email_clean,
                "password": password,
                "options": {
                    "data": {
                        "nome": first_name_clean,
                    }
                },
            }
        )
        user = getattr(response, "user", None)
        session = getattr(response, "session", None)

        if user is None:
            return {
                "status": "error",
                "message": "Não foi possível criar sua conta no Supabase Auth.",
            }

        if session is None:
            return {
                "status": "pending_confirmation",
                "message": "Cadastro criado. Verifique seu e-mail para confirmar a conta antes de entrar.",
                "email": str(getattr(user, "email", email_clean) or email_clean).strip().lower(),
                "auth_user_id": str(getattr(user, "id", "") or ""),
            }

        return {
            "status": "authenticated",
            "message": "Cadastro criado com sucesso.",
            "email": str(getattr(user, "email", email_clean) or email_clean).strip().lower(),
            "auth_user_id": str(getattr(user, "id", "") or ""),
            "access_token": str(getattr(session, "access_token", "") or ""),
            "refresh_token": str(getattr(session, "refresh_token", "") or ""),
        }
    except Exception as exc:
        return {
            "status": "error",
            "message": _friendly_auth_error(exc),
        }