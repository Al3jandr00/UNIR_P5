from __future__ import annotations

import re

from infrastructure.settings import settings

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None


class AIProvider:
    def __init__(self) -> None:
        self._client = self._build_client()
        self._model = self._resolve_model()

    def _build_client(self):
        if OpenAI is None:
            return None
        if settings.has_azure_config:
            return OpenAI(
                api_key=settings.azure_openai_api_key,
                base_url=(
                    f"{settings.azure_openai_endpoint.rstrip('/')}"
                    f"/openai/deployments/{settings.azure_openai_model}"
                ),
                default_query={"api-version": settings.azure_openai_api_version},
            )
        if settings.has_openai_config:
            kwargs = {"api_key": settings.openai_api_key}
            kwargs["base_url"] = settings.openai_base_url or "https://api.openai.com/v1"
            return OpenAI(**kwargs)
        return None

    def _resolve_model(self) -> str:
        if settings.has_azure_config:
            return settings.azure_openai_model
        return settings.openai_model

    def _chat(self, system_prompt: str, user_prompt: str) -> str:
        if self._client is None:
            raise RuntimeError("No hay proveedor LLM configurado.")
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "system",
                    "content": f"{settings.openai_system_prompt}\n\n{system_prompt}",
                },
                {"role": "user", "content": user_prompt},
            ],
            temperature=settings.openai_temperature,
            max_tokens=settings.openai_max_tokens,
            top_p=settings.openai_top_p,
        )
        content = response.choices[0].message.content or ""
        return content.strip()

    def generate_description(self, task_data: dict) -> str:
        return self._run_or_fallback(
            lambda: self._chat(
                "Genera una descripcion profesional y breve para una tarea. Devuelve solo la descripcion.",
                self._task_context(task_data),
            ),
            lambda: self._fallback_description(task_data),
        )

    def categorize_task(self, task_data: dict) -> str:
        return self._run_or_fallback(
            lambda: self._chat(
                (
                    "Clasifica la tarea en una sola categoria. "
                    "Devuelve solo una de estas categorias: Frontend, Backend, Testing, Infra, Data, DevOps, Seguridad, Documentacion, Analisis."
                ),
                self._task_context(task_data),
            ),
            lambda: self._fallback_category(task_data),
        )

    def estimate_effort(self, task_data: dict) -> float:
        return self._run_or_fallback(
            lambda: self._parse_hours(
                self._chat(
                    (
                        "Estima el esfuerzo de la tarea en horas. "
                        "Devuelve solo un numero decimal positivo, sin texto adicional."
                    ),
                    self._task_context(task_data),
                )
            ),
            lambda: self._fallback_effort(task_data),
        )

    def analyze_risks(self, task_data: dict) -> str:
        return self._run_or_fallback(
            lambda: self._chat(
                "Analiza los riesgos de la tarea. Devuelve un texto breve y accionable.",
                self._task_context(task_data),
            ),
            lambda: self._fallback_risk_analysis(task_data),
        )

    def generate_mitigation(self, task_data: dict, risk_analysis: str) -> str:
        return self._run_or_fallback(
            lambda: self._chat(
                "Genera un plan breve de mitigacion de riesgos para la tarea. Devuelve solo el plan.",
                f"{self._task_context(task_data)}\n\nRiesgos detectados:\n{risk_analysis}",
            ),
            lambda: self._fallback_mitigation(task_data, risk_analysis),
        )

    def _run_or_fallback(self, real_call, fallback_call):
        if self._client is None:
            if settings.allow_local_fallback:
                return fallback_call()
            raise RuntimeError("No hay proveedor LLM configurado y el fallback local esta desactivado.")
        try:
            return real_call()
        except Exception as exc:
            if settings.allow_local_fallback:
                return fallback_call()
            raise RuntimeError(f"Fallo la llamada al proveedor LLM: {exc}") from exc

    def _task_context(self, task_data: dict) -> str:
        return (
            f"Titulo: {task_data.get('title', '')}\n"
            f"Descripcion: {task_data.get('description', '')}\n"
            f"Prioridad: {task_data.get('priority', '')}\n"
            f"Estado: {task_data.get('status', '')}\n"
            f"Asignado a: {task_data.get('assigned_to', '')}\n"
            f"Categoria: {task_data.get('category', '')}\n"
        )

    def _fallback_description(self, task_data: dict) -> str:
        title = task_data.get("title", "").strip()
        assigned_to = task_data.get("assigned_to", "").strip()
        priority = task_data.get("priority", "").strip()
        status = task_data.get("status", "").strip()
        category = task_data.get("category", "").strip()
        parts = [f"Desarrollar la tarea '{title}'"]
        if assigned_to:
            parts.append(f"asignada a {assigned_to}")
        if priority:
            parts.append(f"con prioridad {priority}")
        if status:
            parts.append(f"y estado actual {status}")
        sentence = " ".join(parts) + "."
        if category:
            sentence += f" Esta tarea pertenece al area de {category}."
        return sentence

    def _fallback_category(self, task_data: dict) -> str:
        text = " ".join([
            task_data.get("title", ""),
            task_data.get("description", ""),
            task_data.get("category", ""),
        ]).lower()
        rules = [
            ("frontend", "Frontend"),
            ("ui", "Frontend"),
            ("css", "Frontend"),
            ("react", "Frontend"),
            ("backend", "Backend"),
            ("api", "Backend"),
            ("endpoint", "Backend"),
            ("base de datos", "Backend"),
            ("sql", "Backend"),
            ("test", "Testing"),
            ("testing", "Testing"),
            ("qa", "Testing"),
            ("infra", "Infra"),
            ("deploy", "Infra"),
            ("docker", "Infra"),
            ("servidor", "Infra"),
            ("document", "Documentacion"),
            ("analisis", "Analisis"),
            ("seguridad", "Seguridad"),
        ]
        for keyword, category in rules:
            if keyword in text:
                return category
        return "Backend"

    def _fallback_effort(self, task_data: dict) -> float:
        text = " ".join([
            task_data.get("title", ""),
            task_data.get("description", ""),
            task_data.get("category", ""),
        ]).lower()
        rules = [
            (("bug", "fix"), 2.0),
            (("test", "testing", "qa"), 3.0),
            (("endpoint", "api", "backend"), 6.0),
            (("frontend", "ui", "react", "css"), 5.0),
            (("infra", "docker", "deploy", "servidor"), 8.0),
            (("auth", "login", "jwt"), 7.0),
            (("base de datos", "sql", "migracion"), 6.0),
        ]
        for keywords, hours in rules:
            if any(keyword in text for keyword in keywords):
                return hours
        return 4.0

    def _fallback_risk_analysis(self, task_data: dict) -> str:
        title = task_data.get("title", "").strip()
        category = task_data.get("category", "").strip() or "general"
        priority = task_data.get("priority", "").strip()
        risks = [f"Posibles bloqueos tecnicos durante la ejecucion de '{title}'."]
        if priority in {"alta", "bloqueante"}:
            risks.append("La prioridad elevada puede aumentar el impacto de retrasos o errores.")
        risks.append(f"Pueden aparecer dependencias funcionales o tecnicas en el area de {category}.")
        return " ".join(risks)

    def _fallback_mitigation(self, task_data: dict, risk_analysis: str) -> str:
        assigned_to = task_data.get("assigned_to", "").strip() or "el equipo responsable"
        return (
            f"Definir una revision temprana con {assigned_to}, dividir la tarea en hitos pequenos "
            f"y validar pronto los puntos criticos identificados. Mitigar especialmente: {risk_analysis}"
        )

    def _parse_hours(self, raw: str) -> float:
        match = re.search(r"\d+(?:[.,]\d+)?", raw)
        if not match:
            raise ValueError("No se pudo interpretar una estimacion numerica de horas.")
        return float(match.group(0).replace(",", "."))
