(outdated)

# SaaS Boilerplate

A modern SaaS boilerplate built with FastAPI, HTMX, and Shoelace.

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy (async), Pydantic
- **Frontend**: HTMX, Shoelace
- **Templating**: Jinja2

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (Python package manager)

## Getting Started

### 1. Install Dependencies

```bash
# Backend
uv sync
```

### 2. Run Development Servers


```bash
uv run uvicorn app.main:app --reload --port 8000
```


### 3. Open in Browser

Visit [development server](http://localhost:8000)

## Project Structure

```
saas_boilerplate/
├── app/
│   ├── core/           # Config, database, templates
│   ├── models/         # SQLAlchemy models
│   ├── repositories/   # Data access layer
│   ├── services/       # Business logic
│   ├── routers/        # API & web routes
│   └── templates/      # Jinja2 templates
└── pyproject.toml
```
