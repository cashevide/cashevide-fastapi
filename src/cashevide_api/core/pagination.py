from typing import Generic, TypeVar

from fastapi import HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

PAGE_SIZE = 10

T = TypeVar("T", bound=BaseModel)


class Page(BaseModel, Generic[T]):
    count: int
    next: str | None
    previous: str | None
    results: list[T]


def _page_url(request: Request, page: int | None) -> str:

    url = request.url

    scheme = request.headers.get("x-forwarded-proto")

    if scheme in ("http", "https"):
        url = url.replace(scheme=scheme)

    if page is None or page == 1:
        return str(url.remove_query_params("page"))

    return str(url.include_query_params(page=page))


async def paginate(
    db: AsyncSession,
    query: Select,
    request: Request,
    schema: type[T],
    page: int = 1,
    page_size=PAGE_SIZE,
):
    count = await db.scalar(
        select(func.count()).select_from(query.order_by(None).subquery())
    )

    count = count or 0
    last_page = max(1, -(-count // page_size))

    if page < 1 or page > last_page:
        raise HTTPException(status_code=404, detail="Invalid page.")

    rows = await db.scalars(query.limit(page_size).offset((page - 1) * page_size))

    return Page[schema](  # type: ignore[valid-type]
        count=count,
        next=_page_url(request, page + 1) if page < last_page else None,
        previous=_page_url(request, page - 1) if page > 1 else None,
        results=[schema.model_validate(row) for row in rows],
    )
