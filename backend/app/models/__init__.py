"""
ORM models package.

Import model modules here so Alembic autogenerate and `Base.metadata` discover
them. Models are added per phase (auth → P4, travel → P5, etc.).
"""
from app.db.base import Base  # noqa: F401

__all__ = ["Base"]
