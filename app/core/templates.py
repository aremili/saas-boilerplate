"""Jinja2 template configuration with support for module templates."""
from pathlib import Path
from fastapi.templating import Jinja2Templates
from jinja2 import ChoiceLoader, FileSystemLoader
from app.core.config import settings


def discover_template_directories() -> list[str]:
    """Discover all template directories from shared templates and modules."""
    base_path = Path(__file__).parent.parent
    
    # Start with shared templates directory
    template_dirs = [str(base_path / "templates")]
    
    # Discover module template directories
    modules_path = base_path / "modules"
    if modules_path.exists():
        for module_dir in modules_path.iterdir():
            if module_dir.is_dir():
                templates_dir = module_dir / "templates"
                if templates_dir.exists():
                    template_dirs.append(str(templates_dir))
    
    return template_dirs


# Create Jinja2 environment with multiple template directories
template_dirs = discover_template_directories()
loader = ChoiceLoader([FileSystemLoader(d) for d in template_dirs])

templates = Jinja2Templates(directory=template_dirs[0])
templates.env.loader = loader

# Global template variables
templates.env.globals["settings"] = settings
