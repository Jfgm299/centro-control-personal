from sqlalchemy.orm import Session
from ..models.activity import Activity
from ..schemas.activity_schema import ActivityCreate, ActivityUpdate
from ..exceptions.travel_exceptions import ActivityNotFoundError
from .trip_service import get_trip_by_id


def create_activity(db: Session, user_id: int, trip_id: int, data: ActivityCreate) -> Activity:
    get_trip_by_id(db, user_id, trip_id)  # verifies ownership
    activity = Activity(user_id=user_id, trip_id=trip_id, **data.model_dump())
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


def get_activities(db: Session, user_id: int, trip_id: int) -> list[Activity]:
    get_trip_by_id(db, user_id, trip_id)
    return (
        db.query(Activity)
        .filter(Activity.trip_id == trip_id, Activity.user_id == user_id)
        .order_by(Activity.date.asc().nullslast(), Activity.position.asc())
        .all()
    )


def get_activity_by_id(db: Session, user_id: int, activity_id: int) -> Activity:
    activity = (
        db.query(Activity)
        .filter(Activity.id == activity_id, Activity.user_id == user_id)
        .first()
    )
    if not activity:
        raise ActivityNotFoundError(activity_id)
    return activity


def update_activity(
    db: Session, user_id: int, activity_id: int, data: ActivityUpdate
) -> Activity:
    activity = get_activity_by_id(db, user_id, activity_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(activity, field, value)
    db.commit()
    db.refresh(activity)
    return activity


def delete_activity(db: Session, user_id: int, activity_id: int) -> None:
    activity = get_activity_by_id(db, user_id, activity_id)
    db.delete(activity)
    db.commit()