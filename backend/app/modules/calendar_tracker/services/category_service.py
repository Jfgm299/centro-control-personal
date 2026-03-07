import random
from sqlalchemy.orm import Session
from ..models.category import Category
from ..schemas.calendar_schema import CategoryCreate, CategoryUpdate
from ..exceptions import CategoryNotFoundError, CategoryNameAlreadyExistsError

PALETTE = [
    "#5B50E8", "#E8506A", "#18A882", "#E89020", "#7C3AED",
    "#0891B2", "#F06292", "#AED581", "#FFD54F", "#4DB6AC",
    "#FF8A65", "#A1C4FD", "#FD9853", "#B5EAD7", "#C7CEEA",
    "#FFDAC1", "#E2F0CB", "#FF9AA2", "#B5B9FF", "#85E3FF",
]


def _get_random_color(db: Session, user_id: int) -> str:
    """Devuelve un color de la paleta no usado aún por el usuario."""
    used = {c.color for c in db.query(Category).filter(Category.user_id == user_id).all()}
    available = [c for c in PALETTE if c not in used]
    return random.choice(available) if available else random.choice(PALETTE)


class CategoryService:

    def get_all(self, db: Session, user_id: int) -> list[Category]:
        return (
            db.query(Category)
            .filter(Category.user_id == user_id)
            .order_by(Category.name)
            .all()
        )

    def get_by_id(self, db: Session, user_id: int, category_id: int) -> Category:
        category = (
            db.query(Category)
            .filter(Category.id == category_id, Category.user_id == user_id)
            .first()
        )
        if not category:
            raise CategoryNotFoundError(category_id)
        return category

    def create(self, db: Session, user_id: int, data: CategoryCreate) -> Category:
        # Nombre único por usuario
        existing = (
            db.query(Category)
            .filter(Category.user_id == user_id, Category.name == data.name)
            .first()
        )
        if existing:
            raise CategoryNameAlreadyExistsError(data.name)

        color = data.color or _get_random_color(db, user_id)
        category = Category(
            user_id=user_id,
            name=data.name,
            color=color,
            icon=data.icon,
            default_enable_dnd=data.default_enable_dnd,
            default_reminder_minutes=data.default_reminder_minutes,
        )
        db.add(category)
        db.commit()
        db.refresh(category)
        return category

    def update(self, db: Session, user_id: int, category_id: int, data: CategoryUpdate) -> Category:
        category = self.get_by_id(db, user_id, category_id)

        # Si cambia el nombre, verificar unicidad
        if data.name and data.name != category.name:
            existing = (
                db.query(Category)
                .filter(Category.user_id == user_id, Category.name == data.name)
                .first()
            )
            if existing:
                raise CategoryNameAlreadyExistsError(data.name)

        update_data = data.model_dump(exclude_none=True)
        for key, value in update_data.items():
            setattr(category, key, value)

        db.commit()
        db.refresh(category)
        return category

    def delete(self, db: Session, user_id: int, category_id: int) -> None:
        category = self.get_by_id(db, user_id, category_id)
        db.delete(category)
        db.commit()