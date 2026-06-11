from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, status

from application.task_manager import TaskManager
from interface.dependencies import get_task_manager

router = APIRouter(prefix="/tasks", tags=["tasks"])

TaskManagerDep = Annotated[TaskManager, Depends(get_task_manager)]


@router.get("", status_code=status.HTTP_200_OK)
def get_all_tasks(manager: TaskManagerDep) -> list[dict]:
    return [t.to_dict() for t in manager.get_all()]


@router.get("/{task_id}", status_code=status.HTTP_200_OK)
def get_task(task_id: str, manager: TaskManagerDep) -> dict:
    task = manager.get_by_id(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tarea '{task_id}' no encontrada.")
    return task.to_dict()


@router.post("", status_code=status.HTTP_201_CREATED)
def create_task(body: Annotated[dict, Body()], manager: TaskManagerDep) -> dict:
    try:
        return manager.create(body).to_dict()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.put("/{task_id}", status_code=status.HTTP_200_OK)
def update_task(task_id: str, body: Annotated[dict, Body()], manager: TaskManagerDep) -> dict:
    try:
        task = manager.update(task_id, body)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tarea '{task_id}' no encontrada.")
    return task.to_dict()


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: str, manager: TaskManagerDep) -> None:
    if not manager.delete(task_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tarea '{task_id}' no encontrada.")
