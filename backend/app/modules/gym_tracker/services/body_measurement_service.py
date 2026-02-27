from sqlalchemy.orm import Session
from typing import List
from ..models.body_measurement import BodyMeasurement
from ..schemas import BodyMeasurementCreate
from ..exceptions import BodyMeasureNotFound

class BodyMeasureService:

    def get_all(self, db: Session, user_id: int) -> List[BodyMeasurement]:
        return db.query(BodyMeasurement).filter(
            BodyMeasurement.user_id == user_id
        ).all()

    def get_measure(self, measure_id: int, db: Session, user_id: int) -> BodyMeasurement:
        db_measure = db.query(BodyMeasurement).filter(
            BodyMeasurement.id == measure_id,
            BodyMeasurement.user_id == user_id
        ).first()
        if not db_measure:
            raise BodyMeasureNotFound(measure_id)
        return db_measure

    def create_measure(self, db: Session, data: BodyMeasurementCreate, user_id: int) -> BodyMeasurement:
        db_measure = BodyMeasurement(**data.model_dump(), user_id=user_id)
        db.add(db_measure)
        db.commit()
        db.refresh(db_measure)
        return db_measure

    def delete_measure(self, measure_id: int, db: Session, user_id: int) -> bool:
        db_measure = db.query(BodyMeasurement).filter(
            BodyMeasurement.id == measure_id,
            BodyMeasurement.user_id == user_id
        ).first()
        if not db_measure:
            raise BodyMeasureNotFound(measure_id)
        db.delete(db_measure)
        db.commit()
        return True

body_measurement_service = BodyMeasureService()