"""history of adding\deleting users\history and blocking in direct

Revision ID: 41b385c282fe
Revises: 48b7c8a6b60c
Create Date: 2024-05-03 06:28:02.370115

"""
from typing import Sequence, Union
from sqlalchemy.ext.declarative import declarative_base
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Text, ForeignKey
from typing import List
import datetime
from sqlalchemy.dialects.postgresql import ARRAY
from db.models.chat import ChatTypes
Base = declarative_base()

# revision identifiers, used by Alembic.
revision: str = '41b385c282fe'
down_revision: Union[str, None] = '48b7c8a6b60c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


chat_users_association_table = sa.Table(
    "chat_users_association_table",
    Base.metadata,
    sa.Column("user_id", sa.ForeignKey("users.id"), primary_key=True),
    sa.Column("chat_id", sa.ForeignKey("chats.id"), primary_key=True),
)



class AddedDeletedUserHistory(Base):
    __tablename__ = 'added_deleted_user_history'
    added_dates: Mapped[List[datetime.datetime]] = mapped_column(ARRAY(DateTime), server_default='{}',
                                                                nullable=False)  # when user was added
    deleted_dates: Mapped[List[datetime.datetime]] = mapped_column(ARRAY(String), server_default='{}',
                                                                  nullable=True)  # when user was deleted
    user: Mapped["User"] = relationship()
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    chat: Mapped["GroupChat"] = relationship(back_populates='history_of_adding_deleting_users')
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id"), primary_key=True)


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    chats: Mapped[List["Chat"]] = relationship(back_populates='users', secondary=chat_users_association_table)


class Chat(Base):
    __tablename__ = 'chats'
    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[ChatTypes] = mapped_column(String(50), nullable=False)
    class_type: Mapped[str]
    date_of_creation: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    users: Mapped[List["User"]] = relationship(back_populates='chats', secondary=chat_users_association_table)
    __mapper_args__ = {
        "polymorphic_on": "class_type",
        "polymorphic_identity": "chats",
    }


class GroupChat(Chat):
    __mapper_args__ = {
        "polymorphic_identity": "group_chats",
    }
    history_of_adding_deleting_users: Mapped[List[AddedDeletedUserHistory]] = relationship(back_populates="chat")



def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('added_deleted_user_history',
    sa.Column('added_dates', ARRAY(sa.DateTime()), server_default='{}', nullable=True),
    sa.Column('deleted_dates', ARRAY(sa.String()), server_default='{}', nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('chat_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['chat_id'], ['chats.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('user_id', 'chat_id')
    )
    op.create_table('deleted_history',
    sa.Column('deleted_history', sa.DateTime(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('chat_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['chat_id'], ['chats.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('user_id', 'chat_id')
    )
    op.add_column('chats', sa.Column('blocked_by_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'chats', 'users', ['blocked_by_id'], ['id'])
    # ### end Alembic commands ###
    bind = op.get_bind()
    session = Session(bind=bind)
    chats = session.execute(select(GroupChat)).scalars().all()
    for chat in chats:
        for user in chat.users:
            history = AddedDeletedUserHistory(user=user, chat=chat, added_dates=[chat.date_of_creation])
            session.add(history)

    session.commit()
    op.alter_column('added_deleted_user_history', 'added_dates', nullable=False)


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'chats', type_='foreignkey')
    op.drop_column('chats', 'blocked_by_id')
    op.drop_table('deleted_history')
    op.drop_table('added_deleted_user_history')
    # ### end Alembic commands ###
