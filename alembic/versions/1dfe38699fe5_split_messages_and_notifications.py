"""Split messages and notifications

Revision ID: 1dfe38699fe5
Revises: 1fdeb3952dde
Create Date: 2024-11-20 09:41:13.581352

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '1dfe38699fe5'
down_revision: Union[str, None] = '1fdeb3952dde'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('messages',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('message_time', sa.DateTime(), nullable=False),
    sa.Column('message', sa.String(), nullable=False),
    sa.Column('message_sender', sa.Integer(), nullable=False),
    sa.Column('message_reciver', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['message_reciver'], ['users.id'], ),
    sa.ForeignKeyConstraint(['message_sender'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_messages_id'), 'messages', ['id'], unique=False)
    op.create_table('notifications',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('notification_time', sa.DateTime(), nullable=False),
    sa.Column('notification', sa.String(), nullable=False),
    sa.Column('notification_sender', sa.Integer(), nullable=False),
    sa.Column('notification_reciver', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['notification_reciver'], ['users.id'], ),
    sa.ForeignKeyConstraint(['notification_sender'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_id'), 'notifications', ['id'], unique=False)
    op.drop_index('ix_messages_notifications_id', table_name='messages_notifications')
    op.drop_table('messages_notifications')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('messages_notifications',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('content', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('is_read', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('type', postgresql.ENUM('MESSAGE', 'NOTIFICATION', name='recordtype'), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name='messages_notifications_pkey')
    )
    op.create_index('ix_messages_notifications_id', 'messages_notifications', ['id'], unique=False)
    op.drop_index(op.f('ix_notifications_id'), table_name='notifications')
    op.drop_table('notifications')
    op.drop_index(op.f('ix_messages_id'), table_name='messages')
    op.drop_table('messages')
    # ### end Alembic commands ###
