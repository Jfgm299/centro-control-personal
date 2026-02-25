from fastapi import APIRouter, Depends
from ...schemas import BodyMeasurementCreate, BodyMeasurementResponse
from typing import List
from sqlalchemy.orm import Session
from ...services import body_measurement_service

from ...database import get_db

router = APIRouter(prefix='/body-measures', tags=['body-measures'])

@router.get('/', response_model=List[BodyMeasurementResponse])
def get_measures(
    db: Session = Depends(get_db)
):
    return body_measurement_service.get_all(db)

@router.get('/{measurement_id}', response_model=BodyMeasurementResponse)
def get_measure(
    measurement_id: int,
    db: Session = Depends(get_db)
):
    return body_measurement_service.get_measure(measurement_id,db)

@router.post('/', response_model=BodyMeasurementResponse, status_code=201)
def create_measure(
    data: BodyMeasurementCreate,
    db: Session = Depends(get_db)
):
    return body_measurement_service.create_measure(data,db)

@router.delete('/{measurement_id}', response_description='Successfully deleted', status_code=204)
def delete_measure(
    measurement_id: int,
    db: Session = Depends(get_db)
):
    sucess = body_measurement_service.delete_measure(measurement_id, db)
    return {"message": "Body Measurement Deleted", "id": measurement_id}