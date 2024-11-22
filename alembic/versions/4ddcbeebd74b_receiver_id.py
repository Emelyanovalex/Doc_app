"""receiver_id

Revision ID: 4ddcbeebd74b
Revises: c4e6183210a1
Create Date: 2024-11-20 12:54:12.111406

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4ddcbeebd74b'
down_revision: Union[str, None] = 'c4e6183210a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('messages_message_reciver_id_fkey', 'messages', type_='foreignkey')
    op.drop_column('messages', 'message_reciver_id')
    op.drop_constraint('notifications_notification_reciver_id_fkey', 'notifications', type_='foreignkey')
    op.drop_column('notifications', 'notification_reciver_id')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('notifications', sa.Column('notification_reciver_id', sa.INTEGER(), autoincrement=False, nullable=False))
    op.create_foreign_key('notifications_notification_reciver_id_fkey', 'notifications', 'users', ['notification_reciver_id'], ['id'])
    op.add_column('messages', sa.Column('message_reciver_id', sa.INTEGER(), autoincrement=False, nullable=False))
    op.create_foreign_key('messages_message_reciver_id_fkey', 'messages', 'users', ['message_reciver_id'], ['id'])
    # ### end Alembic commands ###
