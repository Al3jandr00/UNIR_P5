from __future__ import annotations

from sqlalchemy.orm import Session

from infrastructure.task_model import TaskModel


class SqlRepository:
    """Implementación de TaskRepositoryProtocol sobre SQLAlchemy.

    Recibe la sesión de BD por constructor (principio D), lo que permite
    inyectar sesiones de test (SQLite en memoria) sin modificar esta clase.

    La estrategia de save() es borrar todas las filas e insertar las nuevas
    en una sola transacción, manteniendo el contrato simple del protocolo
    (load/save sobre listas de dicts) sin modificar TaskManager.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def load(self) -> list[dict]:
        rows = self._session.query(TaskModel).all()
        return [self._to_dict(row) for row in rows]

    def save(self, data: list[dict]) -> None:
        self._session.query(TaskModel).delete()
        for item in data:
            self._session.add(TaskModel(**self._normalize(item)))
        self._session.commit()

    @staticmethod
    def _normalize(item: dict) -> dict:
        return {
            "id": item["id"],
            "title": item["title"],
            "description": item.get("description", ""),
            "priority": item["priority"],
            "effort_hours": item.get("effort_hours"),
            "status": item["status"],
            "assigned_to": item.get("assigned_to", ""),
            "category": item.get("category", ""),
            "risk_analysis": item.get("risk_analysis", ""),
            "risk_mitigation": item.get("risk_mitigation", ""),
        }

    @staticmethod
    def _to_dict(row: TaskModel) -> dict:
        return {
            "id": row.id,
            "title": row.title,
            "description": row.description,
            "priority": row.priority,
            "effort_hours": row.effort_hours,
            "status": row.status,
            "assigned_to": row.assigned_to,
            "category": row.category,
            "risk_analysis": row.risk_analysis,
            "risk_mitigation": row.risk_mitigation,
        }
