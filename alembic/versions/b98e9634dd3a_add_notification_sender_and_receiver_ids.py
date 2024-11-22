"""Add notification sender and receiver IDs

Revision ID: b98e9634dd3a
Revises: 1dfe38699fe5
Create Date: 2024-11-20 10:23:34.034265

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b98e9634dd3a'
down_revision: Union[str, None] = '1dfe38699fe5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('notifications', sa.Column('notification_sender_id', sa.Integer(), nullable=False))
    op.add_column('notifications', sa.Column('notification_reciver_id', sa.Integer(), nullable=False))
    op.drop_constraint('notifications_notification_reciver_fkey', 'notifications', type_='foreignkey')
    op.drop_constraint('notifications_notification_sender_fkey', 'notifications', type_='foreignkey')
    op.create_foreign_key(None, 'notifications', 'users', ['notification_reciver_id'], ['id'])
    op.create_foreign_key(None, 'notifications', 'users', ['notification_sender_id'], ['id'])
    op.drop_column('notifications', 'notification_reciver')
    op.drop_column('notifications', 'notification_sender')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('notifications', sa.Column('notification_sender', sa.INTEGER(), autoincrement=False, nullable=False))
    op.add_column('notifications', sa.Column('notification_reciver', sa.INTEGER(), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'notifications', type_='foreignkey')
    op.drop_constraint(None, 'notifications', type_='foreignkey')
    op.create_foreign_key('notifications_notification_sender_fkey', 'notifications', 'users', ['notification_sender'], ['id'])
    op.create_foreign_key('notifications_notification_reciver_fkey', 'notifications', 'users', ['notification_reciver'], ['id'])
    op.drop_column('notifications', 'notification_reciver_id')
    op.drop_column('notifications', 'notification_sender_id')
    # ### end Alembic commands ###
