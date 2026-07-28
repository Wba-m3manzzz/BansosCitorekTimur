from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas.auth import CurrentAdminResponse, LoginRequest, LoginResponse, LogoutRequest, RefreshRequest
from app.services.auth_service import AuthError, AuthService, get_auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])
security = HTTPBearer(auto_error=False)


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, auth_service: AuthService = Depends(get_auth_service)):
    try:
        result = auth_service.login(payload.username, payload.password)
        return LoginResponse(**result)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.post("/refresh", response_model=LoginResponse)
def refresh(payload: RefreshRequest, auth_service: AuthService = Depends(get_auth_service)):
    try:
        return auth_service.refresh(payload.refresh_token)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.post("/logout")
def logout(payload: LogoutRequest, auth_service: AuthService = Depends(get_auth_service)):
    return auth_service.logout(payload.access_token, payload.refresh_token)


@router.get("/me", response_model=CurrentAdminResponse)
def me(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
):
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token tidak ditemukan")
    try:
        admin = auth_service.resolve_admin_from_token(credentials.credentials)
        return CurrentAdminResponse(authenticated=True, admin=admin)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
