from fastapi import APIRouter, Depends
from ..schemas import BodyMeasurementCreate, BodyMeasurementResponse
from typing import List
from sqlalchemy.orm import Session
from ..services import body_measurement_service
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.auth.user import User

router = APIRouter(prefix='/body-measures', tags=['Body Measurements'])

@router.get('/', response_model=List[BodyMeasurementResponse])
def get_measures(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return body_measurement_service.get_all(db, user_id=user.id)

@router.get('/{measurement_id}', response_model=BodyMeasurementResponse)
def get_measure(
    measurement_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return body_measurement_service.get_measure(measurement_id, db, user_id=user.id)

@router.post('/', response_model=BodyMeasurementResponse, status_code=201)
def create_measure(
    data: BodyMeasurementCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return body_measurement_service.create_measure(db, data, user_id=user.id)

@router.delete('/{measurement_id}', response_description='Successfully deleted', status_code=204)
def delete_measure(
    measurement_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    body_measurement_service.delete_measure(measurement_id, db, user_id=user.id)
    return {"message": "Body Measurement Deleted", "id": measurement_id}