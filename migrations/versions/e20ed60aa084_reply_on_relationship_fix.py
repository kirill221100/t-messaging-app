"""reply on relationship fix

Revision ID: e20ed60aa084
Revises: 8fbbdf54271c
Create Date: 2024-04-01 17:26:47.034951

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e20ed60aa084'
down_revision: Union[str, None] = '8fbbdf54271c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
