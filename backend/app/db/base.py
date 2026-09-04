"""Shared declarative base for all IdeaLens ORM models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base for the IdeaLens schema."""

    pass