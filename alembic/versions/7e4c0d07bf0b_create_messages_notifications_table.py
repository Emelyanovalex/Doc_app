"""Create messages_notifications table

Revision ID: 7e4c0d07bf0b
Revises: bc8fc1bdf1d3
Create Date: 2024-11-19 18:30:26.249897

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7e4c0d07bf0b'
down_revision: Union[str, None] = 'bc8fc1bdf1d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('messages_notifications', sa.Column('type', sa.Enum('MESSAGE', 'NOTIFICATION', name='recordtype'), nullable=False))
    op.drop_column('messages_notifications', 'is_notification')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('messages_notifications', sa.Column('is_notification', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.drop_column('messages_notifications', 'type')
    # ### end Alembic commands ###
