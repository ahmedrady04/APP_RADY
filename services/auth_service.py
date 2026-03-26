from __future__ import annotations

from sqlalchemy.orm import Session

from models import User
from services.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


class AuthServiceError(Exception):
    def __init__(self, *, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def login(
    *,
    db: Session,
    username: str,
    password: str,
    device_id: str,
) -> tuple[str, str, bool]:
    """
    Returns (access_token, refresh_token, is_admin).

    Non-admin users are bound to exactly one device on first successful login.
    """
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        raise AuthServiceError(status_code=401, detail="Invalid username or password")

    if not user.is_active:
        raise AuthServiceError(status_code=403, detail="Account is disabled")

    if not user.is_admin:
        if user.device_id is None:
            user.device_id = device_id
            db.add(user)
            db.commit()
        elif user.device_id != device_id:
            raise AuthServiceError(status_code=403, detail="This account is linked to another device")

    subject = str(user.id)
    return (
        create_access_token(subject),
        create_refresh_token(subject),
        user.is_admin,
    )


def refresh(
    *,
    db: Session,
    refresh_token: str,
    device_id: str,
) -> tuple[str, str, bool]:
    """Returns (access_token, refresh_token, is_admin)."""
    try:
        token_payload = decode_token(refresh_token)
    except Exception as e:
        raise AuthServiceError(status_code=401, detail="Invalid refresh token") from e

    if token_payload.get("type") != "refresh":
        raise AuthServiceError(status_code=401, detail="Invalid token type")

    subject = token_payload.get("sub")
    if not subject or not str(subject).isdigit():
        raise AuthServiceError(status_code=401, detail="Invalid token subject")

    user = db.get(User, int(subject))
    if user is None:
        raise AuthServiceError(status_code=401, detail="User not found")

    if not user.is_active:
        raise AuthServiceError(status_code=403, detail="Account is disabled")

    if not user.is_admin and user.device_id != device_id:
        raise AuthServiceError(status_code=403, detail="Token refresh not allowed from this device")

    user_subject = str(user.id)
    return (
        create_access_token(user_subject),
        create_refresh_token(user_subject),
        user.is_admin,
    )


def create_user(
    *,
    db: Session,
    username: str,
    password: str,
    is_admin: bool = False,
) -> User:
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise AuthServiceError(status_code=409, detail="Username already exists")

    user = User(
        username=username,
        password_hash=hash_password(password),
        is_admin=is_admin,
        is_active=True,
        device_id=None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def set_user_active(
    *,
    db: Session,
    admin: User,
    user_id: int,
    is_active: bool,
) -> User:
    if admin.id == user_id and not is_active:
        raise AuthServiceError(status_code=400, detail="You cannot deactivate your own account")

    target = db.get(User, user_id)
    if target is None:
        raise AuthServiceError(status_code=404, detail="User not found")

    target.is_active = is_active
    db.add(target)
    db.commit()
    db.refresh(target)
    return target


def reset_user_device(
    *,
    db: Session,
    user_id: int,
) -> User:
    target = db.get(User, user_id)
    if target is None:
        raise AuthServiceError(status_code=404, detail="User not found")

    target.device_id = None
    db.add(target)
    db.commit()
    db.refresh(target)
    return target

