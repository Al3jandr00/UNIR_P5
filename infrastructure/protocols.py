from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class TaskRepositoryProtocol(Protocol):
    """Contrato formal para cualquier implementación de persistencia de tareas.

    Aplicando el principio D (Dependency Inversion) y el principio I
    (Interface Segregation) de SOLID: los módulos de alto nivel (TaskManager)
    dependen de esta abstracción, no de SqlRepository directamente.
    """

    def load(self) -> list[dict]: ...
    def save(self, data: list[dict]) -> None: ...


@runtime_checkable
class AIProviderProtocol(Protocol):
    """Contrato formal para cualquier proveedor LLM.

    Permite sustituir el proveedor real por cualquier implementación alternativa
    (mocks, otros LLMs) sin modificar AITaskService — principio O (Open/Closed).
    """

    def generate_description(self, task_data: dict) -> str: ...
    def categorize_task(self, task_data: dict) -> str: ...
    def estimate_effort(self, task_data: dict) -> float: ...
    def analyze_risks(self, task_data: dict) -> str: ...
    def generate_mitigation(self, task_data: dict, risk_analysis: str) -> str: ...
