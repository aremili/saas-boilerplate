from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.routers.web import home, tasks

app = FastAPI(title=settings.PROJECT_NAME)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(home.router)
app.include_router(tasks.router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

