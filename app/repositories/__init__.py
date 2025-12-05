"""Repository pattern implementations - Re-exports for backward compatibility."""
from app.common.repositories import BaseRepository
from app.modules.task.repositories import TaskRepository

__all__ = ["BaseRepository", "TaskRepository"]
