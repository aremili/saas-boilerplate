"""
Task Manager Demo - HTMX + Stimulus + FastAPI Example

This demonstrates:
- HTMX for server communication (hx-get, hx-post, hx-delete, hx-swap)
- Stimulus for client-side interactions (modals, alerts, counters)
- FastAPI for backend logic
- Partial templates for HTMX responses
"""

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from app.core.templates import templates
from typing import Optional
from datetime import datetime
import uuid

router = APIRouter(prefix="/tasks", tags=["tasks"])

# In-memory task storage (replace with database in production)
TASKS: dict[str, dict] = {
    "1": {"id": "1", "title": "Learn Stimulus", "completed": False, "priority": 2, "created_at": datetime.now()},
    "2": {"id": "2", "title": "Build HTMX components", "completed": True, "priority": 1, "created_at": datetime.now()},
    "3": {"id": "3", "title": "Integrate with FastAPI", "completed": False, "priority": 3, "created_at": datetime.now()},
}


@router.get("/", response_class=HTMLResponse)
async def tasks_page(request: Request):
    """Full page with task list"""
    tasks = sorted(TASKS.values(), key=lambda t: (t["completed"], -t["priority"]))
    return templates.TemplateResponse(
        "pages/tasks.html",
        {
            "request": request,
            "tasks": tasks,
            "total": len(tasks),
            "completed": sum(1 for t in tasks if t["completed"]),
        }
    )


@router.get("/list", response_class=HTMLResponse)
async def tasks_list(request: Request):
    """Partial: just the task list (for HTMX refresh)"""
    tasks = sorted(TASKS.values(), key=lambda t: (t["completed"], -t["priority"]))
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
    title: str = Form(...),
    priority: int = Form(2),
    completed: str = Form("false"),  # Checkbox sends "true" or "false" as string
):
    """Create a new task, return the new task row"""
    task_id = str(uuid.uuid4())[:8]
    TASKS[task_id] = {
        "id": task_id,
        "title": title,
        "completed": completed.lower() == "true",  # Convert string to bool
        "priority": priority,
        "created_at": datetime.now(),
    }
    
    # Return just the new task row + trigger alert
    response = templates.TemplateResponse(
        "partials/task_item.html",
        {"request": request, "task": TASKS[task_id]}
    )
    # HTMX trigger to show success alert
    response.headers["HX-Trigger"] = "taskCreated"
    return response


@router.patch("/{task_id}/toggle", response_class=HTMLResponse)
async def toggle_task(request: Request, task_id: str):
    """Toggle task completion, return updated task row"""
    if task_id in TASKS:
        TASKS[task_id]["completed"] = not TASKS[task_id]["completed"]
        response = templates.TemplateResponse(
            "partials/task_item.html",
            {"request": request, "task": TASKS[task_id]}
        )
        # Trigger stats refresh
        response.headers["HX-Trigger"] = "taskToggled"
        return response
    return HTMLResponse("Task not found", status_code=404)


@router.delete("/{task_id}", response_class=HTMLResponse)
async def delete_task(request: Request, task_id: str):
    """Delete a task, return empty (HTMX will remove element)"""
    if task_id in TASKS:
        del TASKS[task_id]
        response = HTMLResponse("")
        response.headers["HX-Trigger"] = "taskDeleted"
        return response
    return HTMLResponse("Task not found", status_code=404)


@router.get("/stats", response_class=HTMLResponse)
async def task_stats(request: Request):
    """Partial: task statistics"""
    total = len(TASKS)
    completed = sum(1 for t in TASKS.values() if t["completed"])
    return templates.TemplateResponse(
        "partials/task_stats.html",
        {
            "request": request,
            "total": total,
            "completed": completed,
        }
    )
