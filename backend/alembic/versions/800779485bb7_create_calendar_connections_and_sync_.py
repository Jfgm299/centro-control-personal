"""create calendar connections and sync logs

Revision ID: 800779485bb7
Revises: 66a4e57d9c89
Create Date: 2026-03-07 16:43:08.644985

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '800779485bb7'
down_revision: Union[str, Sequence[str], None] = '66a4e57d9c89'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'calendar_connections',
        sa.Column('id',               sa.Integer(),               nullable=False),
        sa.Column('user_id',          sa.Integer(),               nullable=False),
        sa.Column('provider',         sa.String(20),              nullable=False),
        sa.Column('access_token',     sa.String(),                nullable=True),
        sa.Column('refresh_token',    sa.String(),                nullable=True),
        sa.Column('token_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('caldav_username',  sa.String(),                nullable=True),
        sa.Column('caldav_password',  sa.String(),                nullable=True),
        sa.Column('calendar_id',      sa.String(),                nullable=True),
        sa.Column('sync_events',      sa.Boolean(),               nullable=False, server_default='true'),
        sa.Column('sync_routines',    sa.Boolean(),               nullable=False, server_default='true'),
        sa.Column('sync_reminders',   sa.Boolean(),               nullable=False, server_default='false'),
        sa.Column('is_active',        sa.Boolean(),               nullable=False, server_default='true'),
        sa.Column('last_synced_at',   sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at',       sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['core.users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'provider', name='uq_user_provider'),
        schema='calendar_tracker',
    )
    op.create_index('ix_cc_id',      'calendar_connections', ['id'],      schema='calendar_tracker')
    op.create_index('ix_cc_user_id', 'calendar_connections', ['user_id'], schema='calendar_tracker')

    op.create_table(
        'sync_logs',
        sa.Column('id',              sa.Integer(),               nullable=False),
        sa.Column('connection_id',   sa.Integer(),               nullable=False),
        sa.Column('user_id',         sa.Integer(),               nullable=False),
        sa.Column('provider',        sa.String(20),              nullable=False),
        sa.Column('direction',       sa.String(10),              nullable=False),
        sa.Column('events_created',  sa.Integer(),               nullable=True, server_default='0'),
        sa.Column('events_updated',  sa.Integer(),               nullable=True, server_default='0'),
        sa.Column('events_deleted',  sa.Integer(),               nullable=True, server_default='0'),
        sa.Column('routines_synced', sa.Integer(),               nullable=True, server_default='0'),
        sa.Column('error',           sa.String(),                nullable=True),
        sa.Column('synced_at',       sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['connection_id'], ['calendar_tracker.calendar_connections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'],       ['core.users.id'],                            ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='calendar_tracker',
    )
    op.create_index('ix_sl_id',      'sync_logs', ['id'],      schema='calendar_tracker')
    op.create_index('ix_sl_user_id', 'sync_logs', ['user_id'], schema='calendar_tracker')


def downgrade() -> None:
    op.drop_index('ix_sl_user_id', 'sync_logs',            schema='calendar_tracker')
    op.drop_index('ix_sl_id',      'sync_logs',            schema='calendar_tracker')
    op.drop_table('sync_logs',                              schema='calendar_tracker')
    op.drop_index('ix_cc_user_id', 'calendar_connections', schema='calendar_tracker')
    op.drop_index('ix_cc_id',      'calendar_connections', schema='calendar_tracker')
    op.drop_table('calendar_connections',                   schema='calendar_tracker')
