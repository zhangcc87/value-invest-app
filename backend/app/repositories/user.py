import uuid

from sqlmodel import Session, col, func, select

from app.models import User


def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()


def get_user_by_id(*, session: Session, user_id: uuid.UUID) -> User | None:
    return session.get(User, user_id)


def list_users(*, session: Session, skip: int, limit: int) -> list[User]:
    statement = (
        select(User).order_by(col(User.created_at).desc()).offset(skip).limit(limit)
    )
    return list(session.exec(statement).all())


def count_users(*, session: Session) -> int:
    return session.exec(select(func.count()).select_from(User)).one()


def add(*, session: Session, user: User) -> User:
    session.add(user)
    session.flush()
    return user


def delete(*, session: Session, user: User) -> None:
    session.delete(user)
    session.flush()
