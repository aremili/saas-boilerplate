from fastapi import APIRouter, Request
from app.core.templates import templates

router = APIRouter()

@router.get("/")
async def home(request: Request):
    return templates.TemplateResponse("pages/index.html", {"request": request})
