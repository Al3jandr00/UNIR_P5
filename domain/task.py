from __future__ import annotations

import uuid
from enum import Enum


class Priority(str, Enum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    BLOQUEANTE = "bloqueante"


class Status(str, Enum):
    PENDIENTE = "pendiente"
    EN_PROGRESO = "en progreso"
    EN_REVISION = "en revisión"
    COMPLETADA = "completada"


class Task:
    def __init__(
        self,
        title: str,
        description: str,
        priority: Priority,
        effort_hours: float | None,
        status: Status,
        assigned_to: str,
        category: str = "",
        risk_analysis: str = "",
        risk_mitigation: str = "",
        id: str | None = None,
    ) -> None:
        self.id = id or str(uuid.uuid4())
        self.title = title
        self.description = description
        self.priority = Priority(priority)
        self.effort_hours = None if effort_hours in (None, "") else float(effort_hours)
        self.status = Status(status)
        self.assigned_to = assigned_to
        self.category = category
        self.risk_analysis = risk_analysis
        self.risk_mitigation = risk_mitigation

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "effort_hours": self.effort_hours,
            "status": self.status.value,
            "assigned_to": self.assigned_to,
            "category": self.category,
            "risk_analysis": self.risk_analysis,
            "risk_mitigation": self.risk_mitigation,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Task:
        return cls(
            id=data.get("id"),
            title=data["title"],
            description=data.get("description", ""),
            priority=data["priority"],
            effort_hours=data.get("effort_hours"),
            status=data["status"],
            assigned_to=data.get("assigned_to", ""),
            category=data.get("category", ""),
            risk_analysis=data.get("risk_analysis", ""),
            risk_mitigation=data.get("risk_mitigation", ""),
        )

    def __repr__(self) -> str:
        return f"Task(id={self.id!r}, title={self.title!r}, status={self.status.value!r})"
