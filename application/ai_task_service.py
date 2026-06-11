from __future__ import annotations

from domain.task import Task
from infrastructure.protocols import AIProviderProtocol


class AITaskService:
    """Orquesta los flujos de enriquecimiento de tareas con IA.

    Aplica el principio D (Dependency Inversion): depende de AIProviderProtocol
    (abstracción), no de AIProvider (implementación concreta). Esto permite usar
    proveedores alternativos o mocks sin modificar esta clase.
    """

    ALLOWED_CATEGORIES = {
        "Frontend",
        "Backend",
        "Testing",
        "Infra",
        "Data",
        "DevOps",
        "Seguridad",
        "Documentacion",
        "Analisis",
    }

    def __init__(self, provider: AIProviderProtocol) -> None:
        self._provider = provider

    def describe_task(self, data: dict) -> dict:
        if not data.get("title", "").strip():
            raise ValueError("El campo 'title' es obligatorio para generar la descripcion.")
        if not data.get("assigned_to", "").strip():
            raise ValueError("El campo 'assigned_to' es obligatorio para generar la descripcion.")
        if data.get("priority") is None or data.get("status") is None:
            raise ValueError("Los campos 'priority' y 'status' son obligatorios para generar la descripcion.")

        enriched = self._normalize_payload(data)
        if not enriched.get("description", "").strip():
            enriched["description"] = self._provider.generate_description(enriched)
        self._require_generated_text(enriched["description"], "description")

        return Task.from_dict(enriched).to_dict()

    def categorize_task(self, data: dict) -> dict:
        if not data.get("title", "").strip():
            raise ValueError("El campo 'title' es obligatorio para categorizar la tarea.")
        if data.get("priority") is None or data.get("status") is None:
            raise ValueError("Los campos 'priority' y 'status' son obligatorios para categorizar la tarea.")
        if not data.get("assigned_to", "").strip():
            raise ValueError("El campo 'assigned_to' es obligatorio para categorizar la tarea.")

        enriched = self._normalize_payload(data)
        if not enriched.get("category", "").strip():
            enriched["category"] = self._provider.categorize_task(enriched)
        enriched["category"] = self._normalize_category(enriched["category"])

        return Task.from_dict(enriched).to_dict()

    def estimate_task(self, data: dict) -> dict:
        if not data.get("title", "").strip():
            raise ValueError("El campo 'title' es obligatorio para estimar la tarea.")
        if not data.get("description", "").strip():
            raise ValueError("El campo 'description' es obligatorio para estimar la tarea.")
        if not data.get("assigned_to", "").strip():
            raise ValueError("El campo 'assigned_to' es obligatorio para estimar la tarea.")
        if data.get("priority") is None or data.get("status") is None:
            raise ValueError("Los campos 'priority' y 'status' son obligatorios para estimar la tarea.")

        enriched = self._normalize_payload(data)
        effort = enriched.get("effort_hours")
        if effort in (None, ""):
            enriched["effort_hours"] = self._provider.estimate_effort(enriched)

        try:
            enriched["effort_hours"] = float(enriched["effort_hours"])
        except (TypeError, ValueError):
            raise ValueError("El valor de 'effort_hours' debe poder convertirse a numero.")

        if enriched["effort_hours"] <= 0:
            raise ValueError("El valor de 'effort_hours' debe ser positivo.")

        return Task.from_dict(enriched).to_dict()

    def audit_task(self, data: dict) -> dict:
        if not data.get("title", "").strip():
            raise ValueError("El campo 'title' es obligatorio para auditar la tarea.")
        if not data.get("description", "").strip():
            raise ValueError("El campo 'description' es obligatorio para auditar la tarea.")
        if not data.get("assigned_to", "").strip():
            raise ValueError("El campo 'assigned_to' es obligatorio para auditar la tarea.")
        if data.get("priority") is None or data.get("status") is None:
            raise ValueError("Los campos 'priority' y 'status' son obligatorios para auditar la tarea.")

        enriched = self._normalize_payload(data)
        risk_analysis = self._provider.analyze_risks(enriched)
        self._require_generated_text(risk_analysis, "risk_analysis")
        enriched["risk_analysis"] = risk_analysis
        risk_mitigation = self._provider.generate_mitigation(enriched, risk_analysis)
        self._require_generated_text(risk_mitigation, "risk_mitigation")
        enriched["risk_mitigation"] = risk_mitigation

        return Task.from_dict(enriched).to_dict()

    def _normalize_payload(self, data: dict) -> dict:
        return {
            "id": data.get("id"),
            "title": data.get("title", ""),
            "description": data.get("description", ""),
            "priority": data.get("priority"),
            "effort_hours": data.get("effort_hours"),
            "status": data.get("status"),
            "assigned_to": data.get("assigned_to", ""),
            "category": data.get("category", ""),
            "risk_analysis": data.get("risk_analysis", ""),
            "risk_mitigation": data.get("risk_mitigation", ""),
        }

    def _require_generated_text(self, value: str, field_name: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"El modelo no devolvio un valor valido para '{field_name}'.")

    def _normalize_category(self, value: str) -> str:
        self._require_generated_text(value, "category")
        candidate = value.strip()
        for allowed in self.ALLOWED_CATEGORIES:
            if candidate.lower() == allowed.lower():
                return allowed
        raise ValueError(
            "El modelo devolvio una categoria invalida. "
            f"Debe ser una de: {sorted(self.ALLOWED_CATEGORIES)}."
        )
