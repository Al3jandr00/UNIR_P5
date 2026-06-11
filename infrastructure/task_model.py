from __future__ import annotations

from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.database import Base


class TaskModel(Base):
    """Modelo ORM de SQLAlchemy para la tabla 'tasks'.

    Separado del modelo de dominio (domain/task.py) aplicando el principio S
    (Single Responsibility): el ORM gestiona la persistencia, el dominio
    gestiona la lógica de negocio.
    """

    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(2000), nullable=False, default="")
    priority: Mapped[str] = mapped_column(String(20), nullable=False)
    effort_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    assigned_to: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    risk_analysis: Mapped[str] = mapped_column(String(2000), nullable=False, default="")
    risk_mitigation: Mapped[str] = mapped_column(String(2000), nullable=False, default="")
