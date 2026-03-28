from sqlalchemy.orm import Session
from ..product import Product
from ..openfoodfacts_client import OpenFoodFactsClient
from ..macro_schema import ProductCreate, ProductUpdate

NUTRIENT_FIELDS = [
    "energy_kcal_100g", "proteins_100g", "carbohydrates_100g",
    "sugars_100g", "fat_100g", "saturated_fat_100g",
    "fiber_100g", "salt_100g",
]


class FoodService:

    def __init__(self):
        self.client = OpenFoodFactsClient()

    async def get_or_fetch_by_barcode(self, db: Session, barcode: str) -> Product:
        barcode = barcode.strip()

        # 1. Buscar en caché local primero
        product = db.query(Product).filter(Product.barcode == barcode).first()
        if product:
            return product

        # 2. No está en BD → llamar a OFF y persistir
        raw    = await self.client.get_product(barcode)
        parsed = self.client.parse_product(raw)

        product = Product(**parsed)
        db.add(product)
        db.commit()
        db.refresh(product)
        return product

    async def search_products(self, db: Session, query: str, limit: int = 20) -> list[Product]:
        query_stripped = query.strip()

        # 1. Buscar en BD local primero
        local_results = (
            db.query(Product)
            .filter(Product.product_name.ilike(f"%{query_stripped}%"))
            .limit(limit)
            .all()
        )

        if len(local_results) >= 5:
            return local_results

        # 2. Completar con resultados de OFF — PERSISTIR para que tengan id
        try:
            remote_results = await self.client.search_by_name(query_stripped, page_size=10)
        except Exception:
            return local_results

        local_barcodes = {p.barcode for p in local_results if p.barcode}

        for raw in remote_results:
            parsed = self.client.parse_product(raw)
            barcode = parsed.get("barcode")

            # Evitar duplicados con local
            if barcode and barcode in local_barcodes:
                continue

            # Upsert: si ya existe en BD por barcode, no duplicar
            if barcode:
                existing = db.query(Product).filter(Product.barcode == barcode).first()
                if existing:
                    local_results.append(existing)
                    local_barcodes.add(barcode)
                    continue

            # Persistir el producto de OFF para que tenga id
            product = Product(**parsed)
            db.add(product)
            try:
                db.commit()
                db.refresh(product)
                local_results.append(product)
                if barcode:
                    local_barcodes.add(barcode)
            except Exception:
                db.rollback()

        return local_results[:limit]

    def get_product_by_id(self, db: Session, product_id: int) -> Product:
        from ..exceptions import ProductNotFoundError
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ProductNotFoundError(product_id)
        return product

    def create_product(self, db: Session, data: ProductCreate) -> Product:
        """Crea un producto manual con source='manual'."""
        product = Product(
            product_name       = data.product_name,
            brand              = data.brand,
            barcode            = data.barcode or None,
            serving_quantity_g = data.serving_quantity_g,
            energy_kcal_100g   = data.energy_kcal_100g,
            proteins_100g      = data.proteins_100g,
            carbohydrates_100g = data.carbohydrates_100g,
            sugars_100g        = data.sugars_100g,
            fat_100g           = data.fat_100g,
            saturated_fat_100g = data.saturated_fat_100g,
            fiber_100g         = data.fiber_100g,
            salt_100g          = data.salt_100g,
            source             = "manual",
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        return product

    def update_product(self, db: Session, product_id: int, data: ProductUpdate) -> Product:
        """Actualiza campos nutricionales de un producto existente."""
        from ..exceptions import ProductNotFoundError
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ProductNotFoundError(product_id)

        for field, value in data.model_dump(exclude_none=True).items():
            setattr(product, field, value)

        db.commit()
        db.refresh(product)
        return product