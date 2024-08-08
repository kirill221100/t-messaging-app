import datetime
from db.db_setup import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime
from typing import List
from enum import Enum
from sqlalchemy import ForeignKey
from db.models.assotiations import chat_users_association_table
from sqlalchemy.dialects.postgresql import ARRAY


class ChatTypes(Enum):
    DIRECT = 'DIRECT'
    GROUP = 'GROUP'


class Chat(Base):
    __tablename__ = 'chats'
    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[ChatTypes] = mapped_column(String(50), nullable=False)
    class_type: Mapped[str]
    date_of_creation: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    users: Mapped[List["User"]] = relationship(back_populates='chats', secondary=chat_users_association_table)
    messages: Mapped[List["Message"]] = relationship(back_populates='chat')
    who_deleted_history: Mapped[List["DeletedHistory"]] = relationship(back_populates="chat")
    read_dates: Mapped[List["ReadDate"]] = relationship(back_populates="chat")
    __mapper_args__ = {
        "polymorphic_on": "class_type",
        "polymorphic_identity": "chats",
    }


class DirectChat(Chat):
    __mapper_args__ = {
        "polymorphic_identity": "direct_chats",
    }
    blocked_by_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=True)
    blocked_by: Mapped["User"] = relationship(foreign_keys=[blocked_by_id])


class GroupChat(Chat):
    __mapper_args__ = {
        "polymorphic_identity": "group_chats",
    }
    name: Mapped[str] = mapped_column(nullable=True)
    avatar: Mapped[str] = mapped_column(nullable=True)
    creator_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=True)
    creator: Mapped["User"] = relationship(foreign_keys=[creator_id])
    history_of_adding_deleting_users: Mapped[List["AddedDeletedUserHistory"]] = relationship(back_populates="chat")
    who_left_chat: Mapped[List["LeftGroupChat"]] = relationship(back_populates="chat")


class AddedDeletedUserHistory(Base):
    __tablename__ = 'added_deleted_user_history'
    added_dates: Mapped[List[datetime.datetime]] = mapped_column(ARRAY(DateTime), server_default='{}',
                                                                nullable=False)  # when user was added
    deleted_dates: Mapped[List[datetime.datetime]] = mapped_column(ARRAY(DateTime), server_default='{}',
                                                                  nullable=True)  # when user was deleted
    user: Mapped["User"] = relationship()
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    chat: Mapped["GroupChat"] = relationship(back_populates='history_of_adding_deleting_users')
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id"), primary_key=True)


class DeletedHistory(Base):
    __tablename__ = 'deleted_history'
    date: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, nullable=False)  # when user deleted his chat's history
    user: Mapped["User"] = relationship()
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id"), primary_key=True)
    chat: Mapped["Chat"] = relationship(back_populates='who_deleted_history')


class ReadDate(Base):
    __tablename__ = 'read_date'
    date: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, nullable=False)  # last time user read messages in chat
    user: Mapped["User"] = relationship()
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id"), primary_key=True)
    chat: Mapped["Chat"] = relationship(back_populates='read_dates')


class LeftGroupChat(Base):
    __tablename__ = 'left_group_chat'
    leave_dates: Mapped[List[datetime.datetime]] = mapped_column(ARRAY(DateTime), server_default='{}',
                                                                 nullable=False)  # when user leaved
    return_dates: Mapped[List[datetime.datetime]] = mapped_column(ARRAY(DateTime), server_default='{}',
                                                                   nullable=True)  # when user returned
    user: Mapped["User"] = relationship()
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id"), primary_key=True)
    chat: Mapped["GroupChat"] = relationship(back_populates='who_left_chat')
