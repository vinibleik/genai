import uuid
from datetime import datetime

from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlmodel import VARCHAR, Column, Field, SQLModel, func, text

from src.utils import now_utc


class ChatBase(SQLModel):
    name: str = Field(sa_type=VARCHAR(255))
    created_at: datetime = Field(
        default_factory=now_utc,
        sa_column=Column(
            TIMESTAMP(True, 6),
            nullable=False,
            server_default=func.current_timestamp(),
        ),
    )


class Chat(ChatBase, table=True):
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        sa_column_kwargs={"server_default": text("gen_random_uuid()")},
    )


class ChatCreate(ChatBase): ...


class ChatRead(ChatBase):
    id: uuid.UUID
