"""
Abstract repository base class defining the repository pattern interface.
"""

import builtins
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from sqlalchemy.orm import Session

T = TypeVar("T")  # Generic type for model


class AbstractRepository(ABC, Generic[T]):
    """Abstract base repository with common CRUD operations."""

    def __init__(self, db: Session, model: type[T]):
        self.db = db
        self.model = model

    @abstractmethod
    def get_by_id(self, id: str) -> T | None:
        """Get entity by primary key."""
        pass

    @abstractmethod
    def create(self, obj: T) -> T:
        """Create and persist a new entity."""
        pass

    @abstractmethod
    def update(self, id: str, update_data: dict[str, Any]) -> T | None:
        """Update an existing entity by ID."""
        pass

    @abstractmethod
    def delete(self, id: str) -> bool:
        """Delete an entity by ID."""
        pass

    @abstractmethod
    def list(self, skip: int = 0, limit: int = 100) -> list[T]:
        """List all entities with pagination."""
        pass

    @abstractmethod
    def list_by_filter(
        self, filters: dict[str, Any], skip: int = 0, limit: int = 100
    ) -> builtins.list[T]:
        """List entities matching filter criteria."""
        pass


class Repository(AbstractRepository[T]):
    """Concrete repository implementation using SQLAlchemy."""

    def get_by_id(self, id: str) -> T | None:
        """Get entity by primary key."""
        return self.db.query(self.model).filter(self.model.id == id).first()

    def create(self, obj: T) -> T:
        """Create and persist a new entity."""
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, id: str, update_data: dict[str, Any]) -> T | None:
        """Update an existing entity by ID."""
        entity = self.get_by_id(id)
        if not entity:
            return None
        for key, value in update_data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def delete(self, id: str) -> bool:
        """Delete an entity by ID."""
        entity = self.get_by_id(id)
        if not entity:
            return False
        self.db.delete(entity)
        self.db.commit()
        return True

    def list(self, skip: int = 0, limit: int = 100) -> list[T]:
        """List all entities with pagination."""
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def list_by_filter(
        self, filters: dict[str, Any], skip: int = 0, limit: int = 100
    ) -> builtins.list[T]:
        """List entities matching filter criteria."""
        query = self.db.query(self.model)
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        return query.offset(skip).limit(limit).all()
