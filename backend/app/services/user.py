import uuid
from typing import Any

from fastapi import HTTPException
from sqlmodel import Session

from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models import User
from app.repositories import item as item_repo
from app.repositories import user as user_repo
from app.schemas.user import (
    PrivateUserCreate,
    UpdatePassword,
    UserCreate,
    UserPublic,
    UserRegister,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
)
from app.services import email as email_service


def create_user(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    user_repo.add(session=session, user=db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> User:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data: dict[str, Any] = {}
    if "password" in user_data:
        password = user_data["password"]
        extra_data["hashed_password"] = get_password_hash(password)
    db_user.sqlmodel_update(user_data, update=extra_data)
    user_repo.add(session=session, user=db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def create_user_private(*, session: Session, user_in: PrivateUserCreate) -> User:
    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
    )
    user_repo.add(session=session, user=user)
    session.commit()
    session.refresh(user)
    return user


def list_users(*, session: Session, page: int, size: int) -> UsersPublic:
    count = user_repo.count_users(session=session)
    skip = (page - 1) * size
    users = user_repo.list_users(session=session, skip=skip, limit=size)
    users_public = [UserPublic.model_validate(user) for user in users]
    return UsersPublic(data=users_public, count=count)


def create_user_with_welcome_email(*, session: Session, user_in: UserCreate) -> User:
    existing_user = user_repo.get_user_by_email(session=session, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )

    user = create_user(session=session, user_create=user_in)
    if settings.emails_enabled and user_in.email:
        email_data = email_service.generate_new_account_email(
            email_to=user_in.email, username=user_in.email, password=user_in.password
        )
        email_service.send_email(
            email_to=user_in.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    return user


def register_user(*, session: Session, user_in: UserRegister) -> User:
    existing_user = user_repo.get_user_by_email(session=session, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )
    user_create = UserCreate.model_validate(user_in)
    return create_user(session=session, user_create=user_create)


def update_user_me(
    *, session: Session, current_user: User, user_in: UserUpdateMe
) -> User:
    if user_in.email:
        existing_user = user_repo.get_user_by_email(
            session=session, email=user_in.email
        )
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )
    user_data = user_in.model_dump(exclude_unset=True)
    current_user.sqlmodel_update(user_data)
    user_repo.add(session=session, user=current_user)
    session.commit()
    session.refresh(current_user)
    return current_user


def update_password_me(
    *, session: Session, current_user: User, body: UpdatePassword
) -> None:
    verified, _ = verify_password(body.current_password, current_user.hashed_password)
    if not verified:
        raise HTTPException(status_code=400, detail="Incorrect password")
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=400, detail="New password cannot be the same as the current one"
        )
    current_user.hashed_password = get_password_hash(body.new_password)
    user_repo.add(session=session, user=current_user)
    session.commit()


def delete_user_me(*, session: Session, current_user: User) -> None:
    if current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )
    session.delete(current_user)
    session.commit()


def read_user_by_id(
    *, session: Session, user_id: uuid.UUID, current_user: User
) -> User:
    user = user_repo.get_user_by_id(session=session, user_id=user_id)
    if user == current_user:
        return user
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="The user doesn't have enough privileges",
        )
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def admin_update_user(
    *, session: Session, user_id: uuid.UUID, user_in: UserUpdate
) -> User:
    db_user = user_repo.get_user_by_id(session=session, user_id=user_id)
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )
    if user_in.email:
        existing_user = user_repo.get_user_by_email(
            session=session, email=user_in.email
        )
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )
    return update_user(session=session, db_user=db_user, user_in=user_in)


def admin_delete_user(
    *, session: Session, current_user: User, user_id: uuid.UUID
) -> None:
    user = user_repo.get_user_by_id(session=session, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user == current_user:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )
    item_repo.delete_items_by_owner(session=session, owner_id=user_id)
    session.delete(user)
    session.commit()
