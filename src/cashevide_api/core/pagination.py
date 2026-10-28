from typing import Generic, TypeVar

from fastapi import Request
from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

PAGE_SIZE = 10

T = TypeVar("T", bound=BaseModel)


class Page(BaseModel, Generic[T]):
    count: int
    next: str | None
    previous: str | None
    result: list[T]


def _page_url(request: Request, page: int | None) -> str:

    url = request.url

    scheme = request.headers.get("x-forwarded-proto")

    if scheme in ("http", "https"):
        url = url.replace(scheme=scheme)

    if page is None or page == 1:
        return str(url.remove_query_params("page"))

    return str(url.include_query_params(page=page))


async def paginate(
    db: AsyncSession, query: Select, request: Request, schema: type[T], page: int = 1
):
    pass
