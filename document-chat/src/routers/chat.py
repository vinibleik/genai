import uuid

from fastapi import APIRouter, HTTPException

from src.agents.chatbot import ChatbotDeps, run_agent
from src.agents.processor import processor
from src.core import settings
from src.dependencies import (
    ChatRepositoryDep,
    MessageRepositoryDep,
    PaginationDep,
)
from src.models.chat import Chat, ChatCreate, ChatRead
from src.models.message import Message, MessageCreate, MessageRead

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/", response_model=list[ChatRead])
async def list_chats(
    repo: ChatRepositoryDep,
    pagination: PaginationDep,
) -> list[Chat]:
    return await repo.list_chats(pagination.limit, pagination.offset)


@router.post("/", response_model=ChatRead)
async def create_chat(body: ChatCreate, repo: ChatRepositoryDep) -> Chat:
    chat = Chat.model_validate(body)
    return await repo.create_chat(chat)


@router.get("/{chat_id}", response_model=ChatRead)
async def get_chat(chat_id: uuid.UUID, repo: ChatRepositoryDep) -> Chat:
    chat = await repo.get_chat(chat_id)
    if not chat:
        raise HTTPException(
            status_code=404, detail=f"Chat {chat_id} not found."
        )
    return chat


@router.get(
    "/{chat_id}/messages",
    response_model=list[MessageRead],
    response_model_exclude_none=True,
    response_model_exclude={"system", "usage", "model"},
)
async def list_chat_messages(
    chat_id: uuid.UUID, repo: MessageRepositoryDep, pagination: PaginationDep
) -> list[Message]:
    return await repo.list_messages(
        chat_id, pagination.limit, pagination.offset
    )


@router.post(
    "/{chat_id}/messages",
    response_model=list[MessageRead],
    response_model_exclude_none=True,
    response_model_exclude={"system", "usage", "model"},
)
async def create_message(
    chat_id: uuid.UUID,
    body: MessageCreate,
    chat_repo: ChatRepositoryDep,
    messages_repo: MessageRepositoryDep,
) -> list[Message]:
    chat = await chat_repo.get_chat(chat_id)
    if not chat:
        raise HTTPException(
            status_code=404, detail=f"Chat {chat_id} not found."
        )
    message_history_db = await messages_repo.list_messages(chat_id, None, None)
    message_history_agent = processor.process_messages_from_db(
        message_history_db
    )
    deps = ChatbotDeps(n=settings.SECRET_NUMBER)
    response_messages_agent = await run_agent(
        body.message, deps, message_history_agent
    )
    response_message_history = processor.process_messages_to_db(
        chat_id, response_messages_agent
    )
    return await messages_repo.create_messages(response_message_history)
