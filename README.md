# SaaS Boilerplate

A modern SaaS boilerplate built with FastAPI, HTMX, and Shoelace.

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy (async), Pydantic
- **Frontend**: HTMX, [Shoelace](https://shoelace.style/) Web Components
- **Templating**: Jinja2
- **Database**: PostgreSQL 17 (via Docker)
- **Auth**: JWT-based authentication
- **Task Runner**: [Just](https://github.com/casey/just)

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [Docker](https://www.docker.com/) (for PostgreSQL)
- [just](https://github.com/casey/just) (optional, for task running)

> [!NOTE]
> the project uses [Testcontainers](https://testcontainers.com/) for testing. Running tests requires a local Docker daemon (e.g., Docker Desktop, OrbStack, or colima) to be running. Tests will automatically spin up an isolated PostgreSQL container.

## Getting Started

### 1. Install Dependencies

```bash
uv sync
```

### 2. Set Up Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Start PostgreSQL

```bash
just db-start
# or: docker compose up -d db
```

### 4. Run Database Migrations

```bash
just db-upgrade
# or: uv run alembic upgrade head
```

### 5. Run Development Server

```bash
just runserver
# or: uv run uvicorn app.main:app --reload --port 8000
```

### 6. Open in Browser

Visit [http://localhost:8000](http://localhost:8000)

## Project Structure

```
saas-boilerplate/
├── app/
│   ├── core/           # Config, database, templates, logging, exceptions
│   ├── common/         # Shared utilities (auth, base models, repositories)
│   │   └── auth/       # Authentication (JWT, password, dependencies)
│   ├── modules/        # Feature modules (domain-driven)
│   │   └── task/       # Task module (example feature)
│   ├── routers/        # API & web routes
│   ├── templates/      # Jinja2 templates
│   │   ├── base.html
│   │   ├── components/ # Reusable UI components
│   │   ├── pages/      # Full page templates
│   │   └── partials/   # HTMX partials
│   └── static/         # Static assets (CSS, JS)
├── migrations/         # Alembic database migrations
├── tests/              # Test suite
├── Justfile            # Task runner commands
└── pyproject.toml
```

## Available Commands

Run `just` to see all available commands:

| Command | Description |
|---------|-------------|
| `just runserver` | Run dev server with auto-reload |
| `just test` | Run tests |
| `just migrate "message"` | Create a new migration |
| `just db-upgrade` | Apply pending migrations |
| `just db-downgrade` | Rollback last migration |
| `just db-reset` | Reset database |
| `just db-start` | Start PostgreSQL container |
| `just db-stop` | Stop PostgreSQL container |
| `just db-shell` | Open PostgreSQL shell |
| `just fmt` | Format code with ruff |
| `just lint` | Lint code with ruff |
| `just clean` | Clean Python cache files |

## Architecture

The project follows a **modular architecture**:

- **Modules** (`app/modules/`): Self-contained feature modules with their own models, repositories, services, and routers
- **Common** (`app/common/`): Shared code including auth, base classes, and utils
- **Core** (`app/core/`): app config, db setup, and infrastructure
