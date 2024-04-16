from db.db_setup import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List
from db.models.assotiations import chat_users_association_table


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=True)
    surname: Mapped[str] = mapped_column(nullable=True)
    username: Mapped[str] = mapped_column(unique=True, nullable=True)
    email: Mapped[str] = mapped_column()
    chats: Mapped[List["Chat"]] = relationship(back_populates='users', secondary=chat_users_association_table)
    messages: Mapped[List["Message"]] = relationship(back_populates='user')
