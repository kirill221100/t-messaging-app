"""last time online

Revision ID: 4e323eda7bbd
Revises: a965e1263105
Create Date: 2024-04-17 10:25:13.939044

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import datetime


# revision identifiers, used by Alembic.
revision: str = '4e323eda7bbd'
down_revision: Union[str, None] = 'a965e1263105'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('last_time_online', sa.DateTime()))
    op.execute("UPDATE users SET last_time_online=timezone('utc', now())")
    op.alter_column('users', 'last_time_online', nullable=False)


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'last_time_online')
    # ### end Alembic commands ###
