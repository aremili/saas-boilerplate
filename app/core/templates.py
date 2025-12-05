from fastapi.templating import Jinja2Templates
from app.core.config import settings

templates = Jinja2Templates(directory="app/templates")

# Global template variables
templates.env.globals["settings"] = settings

