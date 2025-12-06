"""Common base classes and core features shared across all modules."""
from app.common.models import Base
from app.common.repositories import BaseRepository
from app.common.services import BaseService

__all__ = ["Base", "BaseRepository", "BaseService"]
