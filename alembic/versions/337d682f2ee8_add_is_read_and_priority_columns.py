"""Add is_read and priority columns

Revision ID: 337d682f2ee8
Revises: fe15ebc6a054
Create Date: 2024-11-20 15:00:04.948202

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '337d682f2ee8'
down_revision: Union[str, None] = 'fe15ebc6a054'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('messages', sa.Column('priority', sa.String(), nullable=True))
    op.add_column('notifications', sa.Column('is_read', sa.Boolean(), nullable=True))
    op.add_column('notifications', sa.Column('priority', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('notifications', 'priority')
    op.drop_column('notifications', 'is_read')
    op.drop_column('messages', 'priority')
    # ### end Alembic commands ###
