from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from pydantic import BaseModel

from app.core.config import settings

bearer_scheme = HTTPBearer(auto_error=False)
token_request = google_requests.Request()


class User(BaseModel):
    uid: str
    email: Optional[str] = None
    name: Optional[str] = None


def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        claims = id_token.verify_firebase_token(credentials.credentials, token_request, audience=settings.FIREBASE_PROJECT_ID)
    except ValueError:
        claims = None
    if not claims or claims.get("iss") != f"https://securetoken.google.com/{settings.FIREBASE_PROJECT_ID}":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return User(uid=claims["sub"], email=claims.get("email"), name=claims.get("name"))
