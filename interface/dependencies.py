from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from application.ai_task_service import AITaskService
from application.task_manager import TaskManager
from infrastructure.ai_provider import AIProvider
from infrastructure.database import get_db
from infrastructure.sql_repository import SqlRepository


@lru_cache
def get_ai_provider() -> AIProvider:
    """Singleton del cliente LLM — evita crear múltiples conexiones HTTP."""
    return AIProvider()


def get_task_manager(db: Annotated[Session, Depends(get_db)]) -> TaskManager:
    """Proveedor de TaskManager para FastAPI Depends().

    Inyecta SqlRepository con la sesión activa de la petición, cumpliendo
    el principio D de SOLID: el router no conoce SqlRepository ni Session,
    solo TaskManager.
    """
    return TaskManager(SqlRepository(db))


def get_ai_service() -> AITaskService:
    """Proveedor de AITaskService para FastAPI Depends().

    Inyecta el proveedor LLM singleton, desacoplando la capa de interfaz
    de la implementación concreta del proveedor de IA.
    """
    return AITaskService(get_ai_provider())
