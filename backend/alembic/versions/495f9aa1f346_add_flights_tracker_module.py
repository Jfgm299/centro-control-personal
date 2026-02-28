"""add_flights_tracker_module

Revision ID: 495f9aa1f346
Revises: 859a005d0d9c
Create Date: 2026-02-27 22:56:51.336496

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '495f9aa1f346'
down_revision: Union[str, Sequence[str], None] = '859a005d0d9c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('flights',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('flight_number', sa.String(length=10), nullable=False),
    sa.Column('flight_date', sa.Date(), nullable=False),
    sa.Column('status', sa.Enum(
        'expected', 'check_in', 'boarding', 'gate_closed', 'departed',
        'en_route', 'approaching', 'delayed', 'arrived', 'canceled',
        'diverted', 'canceled_uncertain', 'unknown',
        name='flightstatus', schema='flights_tracker'
    ), nullable=False),
    sa.Column('origin_iata', sa.String(length=4), nullable=False),
    sa.Column('origin_icao', sa.String(length=5), nullable=True),
    sa.Column('origin_name', sa.String(length=200), nullable=True),
    sa.Column('origin_city', sa.String(length=100), nullable=True),
    sa.Column('origin_country_code', sa.String(length=3), nullable=True),
    sa.Column('origin_timezone', sa.String(length=50), nullable=True),
    sa.Column('origin_lat', sa.Float(), nullable=True),
    sa.Column('origin_lon', sa.Float(), nullable=True),
    sa.Column('destination_iata', sa.String(length=4), nullable=False),
    sa.Column('destination_icao', sa.String(length=5), nullable=True),
    sa.Column('destination_name', sa.String(length=200), nullable=True),
    sa.Column('destination_city', sa.String(length=100), nullable=True),
    sa.Column('destination_country_code', sa.String(length=3), nullable=True),
    sa.Column('destination_timezone', sa.String(length=50), nullable=True),
    sa.Column('destination_lat', sa.Float(), nullable=True),
    sa.Column('destination_lon', sa.Float(), nullable=True),
    sa.Column('airline_iata', sa.String(length=3), nullable=True),
    sa.Column('airline_icao', sa.String(length=4), nullable=True),
    sa.Column('airline_name', sa.String(length=100), nullable=True),
    sa.Column('scheduled_departure', sa.DateTime(timezone=True), nullable=True),
    sa.Column('revised_departure', sa.DateTime(timezone=True), nullable=True),
    sa.Column('predicted_departure', sa.DateTime(timezone=True), nullable=True),
    sa.Column('actual_departure', sa.DateTime(timezone=True), nullable=True),
    sa.Column('scheduled_arrival', sa.DateTime(timezone=True), nullable=True),
    sa.Column('revised_arrival', sa.DateTime(timezone=True), nullable=True),
    sa.Column('predicted_arrival', sa.DateTime(timezone=True), nullable=True),
    sa.Column('actual_arrival', sa.DateTime(timezone=True), nullable=True),
    sa.Column('duration_minutes', sa.Integer(), nullable=True),
    sa.Column('delay_departure_minutes', sa.Integer(), nullable=True),
    sa.Column('delay_arrival_minutes', sa.Integer(), nullable=True),
    sa.Column('distance_km', sa.Float(), nullable=True),
    sa.Column('aircraft_model', sa.String(length=100), nullable=True),
    sa.Column('aircraft_registration', sa.String(length=20), nullable=True),
    sa.Column('aircraft_icao24', sa.String(length=10), nullable=True),
    sa.Column('terminal_origin', sa.String(length=10), nullable=True),
    sa.Column('gate_origin', sa.String(length=10), nullable=True),
    sa.Column('terminal_destination', sa.String(length=10), nullable=True),
    sa.Column('baggage_belt', sa.String(length=10), nullable=True),
    sa.Column('runway_origin', sa.String(length=10), nullable=True),
    sa.Column('runway_destination', sa.String(length=10), nullable=True),
    sa.Column('data_quality', sa.String(length=50), nullable=True),
    sa.Column('is_past', sa.Boolean(), nullable=False),
    sa.Column('is_diverted', sa.Boolean(), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('last_refreshed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['core.users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'flight_number', 'flight_date'),
    schema='flights_tracker'
    )
    op.create_index('ix_flights_user_date', 'flights', ['user_id', 'flight_date'], unique=False, schema='flights_tracker')
    op.create_index('ix_flights_user_past', 'flights', ['user_id', 'is_past'], unique=False, schema='flights_tracker')


def downgrade() -> None:
    op.drop_index('ix_flights_user_past', table_name='flights', schema='flights_tracker')
    op.drop_index('ix_flights_user_date', table_name='flights', schema='flights_tracker')
    op.drop_table('flights', schema='flights_tracker')
    op.execute("DROP TYPE IF EXISTS flights_tracker.flightstatus")