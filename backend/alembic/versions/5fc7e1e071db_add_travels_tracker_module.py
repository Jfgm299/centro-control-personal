"""add_travels_tracker_module

Revision ID: 5fc7e1e071db
Revises: bb7741351a08
Create Date: 2026-03-01
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers
revision: str = '5fc7e1e071db'
down_revision: Union[str, Sequence[str], None] = 'bb7741351a08'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # ── Schema ─────────────────────────────────────────────
    op.execute("CREATE SCHEMA IF NOT EXISTS travels_tracker")
    bind = op.get_bind()

    # ── Enums (create manually, disable auto-create) ───────
    photostatus_enum = postgresql.ENUM(
        'pending', 'uploaded', 'deleted',
        name='photostatus',
        schema='travels_tracker',
        create_type=False
    )

    activitycategory_enum = postgresql.ENUM(
        'sightseeing', 'food', 'transport',
        'accommodation', 'activity', 'other',
        name='activitycategory',
        schema='travels_tracker',
        create_type=False
    )

    photostatus_enum.create(bind, checkfirst=True)
    activitycategory_enum.create(bind, checkfirst=True)

    # ── trips ──────────────────────────────────────────────
    op.create_table(
        'trips',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('destination', sa.String(200), nullable=False),
        sa.Column('country_code', sa.String(3)),
        sa.Column('lat', sa.Float()),
        sa.Column('lon', sa.Float()),
        sa.Column('start_date', sa.Date()),
        sa.Column('end_date', sa.Date()),
        sa.Column('description', sa.Text()),
        sa.Column('cover_photo_key', sa.String(500)),
        sa.Column('cover_photo_url', sa.String(1000)),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(['user_id'], ['core.users.id'], ondelete='CASCADE'),
        schema='travels_tracker'
    )

    op.create_index(
        'ix_travels_tracker_trips_user_id',
        'trips',
        ['user_id'],
        schema='travels_tracker'
    )

    # ── albums ─────────────────────────────────────────────
    op.create_table(
        'albums',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('trip_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('cover_photo_key', sa.String(500)),
        sa.Column('cover_photo_url', sa.String(1000)),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(['trip_id'], ['travels_tracker.trips.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['core.users.id'], ondelete='CASCADE'),
        schema='travels_tracker'
    )

    op.create_index(
        'ix_travels_tracker_albums_trip_id',
        'albums',
        ['trip_id'],
        schema='travels_tracker'
    )

    op.create_index(
        'ix_travels_tracker_albums_user_id',
        'albums',
        ['user_id'],
        schema='travels_tracker'
    )

    # ── photos ─────────────────────────────────────────────
    op.create_table(
        'photos',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('album_id', sa.Integer(), nullable=False),
        sa.Column('trip_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('r2_key', sa.String(500), nullable=False),
        sa.Column('public_url', sa.String(1000)),
        sa.Column('content_type', sa.String(50)),
        sa.Column('size_bytes', sa.Integer()),
        sa.Column('width', sa.Integer()),
        sa.Column('height', sa.Integer()),
        sa.Column('caption', sa.String(500)),
        sa.Column('taken_at', sa.DateTime(timezone=True)),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('status', photostatus_enum, nullable=False),
        sa.Column('is_favorite', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(['album_id'], ['travels_tracker.albums.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['trip_id'], ['travels_tracker.trips.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['core.users.id'], ondelete='CASCADE'),
        schema='travels_tracker'
    )

    op.create_index('ix_travels_tracker_photos_album_id', 'photos',
                    ['album_id'], schema='travels_tracker')

    op.create_index('ix_travels_tracker_photos_trip_id', 'photos',
                    ['trip_id'], schema='travels_tracker')

    op.create_index('ix_travels_tracker_photos_user_id', 'photos',
                    ['user_id'], schema='travels_tracker')

    op.create_index('ix_travels_photos_trip_status', 'photos',
                    ['trip_id', 'status'], schema='travels_tracker')

    op.create_index('ix_travels_photos_favorites', 'photos',
                    ['user_id', 'is_favorite'], schema='travels_tracker')

    # ── activities ─────────────────────────────────────────
    op.create_table(
        'activities',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('trip_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('category', activitycategory_enum),
        sa.Column('description', sa.Text()),
        sa.Column('date', sa.Date()),
        sa.Column('lat', sa.Float()),
        sa.Column('lon', sa.Float()),
        sa.Column('rating', sa.Integer()),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['trip_id'], ['travels_tracker.trips.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['core.users.id'], ondelete='CASCADE'),
        schema='travels_tracker'
    )

    op.create_index('ix_travels_tracker_activities_trip_id',
                    'activities', ['trip_id'], schema='travels_tracker')

    op.create_index('ix_travels_tracker_activities_user_id',
                    'activities', ['user_id'], schema='travels_tracker')


def downgrade() -> None:

    bind = op.get_bind()

    op.drop_table('activities', schema='travels_tracker')
    op.drop_table('photos', schema='travels_tracker')
    op.drop_table('albums', schema='travels_tracker')
    op.drop_table('trips', schema='travels_tracker')

    postgresql.ENUM(
        name='activitycategory',
        schema='travels_tracker'
    ).drop(bind, checkfirst=True)

    postgresql.ENUM(
        name='photostatus',
        schema='travels_tracker'
    ).drop(bind, checkfirst=True)

    op.execute("DROP SCHEMA IF EXISTS travels_tracker CASCADE")