from sqlalchemy import Column
from sqlalchemy import Table
from sqlalchemy import ForeignKey
from db.db_setup import Base


chat_users_association_table = Table(
    "chat_users_association_table",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("chat_id", ForeignKey("chats.id"), primary_key=True),
)