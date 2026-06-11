"""Tests unitarios de AITaskService.

Se inyecta DummyProvider directamente — no se parchea ningún módulo.
Demuestra el principio L (Liskov Substitution): DummyProvider sustituye
a AIProvider sin que AITaskService necesite cambiar.
"""
import pytest

from application.ai_task_service import AITaskService


class DummyProvider:
    def generate_description(self, task_data: dict) -> str:
        return "Descripcion generada"

    def categorize_task(self, task_data: dict) -> str:
        return "Backend"

    def estimate_effort(self, task_data: dict) -> float:
        return 6.5

    def analyze_risks(self, task_data: dict) -> str:
        return "Riesgo de dependencias."

    def generate_mitigation(self, task_data: dict, risk_analysis: str) -> str:
        return f"Mitigar: {risk_analysis}"


BASE_TASK = {
    "title": "Implementar login",
    "description": "Crear endpoint de autenticacion",
    "priority": "alta",
    "effort_hours": 3.0,
    "status": "pendiente",
    "assigned_to": "Ana",
    "category": "",
    "risk_analysis": "",
    "risk_mitigation": "",
}


def test_describe_task_fills_empty_description():
    service = AITaskService(DummyProvider())
    task = service.describe_task({**BASE_TASK, "description": ""})
    assert task["description"] == "Descripcion generada"


def test_categorize_task_fills_empty_category():
    service = AITaskService(DummyProvider())
    task = service.categorize_task(BASE_TASK)
    assert task["category"] == "Backend"


def test_estimate_task_fills_empty_effort_hours():
    service = AITaskService(DummyProvider())
    task = service.estimate_task({**BASE_TASK, "effort_hours": ""})
    assert task["effort_hours"] == 6.5


def test_audit_task_generates_risks_and_mitigation():
    service = AITaskService(DummyProvider())
    task = service.audit_task(BASE_TASK)
    assert task["risk_analysis"] == "Riesgo de dependencias."
    assert task["risk_mitigation"] == "Mitigar: Riesgo de dependencias."


def test_describe_task_rejects_empty_model_output():
    class EmptyProvider(DummyProvider):
        def generate_description(self, task_data: dict) -> str:
            return "   "

    with pytest.raises(ValueError, match="description"):
        AITaskService(EmptyProvider()).describe_task({**BASE_TASK, "description": ""})


def test_categorize_task_rejects_invalid_category():
    class InvalidProvider(DummyProvider):
        def categorize_task(self, task_data: dict) -> str:
            return "Categoria inventada"

    with pytest.raises(ValueError, match="categoria invalida"):
        AITaskService(InvalidProvider()).categorize_task(BASE_TASK)


def test_describe_requires_title():
    with pytest.raises(ValueError, match="title"):
        AITaskService(DummyProvider()).describe_task({**BASE_TASK, "title": ""})


def test_estimate_requires_description():
    with pytest.raises(ValueError, match="description"):
        AITaskService(DummyProvider()).estimate_task({**BASE_TASK, "description": ""})
