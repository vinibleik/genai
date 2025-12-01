from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends

from src.dependencies.session import SessionDep
from src.repositories import ChatRepository, MessageRepository


async def get_chat_repository(
    session: SessionDep,
) -> AsyncGenerator[ChatRepository]:
    yield ChatRepository(session)


async def get_message_repository(
    session: SessionDep,
) -> AsyncGenerator[MessageRepository]:
    yield MessageRepository(session)


ChatRepositoryDep = Annotated[ChatRepository, Depends(get_chat_repository)]
MessageRepositoryDep = Annotated[
    MessageRepository, Depends(get_message_repository)
]
