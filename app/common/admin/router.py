"""
Admin Routes - Platform Administration

HTMX-based admin pages for superusers to manage platform settings,
staff permissions, and other administrative functions.
"""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse

from app.core.templates import templates
from app.common.auth.dependencies import SuperUser
from app.common.auth.registry import permissions, roles

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/permissions", response_class=HTMLResponse)
async def permissions_page(request: Request, user: SuperUser):
    """
    Render permissions page listing all registered permissions.
    
    Only accessible by superusers.
    """
    all_permissions = permissions.all()
    all_roles = roles.all()
    
    return templates.TemplateResponse(
        "admin/pages/permissions.html",
        {
            "request": request,
            "user": user,
            "permissions": all_permissions,
            "roles": all_roles,
        }
    )
