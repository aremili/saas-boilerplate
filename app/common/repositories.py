"""Base repository class providing CRUD operations."""
from typing import Generic, TypeVar, Type, Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.common.models import Base
from app.core.logging import get_logger

ModelType = TypeVar("ModelType", bound=Base)

logger = get_logger(__name__)


class BaseRepository(Generic[ModelType]):
    """Generic repository providing common database operations."""
    
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get(self, id: int) -> Optional[ModelType]:
        logger.debug(f"Fetching {self.model.__name__} with id={id}")
        return await self.session.get(self.model, id)

    async def get_all(self) -> Sequence[ModelType]:
        logger.debug(f"Fetching all {self.model.__name__} records")
        result = await self.session.execute(select(self.model))
        return result.scalars().all()

    async def create(self, **kwargs) -> ModelType:
        logger.debug(f"Creating {self.model.__name__} with {kwargs}")
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        logger.info(f"Created {self.model.__name__} with id={instance.id}")
        return instance
    
    async def update(self, instance: ModelType, **kwargs) -> ModelType:
        logger.debug(f"Updating {self.model.__name__} id={instance.id} with {kwargs}")
        for key, value in kwargs.items():
            setattr(instance, key, value)
        await self.session.commit()
        await self.session.refresh(instance)
        logger.info(f"Updated {self.model.__name__} with id={instance.id}")
        return instance

    async def delete(self, instance: ModelType) -> None:
        instance_id = instance.id
        logger.debug(f"Deleting {self.model.__name__} with id={instance_id}")
        await self.session.delete(instance)
        await self.session.commit()
        logger.info(f"Deleted {self.model.__name__} with id={instance_id}")
