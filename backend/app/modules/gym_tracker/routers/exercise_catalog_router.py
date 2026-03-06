from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.auth.user import User
from ..services.exercise_catalog_service import (
    exercise_catalog_service,
    CatalogExerciseCreate,
    CatalogExerciseResponse,
)

router = APIRouter(prefix='/exercise-catalog', tags=['Exercise Catalog'])


@router.get('/', response_model=List[CatalogExerciseResponse])
def list_catalog(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return exercise_catalog_service.get_all(db, user_id=user.id)


@router.post('/', response_model=CatalogExerciseResponse, status_code=201)
def create_custom(
    data: CatalogExerciseCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return exercise_catalog_service.create_custom(db, data, user_id=user.id)


@router.delete('/{catalog_id}', status_code=204)
def delete_custom(
    catalog_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not exercise_catalog_service.delete_custom(db, catalog_id, user_id=user.id):
        raise HTTPException(status_code=404, detail='Custom exercise not found')