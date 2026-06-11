from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, status

from application.ai_task_service import AITaskService
from interface.dependencies import get_ai_service

router = APIRouter(prefix="/ai/tasks", tags=["ai-tasks"])

AIServiceDep = Annotated[AITaskService, Depends(get_ai_service)]


@router.post("/describe", status_code=status.HTTP_200_OK)
def describe_task(body: Annotated[dict, Body()], service: AIServiceDep) -> dict:
    try:
        return service.describe_task(body)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))


@router.post("/categorize", status_code=status.HTTP_200_OK)
def categorize_task(body: Annotated[dict, Body()], service: AIServiceDep) -> dict:
    try:
        return service.categorize_task(body)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))


@router.post("/estimate", status_code=status.HTTP_200_OK)
def estimate_task(body: Annotated[dict, Body()], service: AIServiceDep) -> dict:
    try:
        return service.estimate_task(body)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))


@router.post("/audit", status_code=status.HTTP_200_OK)
def audit_task(body: Annotated[dict, Body()], service: AIServiceDep) -> dict:
    try:
        return service.audit_task(body)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
