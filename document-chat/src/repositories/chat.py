import uuid

from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models.chat import Chat


class ChatRepository:
    session: AsyncSession

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def count(self) -> int:
        stmt = select(func.count()).select_from(Chat)
        r = await self.session.exec(stmt)
        return r.one()

    async def list_chats(
        self,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Chat]:
        stmt = (
            select(Chat).limit(limit).offset(offset).order_by(Chat.created_at)  # type: ignore
        )
        r = await self.session.exec(stmt)
        return list(r)

    async def create_chat(self, chat: Chat) -> Chat:
        self.session.add(chat)
        await self.session.commit()
        await self.session.refresh(chat)
        return chat

    async def get_chat(self, chat_id: uuid.UUID) -> Chat | None:
        return await self.session.get(Chat, chat_id)
