from sqlmodel import SQLModel

from src.models.chat import Chat, ChatCreate, ChatRead
from src.models.message import Message, MessageCreate, MessageRead

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = SQLModel.metadata

metadata.naming_convention = NAMING_CONVENTION

__all__ = [
    "metadata",
    "Chat",
    "ChatCreate",
    "ChatRead",
    "Message",
    "MessageCreate",
    "MessageRead",
]
