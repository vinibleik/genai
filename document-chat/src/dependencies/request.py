from typing import Annotated, NamedTuple

from fastapi import Depends, Query


class Pagination(NamedTuple):
    limit: int | None
    offset: int | None
    page: int | None


def get_pagination(
    limit: Annotated[int | None, Query(gt=0)] = None,
    page: Annotated[int | None, Query(ge=0)] = None,
) -> Pagination:
    offset = (page - 1) * limit if limit and page else None
    return Pagination(limit, offset, page)


PaginationDep = Annotated[Pagination, Depends(get_pagination)]
