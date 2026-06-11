"""Tests unitarios de TaskManager.

Se inyecta un Mock directamente en el constructor en lugar de parchear
variables de módulo, respetando el principio D de SOLID y haciendo los
tests independientes de la estructura interna de la clase.
"""
from unittest.mock import Mock

import pytest

from application.task_manager import TaskManager
from domain.task import Task

VALID_DATA = {
    "title": "Revisar PR",
    "description": "Code review del modulo auth",
    "priority": "alta",
    "effort_hours": 2.0,
    "status": "pendiente",
    "assigned_to": "Carlos",
    "category": "",
    "risk_analysis": "",
    "risk_mitigation": "",
}


def make_mock_repo(existing: list[dict] | None = None) -> Mock:
    repo = Mock()
    repo.load.return_value = existing or []
    return repo


def make_task(**overrides) -> Task:
    return Task.from_dict({**VALID_DATA, **overrides})


class TestTaskManagerCreate:
    def test_create_returns_task_instance(self):
        manager = TaskManager(make_mock_repo())
        result = manager.create(VALID_DATA)
        assert isinstance(result, Task)

    def test_create_persists_ai_fields(self):
        repo = make_mock_repo()
        manager = TaskManager(repo)
        manager.create({**VALID_DATA, "category": "Backend"})
        saved = repo.save.call_args[0][0][0]
        assert saved["category"] == "Backend"

    def test_create_empty_description_raises(self):
        manager = TaskManager(make_mock_repo())
        with pytest.raises(ValueError, match="description"):
            manager.create({**VALID_DATA, "description": "   "})

    def test_create_empty_assigned_to_raises(self):
        manager = TaskManager(make_mock_repo())
        with pytest.raises(ValueError, match="assigned_to"):
            manager.create({**VALID_DATA, "assigned_to": ""})

    def test_create_non_numeric_effort_raises(self):
        manager = TaskManager(make_mock_repo())
        with pytest.raises(ValueError, match="effort_hours"):
            manager.create({**VALID_DATA, "effort_hours": "abc"})

    def test_create_negative_effort_raises(self):
        manager = TaskManager(make_mock_repo())
        with pytest.raises(ValueError, match="effort_hours"):
            manager.create({**VALID_DATA, "effort_hours": -1})


class TestTaskManagerRead:
    def test_get_all_returns_task_instances(self):
        task = make_task(id="id-1")
        manager = TaskManager(make_mock_repo([task.to_dict()]))
        result = manager.get_all()
        assert len(result) == 1
        assert isinstance(result[0], Task)

    def test_get_by_id_returns_correct_task(self):
        task = make_task(id="find-me")
        manager = TaskManager(make_mock_repo([task.to_dict()]))
        found = manager.get_by_id("find-me")
        assert found is not None
        assert found.id == "find-me"

    def test_get_by_id_returns_none_for_missing(self):
        manager = TaskManager(make_mock_repo())
        assert manager.get_by_id("no-existe") is None


class TestTaskManagerUpdate:
    def test_update_can_store_risk_fields(self):
        task = make_task(id="upd-id")
        repo = make_mock_repo([task.to_dict()])
        manager = TaskManager(repo)
        result = manager.update("upd-id", {
            "risk_analysis": "Dependencias externas.",
            "risk_mitigation": "Revisar integracion antes.",
        })
        assert result is not None
        assert result.risk_analysis == "Dependencias externas."
        assert result.risk_mitigation == "Revisar integracion antes."

    def test_update_invalid_status_raises(self):
        task = make_task(id="upd-id")
        manager = TaskManager(make_mock_repo([task.to_dict()]))
        with pytest.raises(ValueError):
            manager.update("upd-id", {"status": "invalido"})

    def test_update_nonexistent_returns_none(self):
        manager = TaskManager(make_mock_repo())
        assert manager.update("no-existe", {"title": "X"}) is None


class TestTaskManagerDelete:
    def test_delete_existing_returns_true(self):
        task = make_task(id="del-id")
        manager = TaskManager(make_mock_repo([task.to_dict()]))
        assert manager.delete("del-id") is True

    def test_delete_nonexistent_returns_false(self):
        manager = TaskManager(make_mock_repo())
        assert manager.delete("no-existe") is False
