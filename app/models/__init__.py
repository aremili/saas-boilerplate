"""SQLAlchemy models - Re-exports for backward compatibility."""
from app.common.models import Base
from app.modules.task.models import Task

__all__ = ["Base", "Task"]
