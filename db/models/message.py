import datetime
from db.db_setup import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Text
from sqlalchemy.dialects.postgresql import ARRAY
from typing import List
from enum import Enum
from sqlalchemy import ForeignKey


class MessageTypes(Enum):
    TEXT = "TEXT"
    VOICE = "VOICE"
    STICKER = "STICKER"


class Message(Base):
    __tablename__ = 'messages'
    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(Text)
    pictures: Mapped[List[str]] = mapped_column(ARRAY(String), server_default='{}', nullable=True)  # <= 10
    videos: Mapped[List[str]] = mapped_column(ARRAY(String), server_default='{}', nullable=True)  # <= 10
    user: Mapped["User"] = relationship(back_populates='messages')
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    type: Mapped[MessageTypes] = mapped_column(String(50), nullable=False)
    date: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    chat: Mapped["Chat"] = relationship(back_populates='messages')
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id"))
    reply_on: Mapped["Message"] = relationship(back_populates='replied_messages', remote_side=id)
    reply_on_id: Mapped[int] = mapped_column(ForeignKey("messages.id"), nullable=True)
    replied_messages: Mapped[List["Message"]] = relationship()
