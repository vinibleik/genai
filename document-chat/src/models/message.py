import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any, Literal, TypedDict

from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlmodel import Column, Field, ForeignKey, SQLModel, Text, func, text

from src.utils import now_utc


class MessageRole(StrEnum):
    USER = "user"
    AI = "assistant"


class Usage(TypedDict):
    input_tokens: int
    output_tokens: int


class TextContent(TypedDict):
    type: Literal["text"]
    text: str


class ToolResponseContent(TypedDict):
    type: Literal["tool_response"]
    tool_call_id: str
    content: str
    tool_name: str


class ToolCallContent(TypedDict):
    type: Literal["tool_call"]
    tool_call_id: str
    tool_name: str
    args: str | dict[str, Any]


MessageContent = TextContent | ToolResponseContent | ToolCallContent


class MessageBase(SQLModel):
    chat_id: uuid.UUID = Field(
        sa_column=Column(
            "chat_id",
            ForeignKey("chat.id", onupdate="CASCADE", ondelete="CASCADE"),
            nullable=False,
        )
    )
    role: MessageRole
    content: list[MessageContent] = Field(
        sa_column=Column(
            JSONB,
            nullable=False,
        )
    )
    created_at: datetime = Field(
        default_factory=now_utc,
        sa_column=Column(
            TIMESTAMP(True, 6),
            nullable=False,
            server_default=func.current_timestamp(),
        ),
    )
    system: str | None = Field(default=None, sa_type=Text, nullable=True)
    usage: Usage | None = Field(default=None, sa_type=JSONB, nullable=True)
    model: str | None = Field(default=None, sa_type=Text, nullable=True)

    @property
    def text(self) -> str:
        return "\n".join(c["text"] for c in self.content if c["type"] == "text")

    def has_tool_call(self) -> bool:
        return any(c["type"] == "tool_call" for c in self.content)

    def get_tool_response(self) -> list[ToolResponseContent]:
        return [c for c in self.content if c["type"] == "tool_response"]

    def has_tool_response(self) -> bool:
        return any(c["type"] == "tool_response" for c in self.content)

    def get_tool_calls(self) -> list[ToolCallContent]:
        return [c for c in self.content if c["type"] == "tool_call"]


class Message(MessageBase, table=True):
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )


class MessageCreate(SQLModel):
    message: str


class MessageRead(SQLModel):
    id: uuid.UUID
    chat_id: uuid.UUID
    role: MessageRole
    content: list[MessageContent]
    created_at: datetime
