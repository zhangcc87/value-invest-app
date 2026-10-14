from datetime import UTC, datetime, timedelta

import jwt
from fastapi import HTTPException
from jwt.exceptions import InvalidTokenError
from sqlmodel import Session

from app.core import security
from app.core.config import settings
from app.models import User
from app.repositories import user as user_repo
from app.schemas.token import NewPassword, Token
from app.schemas.user import UserUpdate
from app.services import email as email_service
from app.services import user as user_service
from app.services.email import EmailData

# Dummy hash to use for timing attack prevention when user is not found
# This is an Argon2 hash of a random password, used to ensure constant-time comparison
DUMMY_HASH = "$argon2id$v=19$m=65536,t=3,p=4$MjQyZWE1MzBjYjJlZTI0Yw$YTU4NGM5ZTZmYjE2NzZlZjY0ZWY3ZGRkY2U2OWFjNjk"


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    db_user = user_repo.get_user_by_email(session=session, email=email)
    if not db_user:
        # Prevent timing attacks by running password verification even when user doesn't exist
        # This ensures the response time is similar whether or not the email exists
        security.verify_password(password, DUMMY_HASH)
        return None
    verified, updated_password_hash = security.verify_password(
        password, db_user.hashed_password
    )
    if not verified:
        return None
    if updated_password_hash:
        db_user.hashed_password = updated_password_hash
        user_repo.add(session=session, user=db_user)
        session.commit()
        session.refresh(db_user)
    return db_user


def login(*, session: Session, email: str, password: str) -> Token:
    user = authenticate(session=session, email=email, password=password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(
        access_token=security.create_access_token(
            user.id, expires_delta=access_token_expires
        )
    )


def generate_password_reset_token(email: str) -> str:
    delta = timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
    now = datetime.now(UTC)
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email},
        settings.SECRET_KEY,
        algorithm=security.ALGORITHM,
    )
    return encoded_jwt


def verify_password_reset_token(token: str) -> str | None:
    try:
        decoded_token = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        return str(decoded_token["sub"])
    except InvalidTokenError:
        return None


def recover_password(*, session: Session, email: str) -> None:
    user = user_repo.get_user_by_email(session=session, email=email)

    # Always return the same response to prevent email enumeration attacks
    # Only send email if user actually exists
    if user:
        password_reset_token = generate_password_reset_token(email=email)
        email_data = email_service.generate_reset_password_email(
            email_to=user.email, email=email, token=password_reset_token
        )
        email_service.send_email(
            email_to=user.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )


def reset_password(*, session: Session, body: NewPassword) -> None:
    email = verify_password_reset_token(token=body.token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token")
    user = user_repo.get_user_by_email(session=session, email=email)
    if not user:
        # Don't reveal that the user doesn't exist - use same error as invalid token
        raise HTTPException(status_code=400, detail="Invalid token")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    user_in_update = UserUpdate(password=body.new_password)
    user_service.update_user(session=session, db_user=user, user_in=user_in_update)


def recover_password_html_content(*, session: Session, email: str) -> EmailData:
    user = user_repo.get_user_by_email(session=session, email=email)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system.",
        )
    password_reset_token = generate_password_reset_token(email=email)
    return email_service.generate_reset_password_email(
        email_to=user.email, email=email, token=password_reset_token
    )
