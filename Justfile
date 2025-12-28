# See https://github.com/casey/just for installation

# Default command: show available recipes
default:
    @just --list

# --- Development ---

start:
    just db-start
    just runserver

# Run the development server with auto-reload
runserver:
    uv run uvicorn app.main:app --reload --port 8000

# --- Database & Migrations ---

create-superuser:
    uv run python -m app.cli createsuperuser

# Create a new migration (autogenerate from models)
migrate message:
    uv run alembic revision --autogenerate -m "{{message}}"

# Apply all pending migrations
db-upgrade:
    uv run alembic upgrade head

# Rollback the last migration
db-downgrade:
    uv run alembic downgrade -1

# Show migration history
db-history:
    uv run alembic history

# Reset database (rollback all + upgrade)
db-reset:
    uv run alembic downgrade base
    uv run alembic upgrade head

# --- Dependencies ---

# Install/sync dependencies
install:
    uv sync

# Add a new dependency
add package:
    uv add {{package}}

# Add a dev dependency
add-dev package:
    uv add --dev {{package}}

# --- Testing ---

# Run tests
test:
    uv run pytest -n auto -vv

# Run tests with coverage
test-cov:
    uv run pytest -n auto --cov=app --cov-report=term-missing

# --- Code Quality ---

# Format code with ruff
format:
    uv run ruff format .

# Lint code with ruff
lint:
    uv run ruff check .

# Lint and fix
lint-fix:
    uv run ruff check --fix .

# Type check with mypy
typecheck:
    uv run ty check

# Run all checks (lint + typecheck)
check: lint typecheck

# --- Production ---

# Run production server (no reload)
run-prod:
    uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

# --- Utilities ---

# Start PostgreSQL container
db-start:
    docker compose up -d db

# Stop PostgreSQL container
db-stop:
    docker compose down

# Open PostgreSQL shell
db-shell:
    docker compose exec db psql -U saas -d saas_db

# View PostgreSQL logs
db-logs:
    docker compose logs -f db
