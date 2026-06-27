"""Shared Pydantic schemas reusable across all modules."""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response. Reusable across all list endpoints."""
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
