from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd


def _to_datetime(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce")


def _to_date(series: pd.Series) -> pd.Series:
    return _to_datetime(series).dt.date


def retention_after_days(usuarios: pd.DataFrame, sessoes: pd.DataFrame, days: int) -> float:
    if usuarios.empty or sessoes.empty:
        return 0.0

    if "data_cadastro" not in usuarios.columns or "data_hora_acesso" not in sessoes.columns:
        return 0.0

    users = usuarios[["id_usuario", "data_cadastro"]].copy()
    users["cadastro_date"] = _to_date(users["data_cadastro"])

    sess = sessoes[["id_usuario", "data_hora_acesso"]].copy()
    sess["access_date"] = _to_date(sess["data_hora_acesso"])

    today = datetime.now().date()
    eligible = 0
    retained = 0

    for _, row in users.iterrows():
        signup_date = row["cadastro_date"]
        if pd.isna(signup_date):
            continue

        target_date = signup_date + timedelta(days=days)

        if target_date > today:
            continue

        eligible += 1

        user_sessions = sess[sess["id_usuario"].astype(str) == str(row["id_usuario"])]
        returned = any(user_sessions["access_date"] >= target_date)

        if returned:
            retained += 1

    return round((retained / eligible) * 100, 1) if eligible else 0.0


def calculate_admin_metrics(data: dict[str, pd.DataFrame]) -> dict:
    usuarios = data["usuarios"]
    atividades = data["atividades"]
    execucoes = data["execucoes"]
    sessoes = data["sessoes"]

    total_users = len(usuarios)
    total_activities = len(atividades)
    total_exec = len(execucoes)

    users_with_activity = atividades["id_usuario"].nunique() if not atividades.empty else 0
    activation_rate = round((users_with_activity / total_users) * 100, 1) if total_users else 0

    users_with_completion = execucoes["id_usuario"].nunique() if not execucoes.empty else 0
    completion_user_rate = round((users_with_completion / total_users) * 100, 1) if total_users else 0

    completion_rate = round((total_exec / total_activities) * 100, 1) if total_activities else 0

    today = datetime.now().date()
    dau = 0
    wau = 0
    mau = 0

    if not sessoes.empty and "data_hora_acesso" in sessoes.columns:
        dates = _to_date(sessoes["data_hora_acesso"])
        dau = sessoes.loc[dates == today, "id_usuario"].nunique()
        wau = sessoes.loc[dates >= today - timedelta(days=7), "id_usuario"].nunique()
        mau = sessoes.loc[dates >= today - timedelta(days=30), "id_usuario"].nunique()

    recurring = 0
    if not sessoes.empty:
        recurring = int((sessoes.groupby("id_usuario").size() >= 2).sum())

    return {
        "usuarios": total_users,
        "atividades": total_activities,
        "execucoes": total_exec,
        "ativacao": activation_rate,
        "conclusao": completion_rate,
        "usuarios_com_conclusao": completion_user_rate,
        "dau": dau,
        "wau": wau,
        "mau": mau,
        "recorrentes": recurring,
        "retencao_d1": retention_after_days(usuarios, sessoes, 1),
        "retencao_d7": retention_after_days(usuarios, sessoes, 7),
        "retencao_d30": retention_after_days(usuarios, sessoes, 30),
    }


def category_counts(atividades: pd.DataFrame) -> pd.DataFrame:
    if atividades.empty or "categoria" not in atividades.columns:
        return pd.DataFrame(columns=["categoria", "quantidade"])

    return (
        atividades.groupby("categoria")
        .size()
        .reset_index(name="quantidade")
        .sort_values("quantidade", ascending=False)
    )


def sessions_by_day(sessoes: pd.DataFrame) -> pd.DataFrame:
    if sessoes.empty or "data_hora_acesso" not in sessoes.columns:
        return pd.DataFrame(columns=["data", "usuarios_ativos"])

    df = sessoes.copy()
    df["data"] = _to_datetime(df["data_hora_acesso"]).dt.date.astype(str)

    return (
        df.groupby("data")["id_usuario"]
        .nunique()
        .reset_index(name="usuarios_ativos")
        .sort_values("data")
    )


def completions_by_day(execucoes: pd.DataFrame) -> pd.DataFrame:
    if execucoes.empty or "data_hora_execucao" not in execucoes.columns:
        return pd.DataFrame(columns=["data", "conclusoes"])

    df = execucoes.copy()
    df["data"] = _to_datetime(df["data_hora_execucao"]).dt.date.astype(str)

    return (
        df.groupby("data")
        .size()
        .reset_index(name="conclusoes")
        .sort_values("data")
    )
