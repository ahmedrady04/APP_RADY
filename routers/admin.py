from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db import get_db
from dependencies.auth import require_admin
from models import User
from schemas.user import CreateUserRequest, UserActiveUpdate, UserOut
from services.auth_service import (
    AuthServiceError,
    create_user as auth_create_user,
    reset_user_device as auth_reset_user_device,
    set_user_active as auth_set_user_active,
)


router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/users", response_model=UserOut)
def create_user(
    payload: CreateUserRequest,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        return auth_create_user(
            db=db,
            username=payload.username,
            password=payload.password,
            is_admin=payload.is_admin,
        )
    except AuthServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.get("/users", response_model=list[UserOut])
def list_users(
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return db.query(User).order_by(User.id.asc()).all()


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user_active(
    user_id: int,
    payload: UserActiveUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        return auth_set_user_active(db=db, admin=admin, user_id=user_id, is_active=payload.is_active)
    except AuthServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("/users/{user_id}/reset-device", response_model=UserOut)
def reset_device(
    user_id: int,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        return auth_reset_user_device(db=db, user_id=user_id)
    except AuthServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
