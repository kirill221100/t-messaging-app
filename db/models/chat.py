import datetime
from db.db_setup import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime
from typing import List
from enum import Enum
from sqlalchemy import ForeignKey
from db.models.assotiations import chat_users_association_table


class ChatTypes(Enum):
    DIRECT = 'DIRECT'
    GROUP = 'GROUP'


class Chat(Base):
    __tablename__ = 'chats'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=True)
    creator: Mapped["User"] = relationship()
    creator_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=True)
    users: Mapped[List["User"]] = relationship(back_populates='chats', secondary=chat_users_association_table)
    type: Mapped[ChatTypes] = mapped_column(String(50), nullable=False)
    date_of_creation: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    messages: Mapped[List["Message"]] = relationship(back_populates='chat')