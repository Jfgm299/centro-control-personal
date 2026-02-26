from sqlalchemy.orm import Session
from typing import List

from ..models.body_measurement import BodyMeasurement
from ..schemas import BodyMeasurementCreate
from ..exceptions import BodyMeasureNotFound

class BodyMeasureService:
    def get_all(self,db: Session) -> List[BodyMeasurement]:
        query = db.query(BodyMeasurement) 
        return query.all()

    def get_measure(self, measure_id: int, db: Session) -> BodyMeasurement:
        db_measure = db.query(BodyMeasurement).filter(BodyMeasurement.id == measure_id).first()
        
        if not db_measure: raise BodyMeasureNotFound
        return db_measure

    def create_measure(self, db: Session, data: BodyMeasurementCreate) -> BodyMeasurement:
        db_measure = BodyMeasurement(**data.model_dump())
        db.add(db_measure)
        db.commit()
        db.refresh(db_measure)
        return db_measure

    def delete_measure(self, measure_id: int, db: Session) -> bool:
        db_measure = db.query(BodyMeasurement).filter(BodyMeasurement.id == measure_id).first()

        if not db_measure: raise BodyMeasureNotFound

        db.delete(db_measure)
        db.commit()
        return True

body_measurement_service = BodyMeasureService()