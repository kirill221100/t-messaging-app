from db.db_setup import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime
from typing import List
from db.models.assotiations import chat_users_association_table
import datetime


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True, nullable=False)
    avatar: Mapped[str] = mapped_column(nullable=True)
    description: Mapped[str] = mapped_column(nullable=True)
    email: Mapped[str] = mapped_column()
    chats: Mapped[List["Chat"]] = relationship(back_populates='users', secondary=chat_users_association_table)
    messages: Mapped[List["Message"]] = relationship(back_populates='user')
    last_time_online: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    deleted_chat_history: Mapped[List["DeletedHistory"]] = relationship()
