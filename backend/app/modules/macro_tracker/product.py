from sqlalchemy import Column, Integer, Float, String, JSON, DateTime, Index, text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        Index(
            "ix_products_barcode",
            "barcode",
            unique=True,
            postgresql_where=text("barcode IS NOT NULL"),
        ),
        Index("ix_products_name", "product_name"),
        {"schema": "macro_tracker", "extend_existing": True},
    )

    id                 = Column(Integer, primary_key=True)
    barcode            = Column(String(30), nullable=True)
    product_name       = Column(String(200), nullable=False)
    brand              = Column(String(100), nullable=True)
    serving_size_text  = Column(String(50), nullable=True)
    serving_quantity_g = Column(Float, nullable=True)
    nutriscore         = Column(String(10), nullable=True)
    image_url          = Column(String(500), nullable=True)
    categories         = Column(String(500), nullable=True)
    allergens          = Column(String(300), nullable=True)

    # Nutrientes por 100g
    energy_kcal_100g    = Column(Float, nullable=True)
    proteins_100g       = Column(Float, nullable=True)
    carbohydrates_100g  = Column(Float, nullable=True)
    sugars_100g         = Column(Float, nullable=True)
    fat_100g            = Column(Float, nullable=True)
    saturated_fat_100g  = Column(Float, nullable=True)
    fiber_100g          = Column(Float, nullable=True)
    salt_100g           = Column(Float, nullable=True)
    sodium_100g         = Column(Float, nullable=True)

    source        = Column(String(20), nullable=False, default="openfoodfacts")
    off_raw_data  = Column(JSON, nullable=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    updated_at    = Column(DateTime(timezone=True), onupdate=func.now())

    diary_entries = relationship("DiaryEntry", back_populates="product")