"""
Task Manager Demo - HTMX + Stimulus + FastAPI Example

This demonstrates:
- HTMX for server communication (hx-get, hx-post, hx-delete, hx-swap)
- Stimulus for client-side interactions (modals, alerts, counters)
- FastAPI for backend logic with proper database persistence
- Repository pattern with dependency injection
- Partial templates for HTMX responses
"""

from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from app.core.templates import templates
from app.core.database import get_db
from app.repositories.task import TaskRepository

router = APIRouter(prefix="/tasks", tags=["tasks"])


# Dependency for TaskRepository injection
async def get_task_repo(db: AsyncSession = Depends(get_db)) -> TaskRepository:
    """Provide TaskRepository as a dependency."""
    return TaskRepository(db)


# Type alias for cleaner route signatures
TaskRepoDep = Annotated[TaskRepository, Depends(get_task_repo)]


@router.get("/", response_class=HTMLResponse)
async def tasks_page(request: Request, repo: TaskRepoDep):
    """Full page with task list"""
    tasks = await repo.get_all_sorted()
    total, completed = await repo.count_stats()
    return templates.TemplateResponse(
        "pages/tasks.html",
        {
            "request": request,
            "tasks": tasks,
            "total": total,
            "completed": completed,
        }
    )


@router.get("/list", response_class=HTMLResponse)
async def tasks_list(request: Request, repo: TaskRepoDep):
    """Partial: just the task list (for HTMX refresh)"""
    tasks = await repo.get_all_sorted()
    return templates.TemplateResponse(
        "partials/task_list.html",
        {
            "request": request,
            "tasks": tasks,
        }
    )


@router.post("/", response_class=HTMLResponse)
async def create_task(
    request: Request,
    repo: TaskRepoDep,
    title: str = Form(...),
    priority: int = Form(2),
    completed: str = Form("false"),
):
    """Create a new task, return the new task row + OOB alert"""
    task = await repo.create(
        title=title,
        completed=completed.lower() == "true",
        priority=priority,
    )
    
    # Return the new task row + OOB alert
    task_html = templates.get_template("partials/task_item.html").render(
        request=request, task=task
    )
    alert_html = templates.get_template("partials/alert_oob.html").render(
        message="Task created successfully!", alert_type="success"
    )
    
    response = HTMLResponse(task_html + alert_html)
    response.headers["HX-Trigger"] = "taskCreated"
    return response


@router.patch("/{task_id}/toggle", response_class=HTMLResponse)
async def toggle_task(request: Request, task_id: int, repo: TaskRepoDep):
    """Toggle task completion, return updated task row"""
    task = await repo.toggle_completed(task_id)
    if task:
        response = templates.TemplateResponse(
            "partials/task_item.html",
            {"request": request, "task": task}
        )
        response.headers["HX-Trigger"] = "taskToggled"
        return response
    return HTMLResponse("Task not found", status_code=404)


@router.delete("/{task_id}", response_class=HTMLResponse)
async def delete_task(request: Request, task_id: int, repo: TaskRepoDep):
    """Delete a task, return OOB alert (HTMX will remove original element)"""
    task = await repo.get(task_id)
    if task:
        await repo.delete(task)
        alert_html = templates.get_template("partials/alert_oob.html").render(
            message="Task deleted", alert_type="info"
        )
        response = HTMLResponse(alert_html)
        response.headers["HX-Trigger"] = "taskDeleted"
        return response
    return HTMLResponse("Task not found", status_code=404)


@router.get("/stats", response_class=HTMLResponse)
async def task_stats(request: Request, repo: TaskRepoDep):
    """Partial: task statistics"""
    total, completed = await repo.count_stats()
    return templates.TemplateResponse(
        "partials/task_stats.html",
        {
            "request": request,
            "total": total,
            "completed": completed,
        }
    )
