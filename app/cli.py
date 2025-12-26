"""
CLI commands
"""
import asyncio
import typer
from app.core.config import settings

app = typer.Typer(help="Project CLI")


async def _create_superuser(email: str, password: str):
    """Async function to create superuser."""
    from app.core.database import AsyncSessionLocal
    from app.common.auth.repositories import UserRepository
    from app.common.auth.security import hash_password
    
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        
        existing = await user_repo.get_by_email(email)
        if existing:
            typer.secho(f"Error: User with email '{email}' already exists.", fg=typer.colors.RED)
            raise typer.Exit(1)
        
        user = await user_repo.create(
            email=email,
            hashed_password=hash_password(password),
            is_superuser=True,
            is_active=True,
            tenant_id=None,
        )
        await session.commit()
        
        typer.secho(f"Superuser created: {user.email}", fg=typer.colors.GREEN)


@app.command()
def createsuperuser(
    email: str = typer.Option(..., "--email", "-e", prompt="Email address"),
    password: str = typer.Option(
        ...,
        "--password",
        "-p",
        prompt="Password",
        confirmation_prompt=True,
        hide_input=True,
    ),
):
    """
    Create a superuser account.
    
    Superusers have full access to all platform features.
    """
    asyncio.run(_create_superuser(email, password))


# Add a placeholder command to force subcommand mode
@app.command()
def version():
    """Show the application version."""
    typer.echo(f"{settings.PROJECT_NAME} v{settings.VERSION}")


if __name__ == "__main__":
    app()
