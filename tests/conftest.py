"""Fixtures compartidos para toda la suite de tests.

El cliente HTTP se construye sobrescribiendo las dependencias de FastAPI
(app.dependency_overrides) en lugar de parchear módulos. Se usa SQLite en
memoria como base de datos de test, lo que garantiza aislamiento total y
cero dependencias externas en CI — principio D de SOLID aplicado a tests.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from application.ai_task_service import AITaskService
from application.task_manager import TaskManager
from infrastructure.database import Base
from infrastructure.sql_repository import SqlRepository
from interface.dependencies import get_ai_service, get_task_manager
from main import app

_SQLITE_URL = "sqlite:///:memory:"


class _DummyProvider:
    """Proveedor LLM de prueba — sustituible gracias a AIProviderProtocol."""

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


@pytest.fixture
def db_session():
    """Sesión de SQLite en memoria, aislada por test.

    Las tablas se crean al inicio y se eliminan al finalizar; cada test
    arranca con una BD vacía sin posibilidad de contaminación entre casos.
    """
    engine = create_engine(
        _SQLITE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def task_manager(db_session):
    """TaskManager con repositorio apuntando a SQLite en memoria."""
    return TaskManager(SqlRepository(db_session))


@pytest.fixture
def ai_service():
    """AITaskService con proveedor simulado, sin llamadas reales a LLM."""
    return AITaskService(_DummyProvider())


@pytest.fixture
def client(task_manager, ai_service):
    """TestClient de FastAPI con dependencias sobreescritas para tests.

    Limpia los overrides al finalizar cada test para evitar contaminación
    entre casos de prueba.
    """
    app.dependency_overrides[get_task_manager] = lambda: task_manager
    app.dependency_overrides[get_ai_service] = lambda: ai_service
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
