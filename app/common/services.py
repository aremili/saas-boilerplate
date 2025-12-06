"""Base service class providing common service operations."""
from typing import Generic, TypeVar
from app.common.repositories import BaseRepository

RepoType = TypeVar("RepoType", bound=BaseRepository)


class BaseService(Generic[RepoType]):
    """Base service class that wraps a repository."""
    
    def __init__(self, repository: RepoType):
        self.repository = repository
