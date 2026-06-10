from __future__ import annotations

from dataclasses import dataclass
import json
import re

import requests

from config.settings import (
    chatgpt_api_base_url,
    chatgpt_api_key,
    gemini_api_base_url,
    gemini_api_key,
)
from services.app_service import get_ai_settings


@dataclass
class PlantAiRequest:
    funcionalidade: str
    planta: str
    ambiente: str
    sintomas: str
    contexto: str = ""


def _build_prompt(payload: PlantAiRequest) -> str:
    return f"""
Você é um assistente especialista em cuidados simples com plantas domésticas.
Responda exclusivamente em JSON válido, sem markdown, sem ```json e sem explicações fora do JSON.

A resposta deve seguir exatamente este formato:
{{
  "nome_popular": "",
  "nome_cientifico": "",
  "ambiente_recomendado": "",
  "resumo_cuidados": "",
  "observacoes": "",
  "cuidados_semanais": [
    {{
      "dia_semana": "Segunda",
      "horario": "08:00",
      "tipo_cuidado": "rega",
      "descricao": ""
    }}
  ],
  "alertas": [""]
}}

Regras:
- Use dias da semana em português: Segunda, Terça, Quarta, Quinta, Sexta, Sábado ou Domingo.
- Crie de 1 a 4 cuidados semanais, somente se fizerem sentido para a planta.
- Horário deve estar no formato HH:MM.
- As descrições devem ser curtas e acionáveis, pois virarão tarefas do app.
- Não invente diagnóstico definitivo. Quando houver dúvida, use observações cautelosas.

Dados do usuário:
Funcionalidade: {payload.funcionalidade}
Planta: {payload.planta}
Ambiente: {payload.ambiente}
Sintomas ou objetivo: {payload.sintomas}
Contexto adicional: {payload.contexto or 'Não informado'}
""".strip()


def parse_ai_json(text: str) -> dict:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            raise ValueError("A IA não retornou um JSON válido.")
        return json.loads(match.group(0))


def _extract_openai_text(data: dict) -> str:
    output = data.get("output", [])
    texts: list[str] = []
    for item in output:
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "output_text":
                value = str(content.get("text", "")).strip()
                if value:
                    texts.append(value)
    if texts:
        return "\n\n".join(texts).strip()
    try:
        return str(data["choices"][0]["message"]["content"]).strip()
    except Exception:
        return ""


def _extract_gemini_text(data: dict) -> str:
    texts: list[str] = []
    for candidate in data.get("candidates", []):
        content = candidate.get("content", {})
        for part in content.get("parts", []):
            value = str(part.get("text", "")).strip()
            if value:
                texts.append(value)
    return "\n\n".join(texts).strip()


class PlantAiService:
    def __init__(self) -> None:
        settings = get_ai_settings()
        self.provider = settings["provider"]
        self.model = settings["model"]

    def ask_for_guidance(self, payload: PlantAiRequest) -> dict:
        prompt = _build_prompt(payload)
        if self.provider == "openai":
            text = self._ask_openai(prompt)
        elif self.provider == "gemini":
            text = self._ask_gemini(prompt)
        else:
            raise RuntimeError(f"Provedor de IA não suportado: {self.provider}")
        data = parse_ai_json(text)
        data["_prompt_usuario"] = prompt
        return data

    def _ask_openai(self, prompt: str) -> str:
        api_key = chatgpt_api_key()
        base_url = chatgpt_api_base_url()
        if not api_key:
            raise RuntimeError("API key da OpenAI/ChatGPT não configurada.")
        response = requests.post(
            f"{base_url}/responses",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": self.model, "input": prompt, "temperature": 0.2},
            timeout=45,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"Erro ao chamar OpenAI ({response.status_code}): {response.text[:300]}")
        text = _extract_openai_text(response.json())
        if not text:
            raise RuntimeError("A OpenAI não retornou texto útil.")
        return text

    def _ask_gemini(self, prompt: str) -> str:
        api_key = gemini_api_key()
        base_url = gemini_api_base_url()
        if not api_key:
            raise RuntimeError("API key do Google Gemini não configurada.")
        url = f"{base_url}/models/{self.model}:generateContent"
        response = requests.post(
            url,
            params={"key": api_key},
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.2, "maxOutputTokens": 2048},
            },
            timeout=60,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"Erro ao chamar Gemini ({response.status_code}): {response.text[:300]}")
        text = _extract_gemini_text(response.json())
        if not text:
            raise RuntimeError("O Gemini não retornou texto útil.")
        return text


def get_plant_ai_service() -> PlantAiService:
    return PlantAiService()
