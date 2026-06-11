"""Tests de integración de los endpoints HTTP.

El fixture 'client' (definido en conftest.py) sobreescribe las dependencias
de FastAPI con implementaciones de test. No se parchea ningún módulo ni
atributo de instancia: el desacoplamiento viene de app.dependency_overrides.
"""
import pytest
from fastapi.testclient import TestClient

from application.ai_task_service import AITaskService
from interface.dependencies import get_ai_service, get_task_manager
from main import app

VALID_TASK = {
    "title": "Implementar login",
    "description": "Crear endpoint de autenticacion JWT",
    "priority": "alta",
    "effort_hours": 3.0,
    "status": "pendiente",
    "assigned_to": "Ana",
    "category": "",
    "risk_analysis": "",
    "risk_mitigation": "",
}


# ---------------------------------------------------------------------------
# Endpoint de bienvenida
# ---------------------------------------------------------------------------

def test_greeting_returns_200(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "endpoints" in data


# ---------------------------------------------------------------------------
# CRUD de tareas
# ---------------------------------------------------------------------------

def test_get_tasks_empty(client):
    assert client.get("/tasks").json() == []


def test_create_task_returns_201(client):
    response = client.post("/tasks", json=VALID_TASK)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == VALID_TASK["title"]
    assert "id" in data


def test_get_all_tasks(client):
    client.post("/tasks", json=VALID_TASK)
    client.post("/tasks", json={**VALID_TASK, "title": "Segunda tarea"})
    assert len(client.get("/tasks").json()) == 2


def test_get_task_by_id(client):
    task_id = client.post("/tasks", json=VALID_TASK).json()["id"]
    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["id"] == task_id


def test_get_task_not_found(client):
    assert client.get("/tasks/id-inexistente").status_code == 404


def test_update_task(client):
    task_id = client.post("/tasks", json=VALID_TASK).json()["id"]
    response = client.put(f"/tasks/{task_id}", json={"status": "completada"})
    assert response.status_code == 200
    assert response.json()["status"] == "completada"


def test_update_task_not_found(client):
    assert client.put("/tasks/no-existe", json=VALID_TASK).status_code == 404


def test_delete_task(client):
    task_id = client.post("/tasks", json=VALID_TASK).json()["id"]
    assert client.delete(f"/tasks/{task_id}").status_code == 204
    assert client.get(f"/tasks/{task_id}").status_code == 404


def test_delete_task_not_found(client):
    assert client.delete("/tasks/no-existe").status_code == 404


def test_create_task_invalid_priority(client):
    bad = {**VALID_TASK, "priority": "critica"}
    assert client.post("/tasks", json=bad).status_code == 422


def test_create_task_missing_title(client):
    bad = {**VALID_TASK, "title": ""}
    assert client.post("/tasks", json=bad).status_code == 422


# ---------------------------------------------------------------------------
# Endpoints de IA — el fixture usa DummyProvider de conftest.py
# ---------------------------------------------------------------------------

def test_ai_describe_returns_description(client):
    payload = {**VALID_TASK, "description": ""}
    response = client.post("/ai/tasks/describe", json=payload)
    assert response.status_code == 200
    assert response.json()["description"] == "Descripcion generada"


def test_ai_categorize_returns_category(client):
    response = client.post("/ai/tasks/categorize", json=VALID_TASK)
    assert response.status_code == 200
    assert response.json()["category"] == "Backend"


def test_ai_estimate_returns_effort_hours(client):
    payload = {**VALID_TASK, "effort_hours": ""}
    response = client.post("/ai/tasks/estimate", json=payload)
    assert response.status_code == 200
    assert response.json()["effort_hours"] == 6.5


def test_ai_audit_returns_risk_fields(client):
    response = client.post("/ai/tasks/audit", json=VALID_TASK)
    assert response.status_code == 200
    data = response.json()
    assert data["risk_analysis"] == "Riesgo de dependencias."
    assert data["risk_mitigation"] == "Mitigar: Riesgo de dependencias."


def test_ai_describe_returns_422_on_validation_error():
    class FailService:
        def describe_task(self, data: dict) -> dict:
            raise ValueError("Error de validacion")

    app.dependency_overrides[get_ai_service] = lambda: FailService()
    with TestClient(app) as c:
        response = c.post("/ai/tasks/describe", json=VALID_TASK)
    app.dependency_overrides.pop(get_ai_service, None)
    assert response.status_code == 422


def test_ai_describe_returns_503_on_runtime_error():
    class UnavailableService:
        def describe_task(self, data: dict) -> dict:
            raise RuntimeError("Proveedor no disponible")

    app.dependency_overrides[get_ai_service] = lambda: UnavailableService()
    with TestClient(app) as c:
        response = c.post("/ai/tasks/describe", json=VALID_TASK)
    app.dependency_overrides.pop(get_ai_service, None)
    assert response.status_code == 503
