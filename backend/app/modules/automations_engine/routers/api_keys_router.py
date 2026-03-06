from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from ..schemas.api_key_schema import ApiKeyCreate, ApiKeyResponse, ApiKeyCreateResponse
from ..services import api_key_service
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.auth.user import User

router = APIRouter(prefix="/automations/api-keys", tags=["API Keys"])


@router.get("/", response_model=List[ApiKeyResponse])
def get_api_keys(
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    return api_key_service.get_all(db, user_id=user.id)


@router.post("/", response_model=ApiKeyCreateResponse, status_code=status.HTTP_201_CREATED)
def create_api_key(
    data: ApiKeyCreate,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    api_key, raw_token = api_key_service.create(db, data, user_id=user.id)
    return ApiKeyCreateResponse(
        id            = api_key.id,
        name          = api_key.name,
        automation_id = api_key.automation_id,
        key_prefix    = api_key.key_prefix,
        scopes        = api_key.scopes,
        last_used_at  = api_key.last_used_at,
        expires_at    = api_key.expires_at,
        is_active     = api_key.is_active,
        created_at    = api_key.created_at,
        token         = raw_token,
    )


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_api_key(
    key_id: int,
    db:     Session = Depends(get_db),
    user:   User    = Depends(get_current_user),
):
    api_key_service.revoke(key_id, db, user_id=user.id)