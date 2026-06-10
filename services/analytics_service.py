from __future__ import annotations

import hashlib
import time
from datetime import date, datetime
from typing import Any

import requests
import streamlit as st

from config.settings import ga4_api_secret, ga4_measurement_id, has_ga4_config


SESSION_ID_KEY = "analytics_session_id"


class AnalyticsService:
    def __init__(self) -> None:
        self.enabled = has_ga4_config()

    @staticmethod
    def client_id_from_email(email: str) -> str:
        if not email:
            return "anonymous"
        digest = hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()
        return f"{digest[:10]}.{digest[10:20]}"

    @staticmethod
    def _coerce_value(value: Any) -> Any:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float, str)):
            return value
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if value is None:
            return None
        return str(value)

    def session_id(self) -> int:
        current = st.session_state.get(SESSION_ID_KEY)
        if current:
            return int(current)

        created = int(time.time() * 1000)
        st.session_state[SESSION_ID_KEY] = created
        return created

    def _base_params(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id(),
            "engagement_time_msec": 1,
            "app_name": "CuidaFacil",
        }

    @staticmethod
    def _parse_date(value: Any) -> date | None:
        if not value:
            return None
        if isinstance(value, date):
            return value
        if isinstance(value, datetime):
            return value.date()
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
        except Exception:
            try:
                return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
            except Exception:
                return None

    def retention_params(self, user: dict | None = None) -> dict[str, Any]:
        user = user or {}
        today = date.today()
        created_at = self._parse_date(user.get("data_cadastro"))
        last_access = self._parse_date(user.get("ultimo_acesso"))

        days_since_signup = (today - created_at).days if created_at else 0
        days_since_last_active = (today - last_access).days if last_access else 0
        is_returning_user = bool(last_access and days_since_last_active >= 1)

        if not last_access:
            retention_bucket = "new_user"
        elif days_since_last_active <= 1:
            retention_bucket = "d1"
        elif days_since_last_active <= 7:
            retention_bucket = "d7"
        elif days_since_last_active <= 30:
            retention_bucket = "d30"
        else:
            retention_bucket = "d30_plus"

        return {
            "days_since_signup": max(days_since_signup, 0),
            "days_since_last_active": max(days_since_last_active, 0),
            "is_returning_user": is_returning_user,
            "retention_bucket": retention_bucket,
        }

    def track(
        self,
        event_name: str,
        email: str = "",
        params: dict[str, Any] | None = None,
        user_properties: dict[str, Any] | None = None,
    ) -> None:
        if not self.enabled:
            return

        event_params = {**self._base_params(), **(params or {})}
        normalized_params = {
            key: value
            for key, raw_value in event_params.items()
            if (value := self._coerce_value(raw_value)) is not None
        }

        payload: dict[str, Any] = {
            "client_id": self.client_id_from_email(email),
            "events": [{"name": event_name, "params": normalized_params}],
        }

        if user_properties:
            payload["user_properties"] = {
                key: {"value": value}
                for key, raw_value in user_properties.items()
                if (value := self._coerce_value(raw_value)) is not None
            }

        url = (
            "https://www.google-analytics.com/mp/collect"
            f"?measurement_id={ga4_measurement_id()}&api_secret={ga4_api_secret()}"
        )

        try:
            requests.post(url, json=payload, timeout=3)
        except Exception:
            pass

    def track_page_view(self, page_name: str, email: str = "", params: dict[str, Any] | None = None) -> None:
        page_params = {
            "page_title": page_name,
            "page_location": f"app://cuidafacil/{page_name.lower().replace(' ', '-')}",
            "page_name": page_name,
            **(params or {}),
        }
        self.track("page_view", email, page_params)

    def track_section_access(
        self,
        section_name: str,
        email: str = "",
        params: dict[str, Any] | None = None,
    ) -> None:
        normalized_section = section_name.strip().lower().replace(" ", "_")
        event_params = {
            "section_name": section_name,
            "section_slug": normalized_section,
            **(params or {}),
        }
        self.track("section_access", email, event_params)
        self.track_page_view(section_name, email, event_params)

    def track_hoje_access(self, email: str = "", params: dict[str, Any] | None = None) -> None:
        self.track_section_access("Hoje", email, params)

    def track_calendario_access(self, email: str = "", params: dict[str, Any] | None = None) -> None:
        self.track_section_access("Calendario", email, params)

    def track_evolucao_access(self, email: str = "", params: dict[str, Any] | None = None) -> None:
        self.track_section_access("Evolucao", email, params)

    def track_planta_ia_access(self, email: str = "", params: dict[str, Any] | None = None) -> None:
        self.track_section_access("Planta com IA", email, params)

    def track_retention(self, user: dict, trigger: str = "session") -> None:
        retention = self.retention_params(user)
        params = {**retention, "trigger": trigger}
        user_properties = {
            "days_since_signup": retention["days_since_signup"],
            "retention_bucket": retention["retention_bucket"],
            "is_returning_user": retention["is_returning_user"],
        }
        self.track("retention_checkpoint", user.get("email", ""), params, user_properties=user_properties)


def get_analytics_service() -> AnalyticsService:
    return AnalyticsService()
