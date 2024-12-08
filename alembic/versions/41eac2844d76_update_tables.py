"""Update tables

Revision ID: 41eac2844d76
Revises: b60d344b03ad
Create Date: 2024-12-06 09:20:03.851436

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '41eac2844d76'
down_revision: Union[str, None] = 'b60d344b03ad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('login', sa.String(), nullable=True),
    sa.Column('pas', sa.String(), nullable=True),
    sa.Column('office', sa.String(), nullable=True),
    sa.Column('birthdate', sa.DateTime(), nullable=True),
    sa.Column('role', sa.String(), nullable=True),
    sa.Column('refresh_token', sa.String(), nullable=True),
    sa.Column('last_login', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_login'), 'users', ['login'], unique=True)
    op.create_index(op.f('ix_users_name'), 'users', ['name'], unique=False)
    op.create_table('messages',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('message_time', sa.DateTime(), nullable=False),
    sa.Column('message', sa.String(), nullable=False),
    sa.Column('message_sender', sa.Integer(), nullable=False),
    sa.Column('message_receiver', sa.Integer(), nullable=False),
    sa.Column('message_status', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['message_receiver'], ['users.id'], ),
    sa.ForeignKeyConstraint(['message_sender'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_messages_id'), 'messages', ['id'], unique=False)
    op.create_table('notifications',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('notification_time', sa.DateTime(), nullable=False),
    sa.Column('notification', sa.String(), nullable=False),
    sa.Column('notification_sender', sa.Integer(), nullable=False),
    sa.Column('notification_receiver', sa.Integer(), nullable=False),
    sa.Column('notification_status', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['notification_receiver'], ['users.id'], ),
    sa.ForeignKeyConstraint(['notification_sender'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_id'), 'notifications', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_notifications_id'), table_name='notifications')
    op.drop_table('notifications')
    op.drop_index(op.f('ix_messages_id'), table_name='messages')
    op.drop_table('messages')
    op.drop_index(op.f('ix_users_name'), table_name='users')
    op.drop_index(op.f('ix_users_login'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
    # ### end Alembic commands ###
