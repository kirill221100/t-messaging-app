"""empty message

Revision ID: a965e1263105
Revises: 8079c3ff7f13, f93236bdfc6a
Create Date: 2024-04-17 06:43:04.491267

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a965e1263105'
down_revision: Union[str, None] = ('8079c3ff7f13', 'f93236bdfc6a')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
