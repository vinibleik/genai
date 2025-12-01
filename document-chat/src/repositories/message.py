import asyncio
import uuid

from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.message import Message


class MessageRepository:
    session: AsyncSession

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def count(self) -> int:
        stmt = select(func.count()).select_from(Message)
        r = await self.session.exec(stmt)
        return r.one()

    async def list_messages(
        self,
        chat_id: uuid.UUID,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Message]:
        stmt = (
            select(Message)
            .where(Message.chat_id == chat_id)
            .limit(limit)
            .offset(offset)
            .order_by(Message.created_at)  # type: ignore
        )
        r = await self.session.exec(stmt)
        return list(r)

    async def create_message(self, message: Message) -> Message:
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)
        return message

    async def create_messages(self, messages: list[Message]) -> list[Message]:
        self.session.add_all(messages)
        await self.session.commit()
        await asyncio.gather(*[self.session.refresh(m) for m in messages])
        return messages

    async def get_message(self, message_id: uuid.UUID) -> Message | None:
        return await self.session.get(Message, message_id)
