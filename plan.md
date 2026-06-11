# Plan del Proyecto — Entregable 5

## Objetivo

Completar el ciclo DevOps de la API de gestión de tareas desplegándola en la nube de
Azure: añadir una base de datos real gestionada con docker-compose, publicar la imagen en
Azure Container Registry (ACR), desplegar en Azure Container Apps y automatizar todo el
flujo mediante GitHub Actions con un pipeline que prueba, construye, publica y despliega.

---

## Contexto y base de trabajo

| Entregable | Tecnología | Lo que aporta a este proyecto |
|------------|------------|-------------------------------|
| Entregable 1 | FastAPI + JSON | Arquitectura en 4 capas, CRUD de tareas |
| Entregable 2 | FastAPI + OpenAI | Endpoints de IA (describe, categorize, estimate, audit) |
| Entregable 3 | FastAPI + SQLAlchemy + MySQL | Persistencia relacional, schemas Pydantic, modelos ORM |
| Entregable 4 | FastAPI + Docker + GitHub Actions | Dockerfile non-root, pipeline CI/CD, Protocols DI, imagen en Docker Hub |
| **Entregable 5** | **FastAPI + docker-compose + ACR + Azure Container Apps** | Despliegue cloud completo con BD y CI/CD de extremo a extremo |

### Decisiones de diseño previas que conservamos

- **FastAPI** en lugar de Flask (coherencia con los 4 entregables anteriores; cumple el mismo rol de backend HTTP).
- **Arquitectura en 4 capas** (domain / application / infrastructure / interface) con `Protocol` como contratos entre capas.
- **Inyección de dependencias** con `Depends()` de FastAPI y `@lru_cache` para singletons.
- **Usuario non-root** en el Dockerfile.
- **Tests con `TestClient`** y `app.dependency_overrides` para aislar dependencias externas.

---

## Arquitectura objetivo del Entregable 5

```
Proyecto 5/
├── domain/
│   └── task.py                    ← sin cambios respecto a P4
├── application/
│   ├── task_manager.py            ← sin cambios (opera contra el protocolo)
│   └── ai_task_service.py         ← sin cambios
├── infrastructure/
│   ├── protocols.py               ← añade DatabaseSessionProtocol
│   ├── settings.py                ← añade variables de BD (DB_URL / DB_*)
│   ├── ai_provider.py             ← sin cambios
│   ├── database.py                ← NUEVO: engine + SessionLocal de SQLAlchemy
│   └── sql_repository.py          ← NUEVO: implementa TaskRepositoryProtocol sobre SQLAlchemy
├── interface/
│   ├── dependencies.py            ← actualizado: get_db, get_task_manager usa sql_repository
│   ├── routes.py                  ← sin cambios funcionales
│   └── ai_routes.py               ← sin cambios funcionales
├── tests/
│   ├── conftest.py                ← actualizado: SQLite en memoria para tests
│   ├── test_task.py               ← sin cambios
│   ├── test_task_manager.py       ← sin cambios
│   ├── test_ai_task_service.py    ← sin cambios
│   └── test_routes.py             ← sin cambios
├── .github/
│   └── workflows/
│       └── ci-cd.yml              ← ACTUALIZADO: añade push a ACR y deploy a Azure
├── Dockerfile                     ← actualizado: acepta DB_URL vía entorno
├── .dockerignore                  ← sin cambios
├── docker-compose.yml             ← NUEVO: servicios app + postgres
├── .env.example                   ← actualizado: variables de BD y Azure
├── requirements.txt               ← actualizado: añade SQLAlchemy, psycopg2-binary
├── main.py                        ← actualizado: v5.0.0, dispara creación de tablas
├── plan.md
├── memoria_tecnica.md
└── README.md
```

---

## Pasos planificados

### Fase 1 — Actualización de la capa de dominio e infraestructura de BD

**Objetivo**: sustituir `JsonRepository` por un repositorio SQLAlchemy que implementa el
mismo `TaskRepositoryProtocol`, cumpliendo el **principio O (Open/Closed)** — el
`TaskManager` no se modifica, solo se cambia la implementación inyectada.

- [ ] Añadir dependencias de BD en `requirements.txt`:
  - `SQLAlchemy==2.0.41`
  - `psycopg2-binary==2.9.10` (PostgreSQL en producción)
  - `aiosqlite` no necesario — usamos SQLAlchemy síncrono para simplicidad
- [ ] Crear `infrastructure/database.py`:
  - Función `get_engine(db_url: str) -> Engine` que crea el engine desde la URL
  - `SessionLocal` como `sessionmaker` con `autocommit=False`
  - `Base = declarative_base()` compartido
  - Función `get_db()` como generador (para inyección en FastAPI)
- [ ] Crear modelo ORM `infrastructure/task_model.py`:
  - Clase `TaskModel(Base)` con columnas mapeadas a los campos de `domain/task.py`
  - Separar el modelo ORM (infraestructura) del modelo de dominio (principio S de SOLID)
- [ ] Crear `infrastructure/sql_repository.py`:
  - Clase `SqlRepository` que recibe una sesión SQLAlchemy en constructor
  - Implementa `load() -> list[dict]` y `save(data: list[dict]) -> None` del protocolo
  - La conversión dominio ↔ ORM ocurre dentro de este repositorio (**principio S**)
- [ ] Actualizar `infrastructure/protocols.py`:
  - Mantener `TaskRepositoryProtocol` y `AIProviderProtocol` sin cambios
  - Los protocolos no cambian porque el contrato ya era agnóstico de la persistencia
- [ ] Actualizar `infrastructure/settings.py`:
  - Añadir `DB_URL: str` construida desde variables individuales `DB_HOST`, `DB_PORT`,
    `DB_NAME`, `DB_USER`, `DB_PASSWORD` (compatible con docker-compose y Azure)

### Fase 2 — Actualización de la capa de interface (inyección de BD)

**Objetivo**: cablear la sesión de BD en el grafo de dependencias de FastAPI sin acoplar
las rutas a la implementación concreta (**principio D**).

- [ ] Actualizar `interface/dependencies.py`:
  - Añadir `get_db()` como `Depends` que entrega y cierra la sesión automáticamente
  - `get_task_manager(db: Session = Depends(get_db)) -> TaskManager`:
    construye `SqlRepository(db)` e inyecta en `TaskManager`
  - Los routers no se modifican (reciben `TaskManager` por DI como en P4)
- [ ] Actualizar `main.py`:
  - Versión `5.0.0`
  - En el evento `startup`: llamar a `Base.metadata.create_all(bind=engine)` para crear
    las tablas si no existen (estrategia simple; en producción se usaría Alembic)

### Fase 3 — Actualización de tests

**Objetivo**: garantizar que el cambio de repositorio no rompe los contratos; los tests de
rutas no deben saber que existe una BD real (**principio D en tests**).

- [ ] Actualizar `tests/conftest.py`:
  - Fixture `db_engine` con SQLite en memoria (`sqlite:///:memory:`) + `create_all`
  - Fixture `db_session` que entrega sesión de test y hace rollback al finalizar
  - Override de `get_db` en `app.dependency_overrides` con la sesión de test
  - Fixture `client` adaptada para el nuevo grafo de dependencias
- [ ] Verificar que todos los tests de P4 siguen pasando con la nueva infraestructura
- [ ] Añadir al menos un test de integración que verifique la persistencia real en SQLite

### Fase 4 — docker-compose

**Objetivo**: orquestar la app + base de datos localmente con un solo comando, tal como
pide el enunciado (`docker-compose up --build`).

- [ ] Crear `docker-compose.yml` con dos servicios:
  - **`db`**: imagen `postgres:16-alpine`, volumen persistente `pgdata`,
    variables `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
  - **`app`**: build desde `Dockerfile`, depende de `db`, expone puerto `8000`,
    pasa `DB_HOST=db`, `DB_PORT=5432`, y demás variables de BD; pasa también
    `OPENAI_API_KEY` y `AI_ALLOW_LOCAL_FALLBACK`
  - Usar `healthcheck` en `db` y `condition: service_healthy` en `app` para evitar
    arranques en race condition
- [ ] Crear `.env.example` actualizado con todas las variables necesarias
- [ ] Verificar funcionamiento local: `docker-compose up --build`

### Fase 5 — Azure Container Registry

**Objetivo**: registrar la imagen en ACR (el requisito de Azure del enunciado) en lugar de
Docker Hub.

- [ ] Crear Azure Container Registry con Azure CLI:
  ```bash
  az group create --name rg-taskmanager --location westeurope
  az acr create --resource-group rg-taskmanager \
                --name taskmanageracr5 \
                --sku Basic
  ```
- [ ] Documentar comandos de login y push manual (para la memoria técnica):
  ```bash
  az acr login --name taskmanageracr5
  docker tag task-manager-api:latest taskmanageracr5.azurecr.io/task-manager-api:v5
  docker push taskmanageracr5.azurecr.io/task-manager-api:v5
  ```
- [ ] Anotar el nombre completo del registry (`taskmanageracr5.azurecr.io`) para usarlo
  en el pipeline y en el despliegue de Azure Container Apps

### Fase 6 — Despliegue en Azure Container Apps

**Objetivo**: ejecutar la app en la nube con conexión a una base de datos PostgreSQL
gestionada (Azure Database for PostgreSQL Flexible Server) o con la instancia del
contenedor de BD.

> **Decisión de diseño**: usar **Azure Container Apps** (preferible a Container Instances
> para cargas de trabajo HTTP porque incluye escalado, revisiones y dominios HTTPS
> automáticos). La BD se conectará como variable de entorno apuntando al servidor
> PostgreSQL de Azure.

- [ ] Crear Azure Database for PostgreSQL Flexible Server (o usar contenedor de BD
  como servicio secundario en Container Apps si el evaluador acepta la opción simple):
  ```bash
  az postgres flexible-server create \
    --resource-group rg-taskmanager \
    --name taskmanager-db \
    --admin-user adminuser \
    --admin-password <password> \
    --sku-name Standard_B1ms \
    --tier Burstable \
    --public-access 0.0.0.0
  ```
- [ ] Crear Container Apps Environment:
  ```bash
  az containerapp env create \
    --name taskmanager-env \
    --resource-group rg-taskmanager \
    --location westeurope
  ```
- [ ] Desplegar la app:
  ```bash
  az containerapp create \
    --name task-manager-api \
    --resource-group rg-taskmanager \
    --environment taskmanager-env \
    --image taskmanageracr5.azurecr.io/task-manager-api:latest \
    --registry-server taskmanageracr5.azurecr.io \
    --target-port 8000 \
    --ingress external \
    --env-vars DB_HOST=<servidor> DB_NAME=tasks DB_USER=adminuser DB_PASSWORD=<pass> \
               OPENAI_API_KEY=<key> AI_ALLOW_LOCAL_FALLBACK=true
  ```
- [ ] Verificar acceso público al endpoint HTTPS generado por Container Apps

### Fase 7 — Pipeline CI/CD extendido (GitHub Actions)

**Objetivo**: ampliar el pipeline del P4 con los pasos de publicación en ACR y despliegue
automático en Azure Container Apps.

El pipeline final tendrá tres jobs secuenciales:

```
test → docker-build-push-acr → azure-deploy
```

- [ ] Crear `.github/workflows/ci-cd.yml` con:
  - **Job `test`** (sin cambios respecto a P4):
    - checkout → Python 3.12 → `pip install -r requirements.txt` → `pytest tests/ -v`
    - Variable de entorno: `AI_ALLOW_LOCAL_FALLBACK=true`
  - **Job `docker-build-push-acr`** (nuevo, sustituye al de Docker Hub):
    - `needs: test`
    - Solo en `push` a `main`
    - Login en ACR con `azure/docker-login@v2` (usando secretos `ACR_LOGIN_SERVER`,
      `ACR_USERNAME`, `ACR_PASSWORD`)
    - `docker build` y `docker push` con tags `latest` y SHA del commit
  - **Job `azure-deploy`** (nuevo):
    - `needs: docker-build-push-acr`
    - Login en Azure con `azure/login@v2` (secreto `AZURE_CREDENTIALS`)
    - Actualización de la imagen en Container Apps:
      ```bash
      az containerapp update \
        --name task-manager-api \
        --resource-group rg-taskmanager \
        --image taskmanageracr5.azurecr.io/task-manager-api:${{ github.sha }}
      ```
- [ ] Configurar secretos en GitHub:
  - `ACR_LOGIN_SERVER` — servidor ACR (ej. `taskmanageracr5.azurecr.io`)
  - `ACR_USERNAME` — nombre de usuario ACR (del comando `az acr credential show`)
  - `ACR_PASSWORD` — contraseña ACR
  - `AZURE_CREDENTIALS` — JSON del service principal (del comando `az ad sp create-for-rbac`)
  - `OPENAI_API_KEY` — clave de la API de OpenAI (opcional si se usa fallback local)

### Fase 8 — Monitoreo y validación

**Objetivo**: cumplir el requisito de monitorización del enunciado y preparar el material
para la memoria técnica.

- [ ] Verificar logs en tiempo real desde CLI:
  ```bash
  az containerapp logs show \
    --name task-manager-api \
    --resource-group rg-taskmanager \
    --follow
  ```
- [ ] Realizar pruebas de conexión con la BD desde la app desplegada:
  - `GET /tasks` — verifica lectura desde PostgreSQL de Azure
  - `POST /tasks` — verifica escritura y persistencia
  - `POST /ai/tasks/describe` — verifica integración con OpenAI (o fallback local)
- [ ] Capturar pantallas del pipeline ejecutado en GitHub Actions (los 3 jobs en verde)
- [ ] Capturar pantallas de los logs en Azure Portal o CLI

### Fase 9 — Documentación y memoria técnica

- [ ] Actualizar `README.md` con:
  - URLs reales del repositorio GitHub y del endpoint Azure
  - Instrucciones de ejecución local con `docker-compose`
  - Variables de entorno necesarias
- [ ] Crear `memoria_tecnica.md` con:
  - Narrativa técnica de cada fase
  - Capturas de pantalla del proceso
  - Explicación de decisiones de diseño (FastAPI vs Flask, ACR vs Docker Hub, etc.)
- [ ] Verificar cobertura de la rúbrica (ver tabla más abajo)

---

## Verificación final contra la rúbrica

| Criterio | Peso | Requisito | Cubierto en |
|----------|------|-----------|-------------|
| Configuración y estructuración | 15% | Repositorio GitHub con estructura clara | Fase 1–3, Readme |
| Contenerización | 15% | Dockerfile + docker-compose.yml con BD | Fase 4 |
| Registro en Azure | 20% | Imagen en ACR | Fase 5 |
| Despliegue en Azure | 20% | Container Apps con BD accesible | Fase 6 |
| Pipeline CI/CD | 20% | Test + build + push ACR + deploy automático | Fase 7 |
| Monitoreo y validación | 10% | Logs de Azure + pruebas de conexión | Fase 8 |

---

## Decisiones técnicas relevantes

| Decisión | Alternativa descartada | Motivo |
|----------|------------------------|--------|
| FastAPI (no Flask/Node.js) | Flask (indicado en el enunciado) | Coherencia con los 4 entregables anteriores |
| PostgreSQL | MySQL | Imagen `postgres:16-alpine` más ligera; mejor soporte en Azure Database Flexible Server |
| SQLAlchemy síncrono | asyncpg + SQLAlchemy async | Simplicidad; el ORM async requiere reescribir todos los endpoints |
| Azure Container Apps | Azure Container Instances | Container Apps gestiona HTTPS, escalado y revisiones automáticamente |
| Azure DB for PostgreSQL Flexible | Contenedor Postgres en Azure | El PaaS de BD es la práctica real de producción que el entregable busca demostrar |
| `SqlRepository` inyectado | BD acoplada en `TaskManager` | Principio D: `TaskManager` sigue operando contra el protocolo sin conocer SQLAlchemy |
| SQLite en memoria para tests | Levantar Postgres en tests | Rapidez y cero dependencias externas en CI; SQLAlchemy abstrae el dialecto |
| `Base.metadata.create_all` en startup | Alembic migrations | Simplicidad para el entregable; en producción real se usaría Alembic |

---

## Diagrama del flujo CI/CD

```
git push main
     │
     ▼
┌────────────────────────────────────┐
│ Job: test                          │
│  • pytest tests/ -v (SQLite mem)  │
└────────────────┬───────────────────┘
                 │ OK
                 ▼
┌────────────────────────────────────┐
│ Job: docker-build-push-acr         │
│  • docker build                    │
│  • docker push taskmanageracr5/... │
│    tags: latest, <SHA>             │
└────────────────┬───────────────────┘
                 │ OK
                 ▼
┌────────────────────────────────────┐
│ Job: azure-deploy                  │
│  • az containerapp update          │
│    image: .../task-manager-api:<SHA>│
└────────────────────────────────────┘
                 │
                 ▼
      Azure Container Apps
      (acceso HTTPS externo)
             │
             ▼
  Azure DB for PostgreSQL
```
