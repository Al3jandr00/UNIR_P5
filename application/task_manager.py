from __future__ import annotations

from domain.task import Priority, Status, Task
from infrastructure.protocols import TaskRepositoryProtocol


class TaskManager:
    """Gestiona el ciclo de vida de las tareas (CRUD).

    Aplica el principio D (Dependency Inversion): recibe el repositorio por
    constructor en lugar de instanciarlo internamente, lo que permite sustituir
    la implementación de persistencia sin modificar esta clase.
    """

    def __init__(self, repository: TaskRepositoryProtocol) -> None:
        self._repository = repository

    def get_all(self) -> list[Task]:
        return [Task.from_dict(d) for d in self._repository.load()]

    def get_by_id(self, task_id: str) -> Task | None:
        return next((t for t in self.get_all() if t.id == task_id), None)

    def create(self, data: dict) -> Task:
        self._validate(data)
        task = Task.from_dict(data)
        tasks = self.get_all()
        tasks.append(task)
        self._repository.save([t.to_dict() for t in tasks])
        return task

    def update(self, task_id: str, data: dict) -> Task | None:
        tasks = self.get_all()
        for i, task in enumerate(tasks):
            if task.id == task_id:
                merged = {**task.to_dict(), **data, "id": task_id}
                self._validate(merged)
                tasks[i] = Task.from_dict(merged)
                self._repository.save([t.to_dict() for t in tasks])
                return tasks[i]
        return None

    def delete(self, task_id: str) -> bool:
        tasks = self.get_all()
        filtered = [t for t in tasks if t.id != task_id]
        if len(filtered) == len(tasks):
            return False
        self._repository.save([t.to_dict() for t in filtered])
        return True

    @staticmethod
    def _validate(data: dict) -> None:
        if not data.get("title", "").strip():
            raise ValueError("El campo 'title' es obligatorio y no puede estar vacio.")
        if not data.get("description", "").strip():
            raise ValueError("El campo 'description' es obligatorio y no puede estar vacio.")
        if data.get("priority") not in Priority._value2member_map_:
            raise ValueError(f"'priority' debe ser uno de: {list(Priority._value2member_map_)}.")
        if data.get("status") not in Status._value2member_map_:
            raise ValueError(f"'status' debe ser uno de: {list(Status._value2member_map_)}.")
        if not data.get("assigned_to", "").strip():
            raise ValueError("El campo 'assigned_to' es obligatorio y no puede estar vacio.")

        effort = data.get("effort_hours")
        try:
            effort_value = float(effort)
        except (TypeError, ValueError):
            raise ValueError("'effort_hours' debe ser un numero decimal positivo.")
        if effort is None or effort == "" or effort_value <= 0:
            raise ValueError("'effort_hours' debe ser un numero decimal positivo.")

        for field in ("category", "risk_analysis", "risk_mitigation"):
            value = data.get(field, "")
            if value is not None and not isinstance(value, str):
                raise ValueError(f"El campo '{field}' debe ser texto.")
