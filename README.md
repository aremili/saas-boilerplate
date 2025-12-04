# SaaS Boilerplate

A modern SaaS boilerplate built with FastAPI, HTMX, Stimulus.js, and Vite.

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy (async), Pydantic Settings
- **Frontend**: Vite, TailwindCSS, Stimulus.js, HTMX
- **Templating**: Jinja2

## Prerequisites

- Python 3.11+
- Node.js 18+
- [uv](https://docs.astral.sh/uv/) (Python package manager)

## Getting Started

### 1. Install Dependencies

```bash
# Backend
uv sync

# Frontend
cd frontend
npm install
cd ..
```

### 2. Run Development Servers

You need **two terminals** running simultaneously:

**Terminal 1 - Backend (FastAPI):**
```bash
uv run uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend (Vite):**
```bash
cd frontend
npm run dev
```

### 3. Open in Browser

Visit [http://localhost:8000](http://localhost:8000)

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
├── frontend/
│   ├── src/            # JS/CSS source files
│   └── vite.config.js
└── pyproject.toml
```

## Build for Production

```bash
cd frontend
npm run build
```

This outputs bundled assets to `app/static/`.
