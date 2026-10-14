import uuid

from sqlmodel import Session, col, func, select
from sqlmodel import delete as sql_delete

from app.models import Item


def get_item_by_id(*, session: Session, item_id: uuid.UUID) -> Item | None:
    return session.get(Item, item_id)


def list_items(*, session: Session, skip: int, limit: int) -> list[Item]:
    statement = (
        select(Item).order_by(col(Item.created_at).desc()).offset(skip).limit(limit)
    )
    return list(session.exec(statement).all())


def list_items_by_owner(
    *, session: Session, owner_id: uuid.UUID, skip: int, limit: int
) -> list[Item]:
    statement = (
        select(Item)
        .where(Item.owner_id == owner_id)
        .order_by(col(Item.created_at).desc())
        .offset(skip)
        .limit(limit)
    )
    return list(session.exec(statement).all())


def count_items(*, session: Session) -> int:
    return session.exec(select(func.count()).select_from(Item)).one()


def count_items_by_owner(*, session: Session, owner_id: uuid.UUID) -> int:
    statement = select(func.count()).select_from(Item).where(Item.owner_id == owner_id)
    return session.exec(statement).one()


def add(*, session: Session, item: Item) -> Item:
    session.add(item)
    session.flush()
    return item


def delete(*, session: Session, item: Item) -> None:
    session.delete(item)
    session.flush()


def delete_items_by_owner(*, session: Session, owner_id: uuid.UUID) -> None:
    statement = sql_delete(Item).where(col(Item.owner_id) == owner_id)
    session.exec(statement)
