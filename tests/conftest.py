import asyncio
from typing import AsyncGenerator, Generator
import pytest
import pytest_asyncio
from fastapi import APIRouter, Depends
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import create_app
from app.core.database import get_db
from app.common.models import Base
from app.common.auth.models import User, Role, Permission
from app.common.auth.security import hash_password
from app.common.auth.dependencies import require_role, require_permission


from testcontainers.postgres import PostgresContainer


# --- Test Routes ---
test_deps_router = APIRouter(prefix="/test-deps", tags=["test"])


@test_deps_router.get("/editor-only")
async def editor_only_route(user: User = Depends(require_role(["editor"]))):
    return {"email": user.email}


@test_deps_router.get("/admin-only")
async def admin_only_route(user: User = Depends(require_role(["admin"]))):
    return {"email": user.email}


@test_deps_router.get("/content-edit")
async def content_edit_route(user: User = Depends(require_permission("content:edit"))):
    return {"email": user.email}


@test_deps_router.get("/tasks-write")
async def tasks_write_route(user: User = Depends(require_permission("tasks:write"))):
    return {"email": user.email}


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer, None, None]:
    """Start a PostgreSQL container for the test session."""
    with PostgresContainer("postgres:17", driver="asyncpg") as postgres:
        yield postgres


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_engine(postgres_container: PostgresContainer):
    """Create a test database engine using the container."""
    database_url = postgres_container.get_connection_url()

    engine = create_async_engine(database_url, echo=False, poolclass=NullPool)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session_maker = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(db_engine) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client with database override."""
    # Create test app
    test_app = create_app(init_database=False, include_static=False)

    # Include test routes
    test_app.include_router(test_deps_router)

    # Create session factory for this test
    async_session_maker = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db():
        async with async_session_maker() as session:
            yield session

    test_app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# --- Test Data Fixtures ---


@pytest_asyncio.fixture
async def test_permission(db_session: AsyncSession) -> Permission:
    """Create a test permission."""
    permission = Permission(codename="tests:read", description="Test permission")
    db_session.add(permission)
    await db_session.commit()
    await db_session.refresh(permission)
    return permission


@pytest_asyncio.fixture
async def test_role(db_session: AsyncSession, test_permission: Permission) -> Role:
    """Create a test role with a permission."""
    role = Role(name="tester", description="Test role")
    role.permissions.append(test_permission)
    db_session.add(role)
    await db_session.commit()
    await db_session.refresh(role)
    return role


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user without roles."""
    user = User(
        email="test@example.com",
        hashed_password=hash_password("testpassword123"),
        is_active=True,
        is_superuser=False,
        tenant_id=1,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user, ["roles"])
    return user


@pytest_asyncio.fixture
async def test_user_with_role(db_session: AsyncSession, test_role: Role) -> User:
    """Create a test user with a role."""
    user = User(
        email="roleuser@example.com",
        hashed_password=hash_password("testpassword123"),
        is_active=True,
        is_superuser=False,
    )
    user.roles.append(test_role)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user, ["roles"])
    for role in user.roles:
        await db_session.refresh(role, ["permissions"])
    return user


@pytest_asyncio.fixture
async def superuser(db_session: AsyncSession) -> User:
    """Create a superuser."""
    user = User(
        email="super@example.com",
        hashed_password=hash_password("superpassword123"),
        is_active=True,
        is_superuser=True,
        tenant_id=None,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user, ["roles"])
    return user


@pytest_asyncio.fixture
async def inactive_user(db_session: AsyncSession) -> User:
    """Create an inactive user."""
    user = User(
        email="inactive@example.com",
        hashed_password=hash_password("testpassword123"),
        is_active=False,
        is_superuser=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user
