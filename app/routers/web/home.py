from fastapi import APIRouter, Request
from app.core.templates import templates

router = APIRouter()


@router.get("/")
async def home(request: Request):
    return templates.TemplateResponse("pages/landing.html", {"request": request})


@router.get("/demo")
async def demo(request: Request):
    """Component demo page"""
    return templates.TemplateResponse("pages/index.html", {"request": request})
