"""
Pytest configuration and fixtures for the SaaS boilerplate tests.
"""

import asyncio
from typing import AsyncGenerator, Generator
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.core.database import get_db
from app.common.models import Base
from app.common.auth.models import User, Role, Permission
from app.common.auth.security import hash_password


from testcontainers.postgres import PostgresContainer

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
    # Use the container's connection string
    # driver="asyncpg" in PostgresContainer handles the driver part
    database_url = postgres_container.get_connection_url()
    
    engine = create_async_engine(database_url, echo=False, poolclass=NullPool)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database schema created")

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print("Database schema dropped")

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
    # Create session factory for this test
    async_session_maker = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db():
        async with async_session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


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
    # Refresh with roles and nested permissions
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
