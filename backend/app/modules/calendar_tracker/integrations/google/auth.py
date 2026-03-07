"""
OAuth 2.0 para Google Calendar.

Flujo:
    1. authorize_url()     → redirige al usuario a Google
    2. exchange_code()     → intercambia el code por access+refresh token
    3. refresh_token()     → renueva el access_token cuando expira
"""
from datetime import datetime, timezone, timedelta
from typing import Optional
import httpx
from app.modules.calendar_tracker.manifest import get_settings


GOOGLE_AUTH_URL  = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPES           = "https://www.googleapis.com/auth/calendar"


def authorize_url(state: Optional[str] = None) -> str:
    """Devuelve la URL a la que redirigir al usuario para autorizar Google Calendar."""
    cfg = get_settings()
    params = {
        "client_id":     cfg["GOOGLE_CLIENT_ID"],
        "redirect_uri":  cfg["GOOGLE_REDIRECT_URI"],
        "response_type": "code",
        "scope":         SCOPES,
        "access_type":   "offline",
        "prompt":        "consent",
    }
    if state:
        params["state"] = state

    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{GOOGLE_AUTH_URL}?{query}"


def exchange_code(code: str) -> dict:
    """
    Intercambia el authorization code por tokens.
    Devuelve: {access_token, refresh_token, expires_at}
    """
    cfg = get_settings()
    response = httpx.post(GOOGLE_TOKEN_URL, data={
        "code":          code,
        "client_id":     cfg["GOOGLE_CLIENT_ID"],
        "client_secret": cfg["GOOGLE_CLIENT_SECRET"],
        "redirect_uri":  cfg["GOOGLE_REDIRECT_URI"],
        "grant_type":    "authorization_code",
    })
    response.raise_for_status()
    data = response.json()

    expires_at = datetime.now(timezone.utc) + timedelta(seconds=data["expires_in"])
    return {
        "access_token":  data["access_token"],
        "refresh_token": data.get("refresh_token"),
        "expires_at":    expires_at,
    }


def refresh_access_token(refresh_token: str) -> dict:
    """
    Renueva el access_token usando el refresh_token.
    Devuelve: {access_token, expires_at}
    """
    cfg = get_settings()
    response = httpx.post(GOOGLE_TOKEN_URL, data={
        "refresh_token": refresh_token,
        "client_id":     cfg["GOOGLE_CLIENT_ID"],
        "client_secret": cfg["GOOGLE_CLIENT_SECRET"],
        "grant_type":    "refresh_token",
    })
    response.raise_for_status()
    data = response.json()

    expires_at = datetime.now(timezone.utc) + timedelta(seconds=data["expires_in"])
    return {
        "access_token": data["access_token"],
        "expires_at":   expires_at,
    }