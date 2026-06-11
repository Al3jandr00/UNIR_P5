import pytest

from domain.task import Priority, Status, Task


class TestTaskCreation:
    def test_auto_id_is_uuid(self):
        task = Task("Titulo", "Descripcion", "alta", 2.0, "pendiente", "Ana")
        assert len(task.id) == 36
        assert task.id.count("-") == 4

    def test_effort_hours_can_be_none(self):
        task = Task("Titulo", "Descripcion", "alta", None, "pendiente", "Ana")
        assert task.effort_hours is None

    def test_new_ai_fields_default_to_empty_strings(self):
        task = Task("Titulo", "Descripcion", "alta", 2.0, "pendiente", "Ana")
        assert task.category == ""
        assert task.risk_analysis == ""
        assert task.risk_mitigation == ""

    def test_priority_stored_as_enum(self):
        task = Task("T", "D", "bloqueante", 1.0, "pendiente", "X")
        assert task.priority == Priority.BLOQUEANTE

    def test_status_stored_as_enum(self):
        task = Task("T", "D", "alta", 1.0, "en revisión", "X")
        assert task.status == Status.EN_REVISION


class TestTaskValidation:
    def test_invalid_priority_raises_value_error(self):
        with pytest.raises(ValueError):
            Task("T", "D", "urgente", 1.0, "pendiente", "X")

    def test_invalid_status_raises_value_error(self):
        with pytest.raises(ValueError):
            Task("T", "D", "alta", 1.0, "cancelada", "X")


class TestTaskSerialization:
    def setup_method(self):
        self.task = Task(
            title="Implementar login",
            description="Flujo JWT completo",
            priority="alta",
            effort_hours=3.5,
            status="en progreso",
            assigned_to="Ana Garcia",
            category="Backend",
            risk_analysis="Dependencias de autenticacion.",
            risk_mitigation="Validar integracion temprana.",
            id="abc-123",
        )

    def test_to_dict_contains_all_keys(self):
        keys = {
            "id", "title", "description", "priority", "effort_hours",
            "status", "assigned_to", "category", "risk_analysis", "risk_mitigation",
        }
        assert set(self.task.to_dict().keys()) == keys

    def test_to_dict_values_are_correct(self):
        data = self.task.to_dict()
        assert data["id"] == "abc-123"
        assert data["category"] == "Backend"
        assert data["risk_analysis"] == "Dependencias de autenticacion."
        assert data["risk_mitigation"] == "Validar integracion temprana."

    def test_from_dict_roundtrip_preserves_all_fields(self):
        restored = Task.from_dict(self.task.to_dict())
        assert restored.id == self.task.id
        assert restored.title == self.task.title
        assert restored.priority == self.task.priority
        assert restored.effort_hours == self.task.effort_hours
        assert restored.status == self.task.status
        assert restored.assigned_to == self.task.assigned_to
        assert restored.category == self.task.category
        assert restored.risk_analysis == self.task.risk_analysis
        assert restored.risk_mitigation == self.task.risk_mitigation
