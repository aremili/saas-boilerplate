"""Task repository"""
from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.task.models import Task
from app.common.repositories import BaseRepository


class TaskRepository(BaseRepository[Task]):
    """Repository for Task model with custom query methods."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Task, session)
    
    async def get_all_sorted(self) -> Sequence[Task]:
        """Get all tasks sorted by completed status (incomplete first) and priority (high first)."""
        result = await self.session.execute(
            select(Task).order_by(Task.completed, Task.priority.desc())
        )
        return result.scalars().all()
    
    async def toggle_completed(self, task_id: int) -> Optional[Task]:
        """Toggle the completed status of a task."""
        task = await self.get(task_id)
        if task:
            task.completed = not task.completed
            await self.session.commit()
            await self.session.refresh(task)
        return task
    
    async def count_stats(self) -> tuple[int, int]:
        """Return (total, completed) counts."""
        tasks = await self.get_all()
        total = len(tasks)
        completed = sum(1 for t in tasks if t.completed)
        return total, completed
