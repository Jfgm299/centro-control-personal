import hashlib
import secrets
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from typing import List
from ..models.api_key import ApiKey
from ..schemas import ApiKeyCreate
from ..exceptions import ApiKeyNotFoundError, ApiKeyInvalidError, ApiKeyExpiredError, ApiKeyInsufficientScopeError


class ApiKeyService:

    def get_all(self, db: Session, user_id: int) -> List[ApiKey]:
        return db.query(ApiKey).filter(
            ApiKey.user_id   == user_id,
            ApiKey.is_active == True,
        ).all()

    def create(self, db: Session, data: ApiKeyCreate, user_id: int) -> tuple[ApiKey, str]:
        raw_token  = f"ak_live_{secrets.token_urlsafe(32)}"
        key_hash   = hashlib.sha256(raw_token.encode()).hexdigest()
        key_prefix = raw_token[:8]

        api_key = ApiKey(
            user_id       = user_id,
            automation_id = data.automation_id,
            name          = data.name,
            key_hash      = key_hash,
            key_prefix    = key_prefix,
            scopes        = [s.value for s in data.scopes],
            expires_at    = data.expires_at,
        )
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
        return api_key, raw_token

    def revoke(self, key_id: int, db: Session, user_id: int) -> None:
        api_key = db.query(ApiKey).filter(
            ApiKey.id        == key_id,
            ApiKey.user_id   == user_id,
            ApiKey.is_active == True,  # ← solo activas
        ).first()
        if not api_key:
            raise ApiKeyNotFoundError(key_id)
        api_key.is_active = False
        db.commit()

    def validate(self, raw_token: str, required_scope: str, db: Session) -> ApiKey:
        key_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        api_key  = db.query(ApiKey).filter(
            ApiKey.key_hash  == key_hash,
            ApiKey.is_active == True,
        ).first()

        if not api_key:
            raise ApiKeyInvalidError()

        if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc):
            raise ApiKeyExpiredError()

        if required_scope not in api_key.scopes:
            raise ApiKeyInsufficientScopeError(required_scope)

        api_key.last_used_at = datetime.now(timezone.utc)
        db.commit()
        return api_key


api_key_service = ApiKeyService()