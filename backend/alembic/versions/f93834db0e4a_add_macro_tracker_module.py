"""add_macro_tracker_module

Revision ID: f93834db0e4a
Revises: 495f9aa1f346
Create Date: 2026-02-28 23:46:24.263072

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f93834db0e4a'
down_revision: Union[str, Sequence[str], None] = '495f9aa1f346'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Enum MealType
    mealtype_enum = sa.Enum(
    "breakfast",
    "morning_snack",
    "lunch",
    "afternoon_snack",
    "dinner",
    "other",
    name="mealtype",
    schema="macro_tracker",
    create_type=False,  # 👈 ESTA LÍNEA ES LA CLAVE
)
    #mealtype_enum.create(op.get_bind(), checkfirst=True)

    # 2. Tabla products (catálogo global, sin user_id)
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("barcode", sa.String(30), nullable=True),
        sa.Column("product_name", sa.String(200), nullable=False),
        sa.Column("brand", sa.String(100), nullable=True),
        sa.Column("serving_size_text", sa.String(50), nullable=True),
        sa.Column("serving_quantity_g", sa.Float(), nullable=True),
        sa.Column("nutriscore", sa.String(1), nullable=True),
        sa.Column("image_url", sa.String(500), nullable=True),
        sa.Column("categories", sa.String(500), nullable=True),
        sa.Column("allergens", sa.String(300), nullable=True),
        sa.Column("energy_kcal_100g", sa.Float(), nullable=True),
        sa.Column("proteins_100g", sa.Float(), nullable=True),
        sa.Column("carbohydrates_100g", sa.Float(), nullable=True),
        sa.Column("sugars_100g", sa.Float(), nullable=True),
        sa.Column("fat_100g", sa.Float(), nullable=True),
        sa.Column("saturated_fat_100g", sa.Float(), nullable=True),
        sa.Column("fiber_100g", sa.Float(), nullable=True),
        sa.Column("salt_100g", sa.Float(), nullable=True),
        sa.Column("sodium_100g", sa.Float(), nullable=True),
        sa.Column("source", sa.String(20), nullable=False, server_default="openfoodfacts"),
        sa.Column("off_raw_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="macro_tracker",
    )
    op.create_index(
        "ix_products_barcode", "products", ["barcode"],
        unique=True, schema="macro_tracker",
        postgresql_where=sa.text("barcode IS NOT NULL"),
    )
    op.create_index("ix_products_name", "products", ["product_name"], schema="macro_tracker")

    # 3. Tabla diary_entries
    op.create_table(
        "diary_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("entry_date", sa.Date(), nullable=False),
        sa.Column("meal_type", mealtype_enum, nullable=False),
        sa.Column("amount_g", sa.Float(), nullable=False),
        sa.Column("energy_kcal", sa.Float(), nullable=True),
        sa.Column("proteins_g", sa.Float(), nullable=True),
        sa.Column("carbohydrates_g", sa.Float(), nullable=True),
        sa.Column("sugars_g", sa.Float(), nullable=True),
        sa.Column("fat_g", sa.Float(), nullable=True),
        sa.Column("saturated_fat_g", sa.Float(), nullable=True),
        sa.Column("fiber_g", sa.Float(), nullable=True),
        sa.Column("salt_g", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["product_id"], ["macro_tracker.products.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["core.users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema="macro_tracker",
    )
    op.create_index("ix_diary_user_date", "diary_entries", ["user_id", "entry_date"], schema="macro_tracker")
    op.create_index("ix_diary_user_meal", "diary_entries", ["user_id", "entry_date", "meal_type"], schema="macro_tracker")

    # 4. Tabla user_goals
    op.create_table(
        "user_goals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("energy_kcal", sa.Float(), nullable=False, server_default="2000.0"),
        sa.Column("proteins_g", sa.Float(), nullable=False, server_default="150.0"),
        sa.Column("carbohydrates_g", sa.Float(), nullable=False, server_default="250.0"),
        sa.Column("fat_g", sa.Float(), nullable=False, server_default="65.0"),
        sa.Column("fiber_g", sa.Float(), nullable=True, server_default="25.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["core.users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", name="uq_user_goals_user_id"),
        sa.PrimaryKeyConstraint("id"),
        schema="macro_tracker",
    )


def downgrade() -> None:
    op.drop_table("user_goals", schema="macro_tracker")
    op.drop_index("ix_diary_user_meal", table_name="diary_entries", schema="macro_tracker")
    op.drop_index("ix_diary_user_date", table_name="diary_entries", schema="macro_tracker")
    op.drop_table("diary_entries", schema="macro_tracker")
    op.drop_index("ix_products_name", table_name="products", schema="macro_tracker")
    op.drop_index("ix_products_barcode", table_name="products", schema="macro_tracker")
    op.drop_table("products", schema="macro_tracker")
    sa.Enum(name="mealtype", schema="macro_tracker").drop(op.get_bind(), checkfirst=True)