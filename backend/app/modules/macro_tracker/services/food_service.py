from sqlalchemy.orm import Session
from ..product import Product
from ..openfoodfacts_client import OpenFoodFactsClient

client = OpenFoodFactsClient()


class FoodService:

    async def get_or_fetch_by_barcode(self, db: Session, barcode: str) -> Product:
        # Normalizar: solo dígitos, sin espacios
        barcode = barcode.strip()

        # 1. Buscar en caché local primero — 0 llamadas a OFF
        product = db.query(Product).filter(Product.barcode == barcode).first()
        if product:
            return product

        # 2. No está en BD → llamar a OFF (1 sola llamada)
        raw = await client.get_product(barcode)
        parsed = client.parse_product(raw)

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

        # Si hay suficientes resultados locales, no llamamos a OFF
        if len(local_results) >= 5:
            return local_results

        # 2. Completar con resultados de OFF (no se cachean)
        try:
            remote_results = await client.search_by_name(query_stripped, page_size=10)
        except Exception:
            # Si OFF falla en búsqueda por nombre, devolvemos lo que tenemos local
            return local_results

        # Deduplicar: excluir barcodes que ya están en local
        local_barcodes = {p.barcode for p in local_results if p.barcode}
        extra = []
        for raw in remote_results:
            parsed = client.parse_product(raw)
            if parsed.get("barcode") not in local_barcodes:
                # Crear objeto Product sin persistir (solo para la respuesta)
                extra.append(Product(**parsed))

        return (local_results + extra)[:limit]

    def get_product_by_id(self, db: Session, product_id: int) -> Product:
        from ..exceptions import ProductNotFoundError
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ProductNotFoundError(product_id)
        return product