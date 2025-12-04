import json
from pathlib import Path
from fastapi.templating import Jinja2Templates
from app.core.config import settings

templates = Jinja2Templates(directory="app/templates")

def get_vite_asset(path: str):
    if settings.ENVIRONMENT == "development":
        # If path is main.js, it's in src/
        if path == "main.js":
            return f"http://localhost:5173/src/{path}"
        return f"http://localhost:5173/{path}"
    
    manifest_path = Path("app/static/.vite/manifest.json")
    if not manifest_path.exists():
        # Fallback or error
        return f"/static/{path}"
        
    with open(manifest_path) as f:
        manifest = json.load(f)
        
    # Manifest keys are relative to root (src)
    # e.g. "main.js" -> file: "assets/main-....js"
    if path in manifest:
        return f"/static/{manifest[path]['file']}"
    return f"/static/{path}"

templates.env.globals["vite_asset"] = get_vite_asset
templates.env.globals["settings"] = settings
