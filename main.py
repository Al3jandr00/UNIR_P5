import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from interface.routes import router as tasks_router
from interface.ai_routes import router as ai_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    from infrastructure.database import Base, engine
    import infrastructure.task_model  # noqa: F401 — registra TaskModel en Base.metadata
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Task Manager API", version="5.0.0", lifespan=lifespan)
app.include_router(tasks_router)
app.include_router(ai_router)


@app.get("/", tags=["greeting"])
def greeting() -> dict:
    return {
        "message": "Bienvenido a la API de Gestión de Tareas",
        "version": "5.0.0",
        "descripcion": "API REST para gestión de tareas con integración de IA generativa, BD PostgreSQL, contenedores Docker y despliegue en Azure Container Apps.",
        "docs": "/docs",
        "endpoints": {
            "GET /tasks": "Listar todas las tareas",
            "POST /tasks": "Crear una tarea",
            "GET /tasks/{id}": "Obtener una tarea por ID",
            "PUT /tasks/{id}": "Actualizar una tarea",
            "DELETE /tasks/{id}": "Eliminar una tarea",
            "POST /ai/tasks/describe": "Generar descripción con IA",
            "POST /ai/tasks/categorize": "Categorizar tarea con IA",
            "POST /ai/tasks/estimate": "Estimar esfuerzo con IA",
            "POST /ai/tasks/audit": "Analizar riesgos con IA",
        },
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
