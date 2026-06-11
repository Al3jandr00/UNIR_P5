from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from infrastructure.settings import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(
    settings.db_url,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Generador de sesiones SQLAlchemy para FastAPI Depends().

    Abre una sesión, la cede al endpoint y la cierra siempre al finalizar,
    incluso si se lanza una excepción — patrón estándar de gestión de recursos.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
