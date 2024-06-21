import datetime
from db.db_setup import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Text
from sqlalchemy.dialects.postgresql import ARRAY
from typing import List
from enum import Enum
from sqlalchemy import ForeignKey


class MessageTypes(Enum):
    DEFAULT = 'DEFAULT'
    INFO = 'INFO'


class InfoMessageTypes(Enum):
    CHANGE_NAME = 'change_name'
    CHANGE_AVATAR = 'change_avatar'
    ADD_USERS = 'add_users'
    DELETE_USERS = 'delete_users'
    NEW_CHAT = 'new_chat'
    LEFT_CHAT = 'left_chat'
    RETURN_TO_CHAT = 'return_to_chat'


class Message(Base):
    __tablename__ = 'messages'
    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates='messages', foreign_keys=[user_id])
    date: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    chat: Mapped["Chat"] = relationship(back_populates='messages')
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id"))
    type: Mapped[MessageTypes] = mapped_column(String(50), nullable=False)
    class_type: Mapped[str]
    __mapper_args__ = {
        "polymorphic_on": "class_type",
        "polymorphic_identity": "messages",
    }


class DefaultMessage(Message):
    last_time_edited: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=True)
    photos: Mapped[List[str]] = mapped_column(ARRAY(String), server_default='{}', nullable=True)  # <= 10
    videos: Mapped[List[str]] = mapped_column(ARRAY(String), server_default='{}', nullable=True)  # <= 10
    reply_on: Mapped["DefaultMessage"] = relationship(back_populates='replied_messages', remote_side='DefaultMessage.id')
    reply_on_id: Mapped[int] = mapped_column(ForeignKey("messages.id", ondelete="SET NULL"), nullable=True)
    replied_messages: Mapped[List["DefaultMessage"]] = relationship()
    __mapper_args__ = {
        "polymorphic_identity": "default_messages",
    }


class InfoMessage(Message):
    __mapper_args__ = {
        "polymorphic_identity": "info_messages"
    }
    info_type: Mapped[InfoMessageTypes] = mapped_column(String(50), nullable=True)
    new_name: Mapped[str] = mapped_column(nullable=True)
    new_avatar: Mapped[str] = mapped_column(nullable=True)
    new_users: Mapped[List["User"]] = relationship(uselist=True, lazy='selectin')
    deleted_users: Mapped[List["User"]] = relationship(uselist=True, lazy='selectin')

