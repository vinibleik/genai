from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core import session_maker


async def get_session() -> AsyncGenerator[AsyncSession]:
    async with session_maker() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]
